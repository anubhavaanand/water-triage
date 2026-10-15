#!/usr/bin/env python3
import os
import glob
import pandas as pd
from bs4 import BeautifulSoup
import re
try:
    from district_registry import CANONICAL_DISTRICTS
except ImportError:
    from scripts.district_registry import CANONICAL_DISTRICTS

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
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    state_span = soup.find('span', class_='State_Name')
    if not state_span:
        return None, None
    state = state_span.get_text(strip=True).title()
    if state not in ['Bihar', 'Uttar Pradesh']:
        return None, None
        
    tables = soup.find_all('table')
    if not tables:
        return None, None
    table = tables[0]
    
    data = []
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        vals = [c.get_text(strip=True) for c in cells]
        if len(vals) >= 18:
            data.append(vals)
            
    df_rows = []
    for row in data:
        if row[0].isdigit() or row[1] == 'Total':
            df_rows.append(row)
            
    if not df_rows:
        return None, state
        
    df = pd.DataFrame(df_rows, columns=['sno', 'district'] + CONTAMINANT_COLS)
    for col in CONTAMINANT_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
    df['district'] = df['district'].apply(normalize_district)
    df = df[df['district'].notna()]
    df = df[df['district'] != 'Total']
    df['state'] = state
    
    return df, state

files = glob.glob('data/raw/official/WQ6_*.xls')
all_data = {'Bihar': [], 'Uttar Pradesh': []}

for f in files:
    df, state = parse_wq6_file(f)
    if df is not None:
        all_data[state].append(df)

for state in ['Bihar', 'Uttar Pradesh']:
    if all_data[state]:
        combined = pd.concat(all_data[state], ignore_index=True)
        agg_cols = ['district'] + CONTAMINANT_COLS
        final = combined[agg_cols].groupby('district').max().reset_index()
        final = final[final['district'].isin(CANONICAL_DISTRICTS[state])].copy()
        final['state'] = state
        
        out_csv = f"data/validation_reports/WQ6_Complete_{state.replace(' ', '')}.csv"
        final.to_csv(out_csv, index=False)
        print(f"Saved {out_csv} ({len(final)} districts)")

