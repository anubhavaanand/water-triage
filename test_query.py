from backend.app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
query = """
    SELECT d.name as district, COUNT(ws.id) as total_critical,
           SUM(CASE WHEN 
                 (SELECT COUNT(*) FROM readings WHERE sample_id = ws.id) = 1 
                 AND 
                 (SELECT parameter_key FROM readings WHERE sample_id = ws.id LIMIT 1) = 'iron'
               THEN 1 ELSE 0 END) as single_param_iron_critical
    FROM risk_scores rs
    JOIN water_samples ws ON rs.sample_id = ws.id
    JOIN villages v ON ws.village_id = v.id
    JOIN districts d ON v.district_id = d.id
    WHERE rs.score >= 75
    GROUP BY d.name
    ORDER BY total_critical DESC
    LIMIT 1;
"""
res = db.execute(text(query)).fetchone()
print(dict(res._mapping))
