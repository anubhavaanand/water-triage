#!/usr/bin/env python3
"""
Enrich 4 low-coverage districts (Barabanki, Budaun, Gaya, Madhepura) 
with CGWB data by inserting water_samples and readings.
"""
import sqlite3
import csv
from datetime import datetime
from collections import defaultdict

DB_PATH = "/home/anubhavanand/Documents/Projects/water-triage/data/watertriage.db"
CGWB_PATH = "/home/anubhavanand/Documents/Projects/water-triage/backend/data/cgwb_extracted.csv"

# District to state mapping and "Not available" village IDs
# Some districts appear in CGWB under multiple states - we'll match on district name only
DISTRICT_INFO = {
    "Barabanki": {"state": "Uttar Pradesh", "village_id": 84, "cgwb_district": "Barabanki", "cgwb_states": ["bihar"]},
    "Budaun": {"state": "Uttar Pradesh", "village_id": 77, "cgwb_district": "Budaun", "cgwb_states": ["up", "bihar"]},
    "Gaya": {"state": "Bihar", "village_id": 105, "cgwb_district": "Gaya", "cgwb_states": ["bihar"]},
    "Madhepura": {"state": "Bihar", "village_id": 72, "cgwb_district": "Madhepura", "cgwb_states": ["bihar"]},
}

# CGWB parameter -> BIS parameter key mapping
CGWB_TO_BIS = {
    "ph": "ph",
    "tds": "tds",
    "fluoride": "fluoride",
    "arsenic": "arsenic",
    "nitrate": "nitrate",
    "sulphate": "sulphate",  # stored but not scored per AGENTS.md
    "ec": "ec",  # electrical conductivity - not in BIS
    "hardness": "hardness",  # not in BIS
    "chloride": "chloride",  # not in BIS
    "bicarbonate": "bicarbonate",  # not in BIS
    "carbonate": "carbonate",  # not in BIS
}

# Unit conversion: CGWB uses μg/L for arsenic, but BIS uses mg/L
# 1 mg/L = 1000 μg/L
PARAM_UNIT_CONVERSION = {
    "arsenic": 0.001,  # CGWB μg/L -> BIS mg/L
}

# BIS parameters that are scored
BIS_KEYS = {"ph", "tds", "fluoride", "arsenic", "nitrate", "iron", "turbidity", "e_coli"}

