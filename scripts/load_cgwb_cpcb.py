import os, glob, sys
import pandas as pd
from sqlalchemy import create_engine

# Resolve paths relative to the repo root so the script works from any cwd.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAGGLE = os.path.join(ROOT, "data", "raw", "kaggle")

print("Loading CGWB 2012-2021 Data...")
cgwb_files = glob.glob(os.path.join(KAGGLE, "gw_quality_2012_2021", "Ground Water *.csv"))
if not cgwb_files:
    # The published CGWB extract in this repo is a Power BI .pbix, not CSVs.
    # Say so instead of reporting "no data for UP/Bihar", which reads like a
    # filtering result rather than a missing input.
    pbix = glob.glob(os.path.join(KAGGLE, "gw_quality_2012_2021", "*.pbix"))
    if pbix:
        print(f"CGWB CSVs not found; found Power BI extract at {pbix[0]}. Export to CSV first.")
    else:
        print(f"CGWB CSVs not found under {KAGGLE}/gw_quality_2012_2021/.")
cgwb_list = []
for f in cgwb_files:
    try:
        df = pd.read_csv(f)
        # Filter UP and Bihar
        if 'STATE' in df.columns:
            df = df[df['STATE'].isin(['UTTAR PRADESH', 'BIHAR', 'Uttar Pradesh', 'Bihar', 'uttar pradesh', 'bihar'])]
            # Try to extract district from "BORE WELL AT XXXX, DISTRICT" if possible, or just keep raw
            if not df.empty:
                df.columns = [c.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_') for c in df.columns]
                cgwb_list.append(df)
    except Exception as e:
        print(f"  [WARN] skipping {os.path.basename(f)}: {e}")

if cgwb_list:
    cgwb_full = pd.concat(cgwb_list, ignore_index=True)
    engine = create_engine(os.environ.get("DATABASE_URL"))
    cgwb_full.to_sql('staging_cgwb', engine, if_exists='replace', index=False)
    print(f"Loaded {len(cgwb_full)} CGWB records (UP/Bihar).")
else:
    print("No CGWB data for UP/Bihar found.")

print("Loading CPCB 2021-2023 Data...")
cpcb_file = os.path.join(KAGGLE, "iwq_2021_2023", "Indian_water_data.csv")
if not os.path.exists(cpcb_file):
    print(f"CPCB file not found at {cpcb_file}; skipping. Expected the iwq_2021_2023 extract.")
if os.path.exists(cpcb_file):
    try:
        cpcb = pd.read_csv(cpcb_file, encoding='latin1')
        cpcb = cpcb[cpcb['State Name'].isin(['UTTAR PRADESH', 'BIHAR'])]
        cpcb.columns = [c.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_') for c in cpcb.columns]
        engine = create_engine(os.environ.get("DATABASE_URL"))
        cpcb.to_sql('staging_cpcb', engine, if_exists='replace', index=False)
        print(f"Loaded {len(cpcb)} CPCB records (UP/Bihar).")
    except Exception as e:
        print("Error loading CPCB:", e)
