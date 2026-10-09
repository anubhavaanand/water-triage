#!/usr/bin/env python
"""Fix near-duplicate district names (administrative variants)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.database import SessionLocal, engine
from backend.app.models.entities import District, State, Village, WaterSample, HistoricalContamination
from sqlalchemy import func, text

# Canonical district name mapping
# (old_name, state) -> new_canonical_name
CANONICAL_MAP = {
    # Bihar
    ("Bhojpur(aara)", "Bihar"): "Bhojpur",          # Same district, historical uses '(aara)' suffix
    # Uttar Pradesh
    ("Allahabad", "Uttar Pradesh"): "Prayagraj",    # Renamed 2018
    ("Bara Banki", "Uttar Pradesh"): "Barabanki",   # Spacing variant (official: Barabanki)
    ("Ferozabad", "Uttar Pradesh"): "Firozabad",    # Spelling variant (official: Firozabad)
    ("Siddharth Nagar", "Uttar Pradesh"): "Siddharthnagar",  # Spacing variant
    ("Kushi Nagar", "Uttar Pradesh"): "Kushinagar",         # Spacing variant (official: Kushinagar)
}


def merge_district(db, old_name: str, state_name: str, new_name: str):
    """Merge old district into new canonical district."""
    state = db.query(State).filter(State.name == state_name).one()
    
    old_district = db.query(District).filter(
        District.name == old_name,
        District.state_id == state.id
    ).one_or_none()
    
    new_district = db.query(District).filter(
        District.name == new_name,
        District.state_id == state.id
    ).one_or_none()
    
    if not old_district:
        print(f"  SKIP: Old district '{old_name}' not found")
        return 0
    
    if not new_district:
        # Rename instead of merge
        print(f"  RENAME: '{old_name}' -> '{new_name}' (no canonical target exists)")
        old_district.name = new_name
        db.commit()
        return 1
    
    if old_district.id == new_district.id:
        print(f"  SKIP: Already same district")
        return 0
    
    print(f"  MERGE: '{old_name}' (id={old_district.id}) -> '{new_name}' (id={new_district.id})")
    
    # Use raw SQL to reassign villages (avoids ORM FK issues)
    result = db.execute(
        text("UPDATE villages SET district_id = :new_id WHERE district_id = :old_id"),
        {"new_id": new_district.id, "old_id": old_district.id}
    )
    print(f"    Reassigned {result.rowcount} villages")
    
    # Also update historical_contamination village references (via village_id)
    # No direct update needed - villages table already updated
    
    # Delete old district
    db.delete(old_district)
    db.commit()
    print(f"    Deleted old district row")
    return 1


def main():
    db = SessionLocal()
    try:
        print("Fixing near-duplicate districts...")
        print("=" * 60)
        
        total_merged = 0
        for (old_name, state_name), new_name in CANONICAL_MAP.items():
            print(f"\nProcessing: {old_name} ({state_name}) -> {new_name}")
            total_merged += merge_district(db, old_name, state_name, new_name)
        
        print(f"\n{'=' * 60}")
        print(f"Total merges/renames: {total_merged}")
        
        # Verify final state
        print("\nFinal district count:")
        total = db.query(func.count(District.id)).scalar()
        bihar = db.query(func.count(District.id)).join(State).filter(State.name == "Bihar").scalar()
        up = db.query(func.count(District.id)).join(State).filter(State.name == "Uttar Pradesh").scalar()
        print(f"  Total: {total}")
        print(f"  Bihar: {bihar}")
        print(f"  Uttar Pradesh: {up}")
        
        # Check for remaining duplicates
        print("\nChecking for remaining case-insensitive duplicates...")
        from collections import Counter
        names = db.query(State.name, District.name).join(State).all()
        counter = Counter(f"{s}|{n.lower()}" for s, n in names)
        dupes = [(k, v) for k, v in counter.items() if v > 1]
        if dupes:
            for k, v in dupes:
                s, n = k.split("|")
                print(f"  DUPLICATE: {n} ({s}) x{v}")
        else:
            print("  No case-insensitive duplicates found!")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()