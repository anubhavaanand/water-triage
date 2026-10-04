#!/usr/bin/env python3
"""
Export COMPLETE WQ6 parsed data as full Excel sheets
All districts from WQ6 files, not just our corpus matches
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

# Bihar files
bihar_files = [
    '/home/anubhavanand/Downloads/Water_Triage_Data/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) (1).xls',
]
for i in range(2, 10):
    bihar_files.append(f'/home/anubhavanand/Downloads/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) ({i}).xls')

# UP files
up_files = [
    f'/home/anubhavanand/Downloads/Format WQ6. Contaminant wise details of villages where in water samples were found contaminated(PWS Sources test from Lab) ({i}).xls'
    for i in range(10, 14)
]

bihar_dfs = []
up_dfs = []

print("Parsing Bihar WQ6 files...")
for fpath in bihar_files:
    if os.path.exists(fpath):
        df = parse_wq6_file(fpath)
        if df is not None and len(df) > 0:
            df['source_file'] = os.path.basename(fpath)
            bihar_dfs.append(df)
            print(f"  {os.path.basename(fpath)}: {len(df)} districts")

print("\nParsing UP WQ6 files...")
for fpath in up_files:
    if os.path.exists(fpath):
        df = parse_wq6_file(fpath)
        if df is not None and len(df) > 0:
            df['source_file'] = os.path.basename(fpath)
            up_dfs.append(df)
            print(f"  {os.path.basename(fpath)}: {len(df)} districts")

# Combine and deduplicate (take max across files)
if bihar_dfs:
    bihar_all = pd.concat(bihar_dfs, ignore_index=True)
    agg_cols = ['district'] + CONTAMINANT_COLS
    bihar_all = bihar_all[agg_cols].groupby('district').max().reset_index()
    bihar_all['state'] = 'Bihar'
    print(f"\nTotal unique Bihar districts: {len(bihar_all)}")
    
    # Export
    out_path = "/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_Bihar.xlsx"
    bihar_all.to_excel(out_path, index=False)
    print(f"Saved: {out_path}")

if up_dfs:
    up_all = pd.concat(up_dfs, ignore_index=True)
    agg_cols = ['district'] + CONTAMINANT_COLS
    up_all = up_all[agg_cols].groupby('district').max().reset_index()
    up_all['state'] = 'Uttar Pradesh'
    print(f"\nTotal unique UP districts: {len(up_all)}")
    
    out_path = "/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_UP.xlsx"
    up_all.to_excel(out_path, index=False)
    print(f"Saved: {out_path}")

# Also export as CSV for easy viewing
if bihar_dfs:
    bihar_all.to_csv("/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_Bihar.csv", index=False)
if up_dfs:
    up_all.to_csv("/home/anubhavanand/Documents/Projects/water-triage/WQ6_Complete_UP.csv", index=False)

print("\nDone!")