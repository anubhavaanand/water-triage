#!/usr/bin/env python3
"""
Normalize source_type field in water_samples table to controlled vocabulary.
Controlled vocabulary: ['handpump', 'tube_well', 'piped_supply', 'well', 'spring', 'surface_water', 'other', 'unknown']
"""

import sqlite3
import re
from collections import defaultdict

DB_PATH = "/home/anubhavanand/Documents/Projects/water-triage/data/watertriage.db"

# Controlled vocabulary
CONTROLLED_VOCAB = ['handpump', 'tube_well', 'piped_supply', 'well', 'spring', 'surface_water', 'other', 'unknown']

def get_all_source_types(conn):
    """Get all distinct source_type values with their counts."""
    cursor = conn.cursor()
    cursor.execute("SELECT source_type, COUNT(*) as cnt FROM water_samples GROUP BY source_type ORDER BY cnt DESC")
    return cursor.fetchall()

def normalize_source_type(source_type):
    """
    Map a raw source_type value to controlled vocabulary.
    Returns the normalized value.
    """
    if not source_type or source_type.strip() == '':
        return 'unknown'
    
    s = source_type.strip().lower()
    
    # Direct matches for controlled vocabulary
    if s in CONTROLLED_VOCAB:
        return s
    
    # Piped supply patterns
    piped_patterns = [
        r'individual house tap water',
        r'public tap water',
        r'piped',
        r'tap water',
    ]
    for pattern in piped_patterns:
        if re.search(pattern, s):
            return 'piped_supply'
    
    # Tube well / bore well patterns
    tube_well_patterns = [
        r'tube well',
        r'tubewell',
        r'tube-well',
        r'bore well',
        r'borewell',
        r'bore-well',
        r'deep tubewell',
        r'deep tube',
        r'shallow tubewell',
        r'shallow tube',
        r'hand pump',  # handpumps are often tube wells
        r'handpump',
    ]
    for pattern in tube_well_patterns:
        if re.search(pattern, s):
            return 'tube_well'
    
    # Handpump specific
    handpump_patterns = [
        r'hand\s*pump',
        r'handpump',
    ]
    for pattern in handpump_patterns:
        if re.search(pattern, s):
            return 'handpump'
    
    # Well patterns (traditional/open well)
    well_patterns = [
        r'^well$',
        r'open well',
        r'dug well',
        r'traditional well',
    ]
    for pattern in well_patterns:
        if re.search(pattern, s):
            return 'well'
    
    # Spring patterns
    spring_patterns = [
        r'spring',
        r'natural spring',
    ]
    for pattern in spring_patterns:
        if re.search(pattern, s):
            return 'spring'
    
    # Surface water patterns
    surface_patterns = [
        r'surface water',
        r'river',
        r'lake',
        r'pond',
        r'reservoir',
        r'canal',
    ]
    for pattern in surface_patterns:
        if re.search(pattern, s):
            return 'surface_water'
    
    # Other known types
    other_patterns = [
        r'rainwater',
        r'rain water',
        r'harvest',
    ]
    for pattern in other_patterns:
        if re.search(pattern, s):
            return 'other'
    
    # If it's a person name (contains common name patterns), location, ward, school, etc.
    # These are not source types - mark as unknown
    location_indicators = [
        r'ward\s*no',
        r'ward\s*\d+',
        r'anganwadi',
        r'anganwari',
        r'anganbadi',
        r'school',
        r'vidyalay',
        r'pathshala',
        r'panchayat',
        r'masjid',
        r'mandir',
        r'temple',
        r'mosque',
        r'center',
        r'kendra',
        r'near\s',
        r'at\s',
        r'in\s+habitation',
        r'location\s*:',
        r'name\s*:',
        r'^w\s*\d+',
        r'^y\s*t$',
        r'^c\s*d$',
        r'^b\s*t$',
        r'^d\s*t$',
        r'^e\s*t$',
        r'^h\s*t$',
        r'^j\s*t$',
        r'^k\s*t$',
        r'^m\s*t$',
        r'^n\s*d$',
        r'^p\s*t$',
        r'^r\s*t$',
        r'^s\s*b$',
        r'^s\s*s$',
        r'^h\s*s\s*p$',
        r'^a\s*t$',
        r'^j\s*o$',
        r'^p\s*k$',
        r'^u\s*m\s*s',
        r'^u\.m\.s',
        r'^h\.s\.s',
        r'^m\.s\.',
        r'^p\.s\.',
        r'retesting',
        r'^\d+$',  # Pure numbers
        r'^\d{7,}$',  # Long numbers (IDs)
        r'^[a-z]{1,3}$',  # Very short codes
        r'^[A-Z]{1,3}$',  # Very short codes
    ]
    
    # Check for person names (first/last name patterns)
    # Many entries are clearly person names
    name_indicators = [
        r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # First Last
        r'^[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+$',  # First M. Last
        r'^[A-Z][a-z]+\s+kumar$',
        r'^[A-Z][a-z]+\s+devi$',
        r'^[A-Z][a-z]+\s+yadav$',
        r'^[A-Z][a-z]+\s+singh$',
        r'^[A-Z][a-z]+\s+mandal$',
        r'^[A-Z][a-z]+\s+sah$',
        r'^[A-Z][a-z]+\s+paswan$',
        r'^[A-Z][a-z]+\s+ram$',
        r'^[A-Z][a-z]+\s+mahto$',
        r'^[A-Z][a-z]+\s+das$',
        r'^[A-Z][a-z]+\s+mahto$',
        r'^[A-Z][a-z]+\s+ray$',
        r'^[A-Z][a-z]+\s+ojha$',
        r'^[A-Z][a-z]+\s+pandey$',
        r'^[A-Z][a-z]+\s+thakur$',
        r'^[A-Z][a-z]+\s+chaudhary$',
        r'^[A-Z][a-z]+\s+ansari$',
        r'^[a-z]+\s+[a-z]+$',  # lowercase names
    ]
    
    for pattern in location_indicators:
        if re.search(pattern, s):
            return 'unknown'
    
    for pattern in name_indicators:
        if re.search(pattern, s):
            return 'unknown'
    
    # Check if it's mostly a person name (contains space and looks like name)
    words = s.split()
    if len(words) >= 2:
        # Check if all words start with capital or are common name parts
        name_like = True
        for w in words:
            if w.lower() in ['s/o', 's/o.', 'son', 'of', 'w/o', 'wife', 'c/o', 'c/o.']:
                continue
            if not (w[0].isupper() or w.islower()):
                name_like = False
                break
        if name_like and not any(kw in s for kw in ['tap', 'well', 'tube', 'hand', 'pipe', 'water', 'pump']):
            return 'unknown'
    
    # Default to unknown for anything not matched
    return 'unknown'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all source types
    source_types = get_all_source_types(conn)
    print(f"Found {len(source_types)} distinct source_type values")
    print(f"Total rows: {sum(cnt for _, cnt in source_types)}")
    
    # Create mapping
    mapping = {}
    for source_type, count in source_types:
        normalized = normalize_source_type(source_type)
        mapping[source_type] = normalized
        print(f"  '{source_type}' ({count}) -> '{normalized}'")
    
    # Verify all mappings are in controlled vocabulary
    invalid = [v for v in mapping.values() if v not in CONTROLLED_VOCAB]
    if invalid:
        print(f"\nERROR: Invalid mappings found: {set(invalid)}")
        return
    
    # Show summary
    print("\n=== MAPPING SUMMARY ===")
    summary = defaultdict(int)
    for orig, norm in mapping.items():
        # Get count for this original value
        cursor.execute("SELECT COUNT(*) FROM water_samples WHERE source_type = ?", (orig,))
        cnt = cursor.fetchone()[0]
        summary[norm] += cnt
    
    for vocab in CONTROLLED_VOCAB:
        print(f"  {vocab}: {summary.get(vocab, 0)} rows")
    
    # Auto-proceed (non-interactive)
    print("\nProceeding with update...")
    
    # Perform updates
    print("\nUpdating database...")
    updated = 0
    for orig, norm in mapping.items():
        cursor.execute(
            "UPDATE water_samples SET source_type = ? WHERE source_type = ?",
            (norm, orig)
        )
        updated += cursor.rowcount
        print(f"  Updated {cursor.rowcount} rows: '{orig}' -> '{norm}'")
    
    conn.commit()
    print(f"\nTotal rows updated: {updated}")
    
    # Verify
    cursor.execute("SELECT source_type, COUNT(*) FROM water_samples GROUP BY source_type ORDER BY COUNT(*) DESC")
    print("\n=== VERIFICATION ===")
    for st, cnt in cursor.fetchall():
        status = "OK" if st in CONTROLLED_VOCAB else "INVALID"
        print(f"  {st}: {cnt} [{status}]")
    
    # Add CHECK constraint
    print("\nAdding CHECK constraint...")
    try:
        # SQLite doesn't support ADD CONSTRAINT directly, need to recreate table
        # But we can create a trigger instead
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS check_source_type_valid
            BEFORE INSERT ON water_samples
            FOR EACH ROW
            BEGIN
                SELECT CASE
                    WHEN NEW.source_type NOT IN ('handpump', 'tube_well', 'piped_supply', 'well', 'spring', 'surface_water', 'other', 'unknown')
                    THEN RAISE(ABORT, 'Invalid source_type: ' || NEW.source_type || '. Must be one of: handpump, tube_well, piped_supply, well, spring, surface_water, other, unknown')
                END;
            END;
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS check_source_type_valid_update
            BEFORE UPDATE ON water_samples
            FOR EACH ROW
            BEGIN
                SELECT CASE
                    WHEN NEW.source_type NOT IN ('handpump', 'tube_well', 'piped_supply', 'well', 'spring', 'surface_water', 'other', 'unknown')
                    THEN RAISE(ABORT, 'Invalid source_type: ' || NEW.source_type || '. Must be one of: handpump, tube_well, piped_supply, well, spring, surface_water, other, unknown')
                END;
            END;
        """)
        conn.commit()
        print("Triggers created successfully.")
    except Exception as e:
        print(f"Error creating triggers: {e}")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()