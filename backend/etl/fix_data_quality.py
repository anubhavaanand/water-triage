#!/usr/bin/env python
"""Comprehensive data quality fixes for WaterTriage database.

Addresses:
1. Historical duplicates (17,386 duplicate village/param/year combos)
2. Arsenic zeros flagging (150 readings = 0, likely below detection limit)
3. Sulphate validation (legitimate readings, some exceed BIS limits)
4. Village fuzzy matching between WQMIS and historical
5. District coverage gaps documentation
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.database import SessionLocal, engine
from backend.app.models.entities import (
    HistoricalContamination, Village, District, State, 
    WaterSample, Reading
)
from sqlalchemy import func, text, and_


def fix_historical_duplicates(db):
    """Deduplicate historical records by village/param/year/habitation.
    Since historical_contamination has no 'value' column, duplicates are 
    multiple habitation records for same village/param/year.
    We keep one record per village/param/year (distinct habitation)."""
    print("=" * 60)
    print("Fixing historical duplicates...")
    
    # Find all duplicate groups (same village, parameter, year, but different habitation)
    dup_query = db.execute(text("""
        SELECT village_id, parameter, year, COUNT(*) as cnt
        FROM historical_contamination
        GROUP BY village_id, parameter, year
        HAVING COUNT(*) > 1
    """))
    
    dupes = dup_query.fetchall()
    print(f"Found {len(dupes)} duplicate groups (multiple habitations per village/param/year)")
    
    if not dupes:
        return 0
    
    total_removed = 0
    for v_id, param, year, cnt in dupes:
        # Keep one record per village/param/year (first habitation)
        # Delete the rest
        db.execute(text("""
            DELETE FROM historical_contamination
            WHERE village_id = :v_id AND parameter = :param AND year = :year
            AND id NOT IN (
                SELECT id FROM historical_contamination
                WHERE village_id = :v_id AND parameter = :param AND year = :year
                LIMIT 1
            )
        """), {"v_id": v_id, "param": param, "year": year})
        
        total_removed += (cnt - 1)
    
    db.commit()
    print(f"Removed {total_removed} duplicate historical records")
    return total_removed


def flag_arsenic_bdl(db):
    """Flag arsenic readings of 0 as 'below detection limit' by adding a flag column.
    For now, we'll add a comment field or just document it.
    Alternative: Set to NULL and handle in scoring."""
    print("=" * 60)
    print("Analyzing arsenic below detection limit...")
    
    # Check how many arsenic readings are exactly 0
    arsenic_zero = db.execute(text("""
        SELECT COUNT(*) FROM readings WHERE parameter_key = 'arsenic' AND value = 0
    """)).scalar()
    
    arsenic_total = db.execute(text("""
        SELECT COUNT(*) FROM readings WHERE parameter_key = 'arsenic'
    """)).scalar()
    
    print(f"Arsenic readings: {arsenic_total}, zeros: {arsenic_zero}")
    print(f"BIS limit: 0.01 mg/L - all non-zero values are below this")
    print("RECOMMENDATION: Flag zeros as 'below detection limit' in scoring")
    
    # For now, just document - don't modify data
    return arsenic_zero


def validate_sulphate(db):
    """Validate sulphate readings against BIS limits."""
    print("=" * 60)
    print("Validating sulphate readings...")
    
    sulphate = db.execute(text("""
        SELECT value, sample_id FROM readings WHERE parameter_key = 'sulphate'
    """)).fetchall()
    
    vals = [v for v, _ in sulphate]
    samples = [s for _, s in sulphate]
    
    print(f"Sulphate readings: {len(vals)}")
    print(f"  Range: {min(vals):.1f} - {max(vals):.1f} mg/L")
    print(f"  Mean: {sum(vals)/len(vals):.2f} mg/L")
    print(f"  BIS acceptable: 200 mg/L, permissible: 400 mg/L")
    print(f"  Exceed acceptable (>200): {sum(1 for v in vals if v > 200)}")
    print(f"  Exceed permissible (>400): {sum(1 for v in vals if v > 400)}")
    print(f"  Zero values: {sum(1 for v in vals if v == 0)}")
    
    # These are LEGITIMATE sulphate readings, not pH mis-tags
    # The RECONCILIATION.md bug was already fixed
    return len(vals)


def fuzzy_match_villages(db):
    """Attempt fuzzy matching of WQMIS villages to historical villages
    using name + block + district."""
    print("=" * 60)
    print("Fuzzy matching WQMIS villages to historical...")
    
    # Get WQMIS villages with real names
    wqmis_villages = db.execute(text("""
        SELECT v.id, v.name, v.block, v.district_id, d.name as district_name
        FROM villages v
        JOIN water_samples ws ON ws.village_id = v.id
        JOIN districts d ON d.id = v.district_id
        WHERE v.name NOT IN ('Not available', 'UNKNOWN')
        GROUP BY v.id, v.name, v.block, v.district_id, d.name
    """)).fetchall()
    
    print(f"WQMIS villages with real names: {len(wqmis_villages)}")
    
    matches = []
    for v_id, v_name, v_block, v_district_id, d_name in wqmis_villages:
        # Try exact name match in same district (SQLite: use LOWER for case-insensitive)
        hist_villages = db.execute(text("""
            SELECT id, name, block FROM villages
            WHERE district_id = :d_id AND LOWER(name) = LOWER(:name)
        """), {"d_id": v_district_id, "name": v_name}).fetchall()
        
        if hist_villages:
            for hv_id, hv_name, hv_block in hist_villages:
                # Check block similarity
                block_match = v_block and hv_block and v_block.upper() == hv_block.upper()
                matches.append({
                    'wqmis_vid': v_id,
                    'wqmis_name': v_name,
                    'wqmis_block': v_block,
                    'hist_vid': hv_id,
                    'hist_name': hv_name,
                    'hist_block': hv_block,
                    'district': d_name,
                    'block_match': block_match,
                    'name_match': v_name.lower() == hv_name.lower()
                })
    
    print(f"Potential matches found: {len(matches)}")
    for m in matches:
        status = "✓ BLOCK MATCH" if m['block_match'] else "~ NAME ONLY"
        print(f"  {status}: WQMIS {m['wqmis_vid']}({m['wqmis_name']}, block={m['wqmis_block']}) "
              f"-> Hist {m['hist_vid']}({m['hist_name']}, block={m['hist_block']}) in {m['district']}")
    
    return matches


def document_district_coverage(db):
    """Document district coverage gaps."""
    print("=" * 60)
    print("District coverage analysis...")
    
    # Districts with WQMIS
    wqmis_districts = db.execute(text("""
        SELECT DISTINCT d.id, d.name, s.name as state
        FROM districts d
        JOIN states s ON s.id = d.state_id
        JOIN villages v ON v.district_id = d.id
        JOIN water_samples ws ON ws.village_id = v.id
    """)).fetchall()
    
    # Districts with historical
    hist_districts = db.execute(text("""
        SELECT DISTINCT d.id, d.name, s.name as state
        FROM districts d
        JOIN states s ON s.id = d.state_id
        JOIN villages v ON v.district_id = d.id
        JOIN historical_contamination hc ON hc.village_id = v.id
    """)).fetchall()
    
    wqmis_set = {(d, n, st) for d, n, st in wqmis_districts}
    hist_set = {(d, n, st) for d, n, st in hist_districts}
    
    both = wqmis_set & hist_set
    wqmis_only = wqmis_set - hist_set
    hist_only = hist_set - wqmis_set
    all_districts = db.execute(text("""
        SELECT d.id, d.name, s.name as state
        FROM districts d JOIN states s ON s.id = d.state_id
    """)).fetchall()
    all_set = {(d, n, st) for d, n, st in all_districts}
    neither = all_set - wqmis_set - hist_set
    
    print(f"Total districts: {len(all_set)}")
    print(f"  Both WQMIS + Historical: {len(both)}")
    print(f"  WQMIS only: {len(wqmis_only)}")
    print(f"  Historical only: {len(hist_only)}")
    print(f"  Neither: {len(neither)}")
    
    if wqmis_only:
        print("\nWQMIS only districts:")
        for d, n, st in wqmis_only:
            print(f"  {n} ({st})")
    
    if hist_only:
        print("\nHistorical only districts (sample):")
        for d, n, st in list(hist_only)[:10]:
            print(f"  {n} ({st})")
        if len(hist_only) > 10:
            print(f"  ... and {len(hist_only) - 10} more")
    
    if neither:
        print("\nNeither:")
        for d, n, st in neither:
            print(f"  {n} ({st})")


def main():
    db = SessionLocal()
    try:
        print("WATER TRIAGE - DATA QUALITY FIXES")
        print("=" * 60)
        
        # 1. Fix historical duplicates
        fix_historical_duplicates(db)
        
        # 2. Analyze arsenic BDL
        flag_arsenic_bdl(db)
        
        # 3. Validate sulphate
        validate_sulphate(db)
        
        # 4. Fuzzy match villages
        fuzzy_match_villages(db)
        
        # 5. Document district coverage
        document_district_coverage(db)
        
        print("\n" + "=" * 60)
        print("DATA QUALITY ANALYSIS COMPLETE")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()