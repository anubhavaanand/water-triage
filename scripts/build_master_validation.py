#!/usr/bin/env python3
"""
Build Master Validation Tables for WaterTriage
Joins: Our Corpus (1,741 samples) + IMIS 2009-12 + CGWB 2012-21 (state) + WQ6 2024
Outputs: Master_Validation_Bihar.csv, Master_Validation_UP.csv
"""

import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://jjm_user:postgres@localhost:5432/jjm_triage"
engine = create_engine(DATABASE_URL)

# Contaminant mapping
CONTAMINANT_COLS = [
    'pH', 'TDS', 'Turbidity', 'Chloride', 'Total_Alkalinity', 'Total_Hardness',
    'Sulphate', 'Iron', 'Total_Arsenic', 'Fluoride', 'Nitrate', 'Residual_Chlorine',
    'Others_chem', 'E_coli', 'Total_Coliform', 'Others_bact'
]

# District name normalization
def normalize_district(name):
    """Normalize district names for joining"""
    if not name or name in ['Total', 'S.No.', 'District name', 'State']:
        return None
    name = re.sub(r'\(\d+\)', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

def parse_wq6_file(filepath):
    """Parse a WQ6 HTML table file (district-level)"""
    with open(filepath, 'r') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return None
    table = tables[0]
    rows = table.find_all('tr')
    
    data = []
    for row in rows:
        cells = row.find_all(['td', 'th'])
        vals = [c.get_text(strip=True) for c in cells]
        if len(vals) >= 18:
            data.append(vals)
    
    if not data:
        return None
    
    df_rows = []
    for row in data[3:]:
        if row[0].isdigit() or row[1] == 'Total':
            df_rows.append(row)
    
    if not df_rows:
        return None
    
    df = pd.DataFrame(df_rows, columns=['sno', 'district'] + CONTAMINANT_COLS)
    
    for col in CONTAMINANT_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    df['district'] = df['district'].apply(normalize_district)
    df = df[df['district'].notna()]
    return df

def load_cgwb_state():
    """Load CGWB 2012-2021 data - state level only"""
    cgwb_dir = "/home/anubhavanand/Documents/Projects/water-triage/data/raw/kaggle/gw_quality_2012_2021/"
    all_data = []
    
    for year in range(2012, 2022):
        if year == 2020:
            continue
        fname = f"Ground Water {year}.csv"
        fpath = os.path.join(cgwb_dir, fname)
        if not os.path.exists(fpath):
            continue
        df = pd.read_csv(fpath)
        df.columns = [c.strip().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_') for c in df.columns]
        if 'STATE' in df.columns:
            df = df[df['STATE'].str.upper().isin(['UTTAR PRADESH', 'BIHAR'])]
        if len(df) == 0:
            continue
        df['year'] = year
        all_data.append(df)
        print(f"  Loaded {len(df)} rows from {fname}")
    
    if not all_data:
        return pd.DataFrame()
    combined = pd.concat(all_data, ignore_index=True)
    combined['state'] = combined['STATE'].str.title()
    return combined

def get_cgwb_state_agg(cgwb_df):
    """Aggregate CGWB data by state/year"""
    if cgwb_df.empty:
        return pd.DataFrame()
    if 'pH_Min' in cgwb_df.columns and 'pH_Max' in cgwb_df.columns:
        cgwb_df['pH_mean'] = (cgwb_df['pH_Min'] + cgwb_df['pH_Max']) / 2
        agg = cgwb_df.groupby(['state', 'year']).agg(
            stations=('Station_Code', 'count'),
            ph_exceed_pct=('pH_mean', lambda x: ((x < 6.5) | (x > 8.5)).mean() * 100)
        ).reset_index()
        agg['ph_exceed_pct'] = agg['ph_exceed_pct'].round(1)
        return agg
    return pd.DataFrame()

def get_our_corpus():
    """Get our WQMIS corpus exceedance by district"""
    query = text("""
        SELECT 
            d.name as district,
            s.name as state,
            COUNT(DISTINCT ws.id) as our_samples,
            COUNT(CASE WHEN 
                (bp.strategy = 'range' AND (r.value < bp.acceptable_limit OR r.value > COALESCE(bp.permissible_limit, 8.5)))
                OR (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
            THEN 1 END) as our_exceedances,
            COUNT(CASE WHEN bp.key = 'iron' AND 
                (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
            THEN 1 END) as our_iron_exceed,
            COUNT(CASE WHEN bp.key = 'arsenic' AND 
                (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
            THEN 1 END) as our_arsenic_exceed,
            COUNT(CASE WHEN bp.key = 'fluoride' AND 
                (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
            THEN 1 END) as our_fluoride_exceed,
            COUNT(CASE WHEN bp.key = 'nitrate' AND 
                (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
            THEN 1 END) as our_nitrate_exceed,
            COUNT(CASE WHEN bp.key = 'e_coli' AND 
                r.value > bp.acceptable_limit
            THEN 1 END) as our_ecoli_exceed
        FROM water_samples ws
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        LEFT JOIN readings r ON r.sample_id = ws.id
        LEFT JOIN bis_parameters bp ON r.parameter_key = bp.key
        WHERE d.name != 'Not available'
        GROUP BY d.name, s.name
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    df['district_norm'] = df['district'].apply(normalize_district)
    return df

def get_imis_data():
    """Get IMIS 2009-2012 data from staging_l3_habitations"""
    query = text("""
        SELECT 
            district,
            state,
            contaminant,
            SUM(affected_habitations) as imis_habitations
        FROM staging_l3_habitations
        GROUP BY district, state, contaminant
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    pivot = df.pivot_table(
        index=['district', 'state'], columns='contaminant', 
        values='imis_habitations', aggfunc='sum'
    ).fillna(0).astype(int).reset_index()
    pivot['district_norm'] = pivot['district'].apply(normalize_district)
    pivot['state'] = pivot['state'].str.title()
    rename_map = {
        'Iron': 'imis_iron', 'Arsenic': 'imis_arsenic', 
        'Fluoride': 'imis_fluoride', 'Nitrate': 'imis_nitrate', 'Salinity': 'imis_salinity'
    }
    pivot = pivot.rename(columns=rename_map)
    return pivot

def parse_all_wq6():
    """Parse all WQ6 district-level files"""
    bihar_files = [
        '/home/anubhavanand/Downloads/Water_Triage_Data/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) (1).xls',
    ]
    # Files 2-9 in Downloads
    for i in range(2, 10):
        bihar_files.append(f'/home/anubhavanand/Downloads/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) ({i}).xls')
    
    up_files = [
        f'/home/anubhavanand/Downloads/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) ({i}).xls'
        for i in range(10, 14)
    ]
    
    all_dfs = []
    for fpath in bihar_files + up_files:
        if os.path.exists(fpath):
            df = parse_wq6_file(fpath)
            if df is not None and len(df) > 0:
                all_dfs.append(df)
                print(f"  Parsed {os.path.basename(fpath)}: {len(df)} districts")
    
    if not all_dfs:
        return pd.DataFrame()
    
    combined = pd.concat(all_dfs, ignore_index=True)
    combined['district_norm'] = combined['district'].apply(normalize_district)
    
    # For duplicates, take max
    agg_cols = ['district_norm'] + CONTAMINANT_COLS
    combined = combined[agg_cols].groupby('district_norm').max().reset_index()
    
    # Assign state
    bihar_districts = {
        'Araria', 'Arwal', 'Aurangabad', 'Banka', 'Begusarai', 'Bhagalpur', 
        'Bhojpur', 'Buxar', 'Darbhanga', 'Gaya', 'Gopalganj', 'Jamui', 
        'Jehanabad', 'Kaimur', 'Katihar', 'Khagaria', 'Kishanganj', 'Lakhisarai', 
        'Madhepura', 'Madhubani', 'Munger', 'Muzaffarpur', 'Nalanda', 'Nawada', 
        'Patna', 'Purnia', 'Rohtas', 'Saharsa', 'Samastipur', 'Saran', 'Sheikhpura', 
        'Sheohar', 'Sitamarhi', 'Siwan', 'Supaul', 'Vaishali', 'West Champaran', 'East Champaran'
    }
    def assign_state(d):
        return 'Bihar' if d in bihar_districts else 'Uttar Pradesh'
    combined['state'] = combined['district_norm'].apply(assign_state)
    return combined

def main():
    print("=" * 60)
    print("BUILDING MASTER VALIDATION TABLES")
    print("=" * 60)
    
    # 1. Our corpus
    print("\n1. Loading our WQMIS corpus...")
    our_df = get_our_corpus()
    print(f"   Got {len(our_df)} districts")
    
    # 2. IMIS
    print("\n2. Loading IMIS 2009-2012...")
    imis_df = get_imis_data()
    print(f"   Got {len(imis_df)} district-contaminant records")
    
    # 3. CGWB state-level
    print("\n3. Loading CGWB 2012-2021 (state-level)...")
    cgwb_raw = load_cgwb_state()
    cgwb_state = get_cgwb_state_agg(cgwb_raw)
    print(f"   State-level pH exceedance: {len(cgwb_state)} state-year records")
    
    # 4. WQ6
    print("\n4. Parsing WQ6 2024 district-level...")
    wq6_df = parse_all_wq6()
    print(f"   Got {len(wq6_df)} districts from WQ6")
    
    # 5. Build master
    print("\n5. Building master validation table...")
    
    master = our_df[['district_norm', 'state', 'our_samples', 'our_exceedances', 
                     'our_iron_exceed', 'our_arsenic_exceed', 'our_fluoride_exceed',
                     'our_nitrate_exceed', 'our_ecoli_exceed']].copy()
    
    # Merge IMIS
    imis_cols = ['district_norm', 'state', 'imis_iron', 'imis_arsenic', 'imis_fluoride', 'imis_nitrate', 'imis_salinity']
    available_imis = [c for c in imis_cols if c in imis_df.columns]
    master = master.merge(imis_df[available_imis], on=['district_norm', 'state'], how='left')
    
    # Merge WQ6
    wq6_cols = ['district_norm'] + CONTAMINANT_COLS
    available_wq6 = [c for c in wq6_cols if c in wq6_df.columns]
    master = master.merge(wq6_df[available_wq6], on='district_norm', how='left', suffixes=('', '_wq6'))
    
    master = master.fillna(0)
    
    # Split by state
    bihar = master[master['state'] == 'Bihar'].copy()
    up = master[master['state'] == 'Uttar Pradesh'].copy()
    
    # Sort by historical severity
    for df, name in [(bihar, 'Bihar'), (up, 'Uttar Pradesh')]:
        if 'imis_iron' in df.columns and 'imis_arsenic' in df.columns:
            df['combined_severity'] = df['imis_iron'] + df['imis_arsenic'] * 10
            df = df.sort_values('combined_severity', ascending=False)
        
        out_path = f"/home/anubhavanand/Documents/Projects/water-triage/Master_Validation_{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"\n   Saved {name}: {len(df)} districts -> {out_path}")
        
        # Print top 15
        print(f"\n   Top 15 {name} districts:")
        show_cols = ['district', 'our_samples', 'our_iron_exceed', 'our_arsenic_exceed', 'our_fluoride_exceed', 'our_ecoli_exceed']
        imis_cols_show = [c for c in ['imis_iron', 'imis_arsenic', 'imis_fluoride'] if c in df.columns]
        wq6_cols_show = [c for c in ['Iron', 'Total_Arsenic', 'Fluoride', 'E_coli', 'Total_Coliform'] if c in df.columns]
        show = [c for c in show_cols + imis_cols_show + wq6_cols_show if c in df.columns]
        print(df[show].head(15).to_string(index=False))
    
    # Save CGWB state summary
    if not cgwb_state.empty:
        cgwb_path = "/home/anubhavanand/Documents/Projects/water-triage/CGWB_State_Validation.csv"
        cgwb_state.to_csv(cgwb_path, index=False)
        print(f"\n   CGWB State validation -> {cgwb_path}")
        print(cgwb_state.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

if __name__ == "__main__":
    main()