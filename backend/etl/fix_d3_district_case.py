#!/usr/bin/env python3
"""
Fix D3: Normalize district names to Title Case.

Each district appears twice: once in UPPERCASE, once in Title Case.
We keep the Title Case version and update all foreign keys.
Also merge villages with same name within the same district.
"""

from app.database import SessionLocal
from app.models.entities import District, Village, WaterSample, State
from sqlalchemy import func, update, text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def to_title_case(name: str) -> str:
    """Convert to Title Case, handling special cases."""
    if name.upper() == "NOT AVAILABLE":
        return "Not available"
    # Handle multi-word districts
    words = name.lower().split()
    # Special handling for common prefixes
    result = []
    for w in words:
        if w in ['and', 'or', 'the', 'of', 'in', 'on', 'at', 'by', 'for', 'to', 'from']:
            result.append(w.lower())
        else:
            result.append(w.capitalize())
    return ' '.join(result)

def main():
    db = SessionLocal()
    
    # Enable foreign key enforcement for SQLite
    db.execute(text("PRAGMA foreign_keys=ON"))
    
    try:
        # Step 1: Find all case-insensitive duplicates
        log.info("Finding case-insensitive duplicate districts...")
        dup_groups = db.query(
            func.lower(District.name).label('lname'),
            District.state_id,
            func.count(District.id).label('cnt')
        ).group_by(
            func.lower(District.name),
            District.state_id
        ).having(func.count(District.id) > 1).all()
        
        log.info(f"Found {len(dup_groups)} district groups with case variations")
        
        total_fixed = 0
        total_merged = 0
        
        # Track districts we've already processed as canonical
        processed_canonical = set()
        
        for group in dup_groups:
            lname = group.lname
            state_id = group.state_id
            cnt = group.cnt
            
            # Get all districts in this group
            districts = db.query(District).filter(
                func.lower(District.name) == lname,
                District.state_id == state_id
            ).order_by(District.name).all()  # Title Case comes before UPPERCASE
            
            # Determine canonical name (Title Case)
            canonical_name = to_title_case(lname)
            
            # Find the canonical district (or create if needed)
            canonical = None
            for d in districts:
                if d.name == canonical_name:
                    canonical = d
                    break
            
            if not canonical:
                # Use the first one and rename it
                canonical = districts[0]
                old_name = canonical.name
                canonical.name = canonical_name
                log.info(f"Renamed district {canonical.id}: '{old_name}' -> '{canonical_name}'")
            
            # Mark canonical as processed so we don't handle it again
            processed_canonical.add(canonical.id)
            
            # Merge all other districts into canonical
            for d in districts:
                if d.id == canonical.id:
                    continue
                
                log.info(f"Merging district {d.id} ('{d.name}') into {canonical.id} ('{canonical.name}')")
                
                # First, handle villages: merge villages with same name
                source_villages = db.query(Village).filter(Village.district_id == d.id).all()
                for sv in source_villages:
                    # Check if a village with same name exists in canonical district
                    target_village = db.query(Village).filter(
                        Village.district_id == canonical.id,
                        Village.name == sv.name
                    ).first()
                    
                    if target_village:
                        # Merge samples from source village to target village
                        samples_updated = db.query(WaterSample).filter(
                            WaterSample.village_id == sv.id
                        ).update(
                            {WaterSample.village_id: target_village.id},
                            synchronize_session=False
                        )
                        log.info(f"  Merged village {sv.id} ('{sv.name}') into {target_village.id}, updated {samples_updated} samples")
                        db.delete(sv)
                    else:
                        # Just reassign village to canonical district
                        sv.district_id = canonical.id
                        log.info(f"  Reassigned village {sv.id} ('{sv.name}') to district {canonical.id}")
                
                # Flush to ensure village reassignments are persisted before deleting district
                db.flush()
                
                # Delete the duplicate district
                db.delete(d)
                total_merged += 1
            
            total_fixed += 1
            # Flush after each group to prevent session issues
            db.flush()
        
        # Step 2: Handle remaining UPPERCASE districts without Title Case counterpart
        log.info("Finding remaining UPPERCASE districts without Title Case counterpart...")
        uppercase_districts = db.query(District).filter(
            District.name == func.upper(District.name),
            District.name != 'Not available'
        ).all()
        
        log.info(f"Found {len(uppercase_districts)} remaining UPPERCASE districts")
        
        for d in uppercase_districts:
            canonical_name = to_title_case(d.name)
            log.info(f"Renaming district {d.id}: '{d.name}' -> '{canonical_name}'")
            d.name = canonical_name
            total_fixed += 1
        
        db.flush()
        
        # Note: "Not available" districts are already handled by the main loop above
        # since they appear as case-insensitive duplicates (e.g., "Not available" vs "NOT AVAILABLE")
        # No additional handling needed here.
        log.info("Skipping redundant 'Not available' handling - already processed in main loop")
        
        db.commit()
        
        # Verify
        total = db.query(func.count(District.id)).scalar()
        distinct = db.query(func.count(func.distinct(District.name))).scalar()
        
        log.info(f"=== SUMMARY ===")
        log.info(f"Groups fixed: {total_fixed}")
        log.info(f"Duplicates merged: {total_merged}")
        log.info(f"Final district count: {total}")
        log.info(f"Distinct names: {distinct}")
        
        # Check for any remaining case-insensitive duplicates
        remaining = db.query(
            func.lower(District.name).label('lname'),
            District.state_id,
            func.count(District.id).label('cnt')
        ).group_by(
            func.lower(District.name),
            District.state_id
        ).having(func.count(District.id) > 1).all()
        
        if remaining:
            log.warning(f"Remaining duplicates: {len(remaining)}")
            for r in remaining:
                log.warning(f"  {r.lname} (state_id={r.state_id}): {r.cnt} rows")
        else:
            log.info("No remaining case-insensitive duplicates!")
        
        # Check for any remaining UPPERCASE districts (excluding "Not available")
        remaining_upper = db.query(District).filter(
            District.name == func.upper(District.name),
            District.name != 'Not available'
        ).count()
        
        if remaining_upper > 0:
            log.warning(f"WARNING: {remaining_upper} UPPERCASE districts still remain!")
        else:
            log.info("All districts normalized to Title Case!")
        
        # Check villages with null district_id
        null_villages = db.query(Village).filter(Village.district_id.is_(None)).count()
        if null_villages > 0:
            log.error(f"ERROR: {null_villages} villages have NULL district_id!")
        else:
            log.info("All villages have valid district_id")
        
    except Exception as e:
        db.rollback()
        log.error(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()