def load_cgwb_data():
    """Load and filter CGWB data for the 4 districts."""
    district_data = defaultdict(lambda: defaultdict(list))
    
    with open(CGWB_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cgwb_state = row['state'].strip().lower()
            cgwb_district = row['district'].strip()
            param = row['parameter'].strip().lower()
            value = float(row['value'])
            year = row['year'].strip()
            
            # Match to our districts (check multiple possible CGWB states)
            for dist_name, info in DISTRICT_INFO.items():
                if cgwb_state in info['cgwb_states'] and info['cgwb_district'].lower() == cgwb_district.lower():
                    bis_key = CGWB_TO_BIS.get(param)
                    if bis_key:
                        district_data[dist_name][bis_key].append({
                            'value': value,
                            'year': year,
                            'source': row['source'],
                            'pdf_page': row['pdf_page']
                        })
    return district_data

def parse_year(year_str):
    """Parse year string like '2023-24' or '2024' to integer year."""
    if '-' in year_str:
        return int(year_str.split('-')[0])
    return int(year_str)

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Load CGWB data
    district_data = load_cgwb_data()
    
    print("CGWB data loaded for districts:")
    for dist, params in district_data.items():
        print(f"  {dist}: {list(params.keys())}")
    
    # Process each district
    for dist_name, info in DISTRICT_INFO.items():
        village_id = info['village_id']
        params = district_data.get(dist_name, {})
        
        if not params:
            print(f"\n{dist_name}: No CGWB data found!")
            continue
        
        print(f"\n--- Processing {dist_name} (village_id={village_id}) ---")
        
        # Get BIS parameters that have data
        bis_params_with_data = [p for p in params.keys() if p in BIS_KEYS]
        print(f"  BIS parameters with data: {bis_params_with_data}")
        
        if not bis_params_with_data:
            print(f"  No BIS parameters found, skipping")
            continue
        
        # Create a water sample for this district (using "Not available" village)
        # Use the earliest year from data as collection date
        years = []
        for p_data in params.values():
            for reading in p_data:
                years.append(parse_year(reading['year']))
        collected_year = min(years) if years else 2024
        
        # Insert water_sample
        cursor.execute("""
            INSERT INTO water_samples (village_id, source_type, collected_on, lab_name, wqmis_ref, created_at, is_located)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            village_id,
            'handpump',  # generic source type
            f"{collected_year}-01-01 00:00:00",
            'CGWB Year Book',
            f'CGWB-{dist_name}-{collected_year}',
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            1
        ))
        sample_id = cursor.lastrowid
        print(f"  Created water_sample id={sample_id}")
        
        # Insert readings for each parameter
        for param_key, readings in params.items():
            if param_key not in BIS_KEYS:
                continue  # only insert BIS-scored parameters
            
            # Use the median value as representative
            values = [r['value'] for r in readings]
            values.sort()
            median_value = values[len(values) // 2]
            
            # Apply unit conversion if needed
            if param_key in PARAM_UNIT_CONVERSION:
                median_value = median_value * PARAM_UNIT_CONVERSION[param_key]
                print(f"  Unit conversion: {param_key} {values[len(values)//2]} -> {median_value}")
            
            cursor.execute("""
                INSERT INTO readings (sample_id, parameter_key, value)
                VALUES (?, ?, ?)
            """, (sample_id, param_key, median_value))
            print(f"  Inserted reading: {param_key} = {median_value} (from {len(values)} CGWB readings)")
        
        # Compute risk score for this sample
        # We need to calculate severity score using BIS weights
        cursor.execute("SELECT key, weight, acceptable_limit, permissible_limit, strategy FROM bis_parameters")
        bis_params = {row[0]: {"weight": row[1], "acceptable": row[2], "permissible": row[3], "strategy": row[4]} for row in cursor.fetchall()}
        
        # Get readings for this sample
        cursor.execute("SELECT parameter_key, value FROM readings WHERE sample_id = ?", (sample_id,))
        sample_readings = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Calculate severity score
        total_score = 0.0
        worst_param = None
        worst_score = 0.0
        
        for param_key, value in sample_readings.items():
            if param_key not in bis_params:
                continue
            bp = bis_params[param_key]
            weight = bp["weight"]
            acceptable = bp["acceptable"]
            permissible = bp["permissible"]
            strategy = bp["strategy"]
            
            # Calculate sub-score based on strategy
            if strategy == "threshold":
                if permissible is not None and value > permissible:
                    sub_score = weight * 100
                elif value > acceptable:
                    # Linear interpolation between acceptable and permissible
                    if permissible is not None and permissible > acceptable:
                        sub_score = weight * 50 * (value - acceptable) / (permissible - acceptable)
                    else:
                        sub_score = weight * 50
                else:
                    sub_score = 0
            elif strategy == "range":
                # pH: outside [acceptable, permissible] range
                if value < acceptable or value > permissible:
                    sub_score = weight * 100
                else:
                    sub_score = 0
            elif strategy == "microbial":
                # E. coli: any detection is bad
                if value > 0:
                    sub_score = weight * 100
                else:
                    sub_score = 0
            else:
                sub_score = 0
            
            total_score += sub_score
            if sub_score > worst_score:
                worst_score = sub_score
                worst_param = param_key
        
        # Determine band
        if total_score >= 75:
            band = "Critical"
        elif total_score >= 50:
            band = "High"
        elif total_score >= 25:
            band = "Medium"
        else:
            band = "Low"
        
        # Insert risk score
        cursor.execute("""
            INSERT INTO risk_scores (sample_id, score, band, worst_parameter, computed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (sample_id, total_score, band, worst_param, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        print(f"  Risk score: {total_score:.1f} ({band}), worst: {worst_param}")
        
        # Update district parameter_count and data_quality
        param_count = len(bis_params_with_data)
        
        if param_count >= 7:
            quality = "high_coverage"
        elif param_count >= 4:
            quality = "medium_coverage"
        elif param_count >= 2:
            quality = "low_coverage"
        else:
            quality = "very_low_coverage"
        
        cursor.execute("""
            UPDATE districts 
            SET parameter_count = ?, data_quality = ?
            WHERE name = ? AND state_id = (SELECT id FROM states WHERE name = ?)
        """, (param_count, quality, dist_name, info['state']))
        
        print(f"  Updated district: parameter_count={param_count}, data_quality={quality}")
    
    conn.commit()
    
    # Verify results
    print("\n=== VERIFICATION ===")
    cursor.execute("""
        SELECT d.name, s.name as state, d.parameter_count, d.data_quality
        FROM districts d
        JOIN states s ON d.state_id = s.id
        WHERE d.name IN ('Barabanki', 'Budaun', 'Gaya', 'Madhepura')
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]}): param_count={row[2]}, quality={row[3]}")
    
    cursor.execute("""
        SELECT d.name as district, r.parameter_key, COUNT(*) as count
        FROM readings r
        JOIN water_samples ws ON r.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        WHERE d.name IN ('Barabanki', 'Budaun', 'Gaya', 'Madhepura')
        GROUP BY d.name, r.parameter_key
        ORDER BY d.name, r.parameter_key;
    """)
    print("\nReadings by district and parameter:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} = {row[2]}")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()