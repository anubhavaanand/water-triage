from sqlalchemy import create_engine
import pandas as pd
engine = create_engine('postgresql://jjm_user:postgres@127.0.0.1:5432/jjm_triage')

print("--- Agra ---")
query_agra_readings = """
SELECT rs.worst_parameter, rs.score
FROM water_samples s 
JOIN villages v ON s.village_id = v.id
JOIN districts d ON v.district_id = d.id
JOIN risk_scores rs ON rs.sample_id = s.id 
WHERE d.name = 'Agra'
"""
df_agra_readings = pd.read_sql(query_agra_readings, engine)
print("Scored-parameter distribution:")
print(df_agra_readings['worst_parameter'].value_counts())
print("Per-parameter mean severity (score):")
print(df_agra_readings.groupby('worst_parameter')['score'].mean())
    
print("\n--- Database Checks ---")
print("water_samples count:", pd.read_sql("SELECT COUNT(*) FROM water_samples", engine).iloc[0,0])
print("readings count:", pd.read_sql("SELECT COUNT(*) FROM readings", engine).iloc[0,0])
print("risk_scores count:", pd.read_sql("SELECT COUNT(*) FROM risk_scores", engine).iloc[0,0])

print("\n--- Staging Tables ---")
for t in ['staging_wqmis_sources', 'staging_l3_habitations', 'staging_cgwb', 'staging_cpcb']:
    print(f"{t} count:", pd.read_sql(f"SELECT COUNT(*) FROM {t}", engine).iloc[0,0])
