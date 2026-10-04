import os
import pandas as pd
import psycopg2
import re

print("Loading historical data...")
df = pd.read_csv("data/raw/kaggle/affected_areas_2009_2012/IndiaAffectedWaterQualityAreas.csv", dtype=str, encoding='latin1')
df_ub = df[df['State Name'].isin(['UTTAR PRADESH', 'BIHAR'])]

# Clean district names
def clean_district(d):
    d = str(d).split('(')[0].strip().lower()
    return d

df_ub['clean_district'] = df_ub['District Name'].apply(clean_district)
df_ub['clean_state'] = df_ub['State Name'].apply(lambda x: str(x).lower().title())

summary = df_ub.groupby(['clean_state', 'clean_district', 'Quality Parameter']).size().reset_index(name='affected')

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

# Clear table
cur.execute("TRUNCATE TABLE staging_l3_habitations RESTART IDENTITY")

inserted = 0
for _, row in summary.iterrows():
    cur.execute("""
        INSERT INTO staging_l3_habitations (source_name, source_url, state, district, contaminant, affected_habitations)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('CGWB Affected Areas 2009-2012', 'kaggle', row['clean_state'], row['clean_district'], row['Quality Parameter'], int(row['affected'])))
    inserted += 1

conn.commit()
print(f"Inserted {inserted} historical habitation records into staging_l3_habitations.")
