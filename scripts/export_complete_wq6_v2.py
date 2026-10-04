#!/usr/bin/env python3
"""
Export COMPLETE WQ6 parsed data - properly separated by state
"""

import os
import re
import pandas as pd
from bs4 import BeautifulSoup

CONTAMINANT_COLS = [
    'pH', 'TDS', 'Turbidity', 'Chloride', 'Total_Alkalinity', 'Total_Hardness',
    'Sulphate', 'Iron', 'Total_Arsenic', 'Fluoride', 'Nitrate', 'Residual_Chlorine',
    'Others_chem', 'E_coli', 'Total_Coliform', 'Others_bact'
]

def normalize_district(name):
    if not name or name in ['Total', 'S.No.', 'District name', 'State']:
        return None
    name = re.sub(r'\(\d+\)', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

# Known districts for each state
BIHAR_DISTRICTS = {
    'Araria', 'Arwal', 'Aurangabad', 'Banka', 'Begusarai', 'Bhagalpur', 
    'Bhojpur', 'Buxar', 'Darbhanga', 'Gaya', 'Gopalganj', 'Jamui', 
    'Jehanabad', 'Kaimur', 'Katihar', 'Khagaria', 'Kishanganj', 'Lakhisarai', 
    'Madhepura', 'Madhubani', 'Munger', 'Muzaffarpur', 'Nalanda', 'Nawada', 
    'Patna', 'Purnia', 'Rohtas', 'Saharsa', 'Samastipur', 'Saran', 'Sheikhpura', 
    'Sheohar', 'Sitamarhi', 'Siwan', 'Supaul', 'Vaishali', 'West Champaran', 'East Champaran'
}

UP_DISTRICTS = {
    'Agra', 'Aligarh', 'Ambedkar Nagar', 'Amethi', 'Amroha', 'Auraiya', 'Ayodhya',
    'Azamgarh', 'Baghpat', 'Bahraich', 'Ballia', 'Balrampur', 'Banda', 'Bara Banki',
    'Bareilly', 'Basti', 'Bhadohi', 'Bijnor', 'Budaun', 'Bulandshahr', 'Chandauli',
    'Chitrakoot', 'Deoria', 'Etah', 'Etawah', 'Farrukhabad', 'Fatehpur', 'Firozabad',
    'Gautam Buddha Nagar', 'Ghaziabad', 'Ghazipur', 'Gonda', 'Gorakhpur', 'Hamirpur',
    'Hapur', 'Hardoi', 'Hathras', 'Jalaun', 'Jaunpur', 'Jhansi', 'Kannauj', 
    'Kanpur Dehat', 'Kanpur Nagar', 'Kasganj', 'Kaushambi', 'Kheri', 'Kushinagar',
    'Lalitpur', 'Lucknow', 'Mahoba', 'Mahrajganj', 'Mainpuri', 'Mathura', 'Mau',
    'Meerut', 'Mirzapur', 'Moradabad', 'Muzaffarnagar', 'Pilibhit', 'Pratapgarh',
    'Prayagraj', 'Rae Bareli', 'Rampur', 'Saharanpur', 'Sambhal', 'Sant Kabir Nagar',
    'Shahjahanpur', 'Shamli', 'Shrawasti', 'Siddharthnagar', 'Sitapur', 'Sonbhadra',
    'Sultanpur', 'Unnao', 'Varanasi'
}

def parse_wq6_file(filepath):
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
    df = df[df['district'] != 'Total']
    return df

def assign_state(district):
    d = district.strip()
    if d in BIHAR_DISTRICTS:
        return 'Bihar'
    if d in UP_DISTRICTS:
        return 'Uttar Pradesh'
    # Fuzzy match for common variations
    d_lower = d.lower()
    for bd in BIHAR_DISTRICTS:
        if bd.lower() in d_lower or d_lower in bd.lower():
            return 'Bihar'
    for ud in UP_DISTRICTS:
        if ud.lower() in d_lower or d_lower in ud.lower():
            return 'Uttar Pradesh'
    return 'Unknown'

# File groups
bihar_files = [
    '/home/anubhavanand/Downloads/Water_Triage_Data/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) (1).xls',
]
for i in range(2, 10):
    bihar_files.append(f'/home/anubhavanand/Downloads/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) ({i}).xls')

up_files = [
    f'/home/anubhavanand/Downloads/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) ({i}).xls'
    for i in range(10, 14)
]

all_bihar = []
all_up = []

print("Parsing Bihar files (1-9)...")
for fpath in bihar_files:
    if os.path.exists(fpath):
        df = parse_wq6_file(fpath)
        if df is not None and len(df) > 0:
            df['source_file'] = os.path.basename(fpath)
            df['state'] = df['district'].apply(assign_state)
            bihar_only = df[df['state'] == 'Bihar'].copy()
            all_bihar.append(bihar_only)
            print(f"  {os.path.basename(fpath)}: {len(bihar_only)} Bihar districts")

print("\nParsing UP files (10-13)...")
for fpath in up_files:
    if os.path.exists(fpath):
        df = parse_wq6_file(fpath)
        if df is not None and len(df) > 0:
            df['source_file'] = os.path.basename(fpath)
            df['state'] = df['district'].apply(assign_state)
            up_only = df[df['state'] == 'Uttar Pradesh'].copy()
            all_up.append(up_only)
            print(f"  {os.path.basename(fpath)}: {len(up_only)} UP districts")

# Combine and deduplicate
if all_bihar:
    bihar_combined = pd.concat(all_bihar, ignore_index=True)
    agg_cols = ['district'] + CONTAMINANT_COLS
    bihar_final = bihar_combined[agg_cols].groupby('district').max().reset_index()
    bihar_final['state'] = 'Bihar'
    print(f"\nFinal Bihar districts: {len(bihar_final)}")
    
    # Add missing Bihar districts with zeros
    missing = BIHAR_DISTRICTS - set(bihar_final['district'])
    if missing:
        print(f"Adding {len(missing)} missing Bihar districts with zeros")
        for d in missing:
            row = {'district': d, 'state': 'Bihar'}
            for c in CONTAMINANT_COLS:
                row[c] = 0
            bihar_final = pd.concat([bihar_final, pd.DataFrame([row])], ignore_index=True)
    
    bihar_final = bihar_final.sort_values('district').reset_index(drop=True)
    
    out_xlsx = "/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_Bihar.xlsx"
    out_csv = "/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_Bihar.csv"
    bihar_final.to_excel(out_xlsx, index=False)
    bihar_final.to_csv(out_csv, index=False)
    print(f"Saved Bihar: {out_xlsx} ({len(bihar_final)} districts)")

if all_up:
    up_combined = pd.concat(all_up, ignore_index=True)
    agg_cols = ['district'] + CONTAMINANT_COLS
    up_final = up_combined[agg_cols].groupby('district').max().reset_index()
    up_final['state'] = 'Uttar Pradesh'
    print(f"\nFinal UP districts: {len(up_final)}")
    
    missing = UP_DISTRICTS - set(up_final['district'])
    if missing:
        print(f"Adding {len(missing)} missing UP districts with zeros")
        for d in missing:
            row = {'district': d, 'state': 'Uttar Pradesh'}
            for c in CONTAMINANT_COLS:
                row[c] = 0
            up_final = pd.concat([up_final, pd.DataFrame([row])], ignore_index=True)
    
    up_final = up_final.sort_values('district').reset_index(drop=True)
    
    out_xlsx = "/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_UP.xlsx"
    out_csv = "/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_UP.csv"
    up_final.to_excel(out_xlsx, index=False)
    up_final.to_csv(out_csv, index=False)
    print(f"Saved UP: {out_xlsx} ({len(up_final)} districts)")

print("\nDone!")