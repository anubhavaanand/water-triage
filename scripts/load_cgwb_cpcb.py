import os, glob
import pandas as pd
from sqlalchemy import create_engine

print("Loading CGWB 2012-2021 Data...")
cgwb_files = glob.glob('Downloaded_Datasets/gw_quality_2012_2021/Ground Water *.csv')
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
        pass

if cgwb_list:
    cgwb_full = pd.concat(cgwb_list, ignore_index=True)
    engine = create_engine(os.environ.get("DATABASE_URL"))
    cgwb_full.to_sql('staging_cgwb', engine, if_exists='replace', index=False)
    print(f"Loaded {len(cgwb_full)} CGWB records (UP/Bihar).")
else:
    print("No CGWB data for UP/Bihar found.")

print("Loading CPCB 2021-2023 Data...")
cpcb_file = 'codebase/data/raw/kaggle/iwq_2021_2023/Indian_water_data.csv'
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
