#!/usr/bin/env python3
"""
scripts/wpr_facts.py
Queries the canonical PostgreSQL database (watertriage-db / jjm_triage)
and generates reports/facts.json and reports/facts_queries.sql.
No hand-typed numbers. Everything verified directly against the DB and git.
"""

import json
import os
import subprocess
import psycopg2
from datetime import datetime, timezone

# 1. Connect to PostgreSQL
env_path = os.path.join(os.path.dirname(__file__), "../codebase/.env")
db_url = None
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.strip().split("=", 1)[1].strip("'\"")
                break

if not db_url:
    db_url = "postgresql://jjm_user:SECRET_REDACTED@localhost:5432/jjm_triage"

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# 2. Queries definition
QUERIES = {
    "sample_count": "SELECT COUNT(*) FROM water_samples;",
    "reading_count": "SELECT COUNT(*) FROM readings;",
    "historical_event_count": "SELECT COUNT(*) FROM historical_contamination;",
    "historical_distinct_villages": "SELECT COUNT(DISTINCT village_id) FROM historical_contamination;",
    "band_counts": """
        SELECT band, COUNT(*) 
        FROM risk_scores 
        GROUP BY band 
        ORDER BY CASE band 
            WHEN 'Critical' THEN 1 
            WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 
            WHEN 'Low' THEN 4 
            ELSE 5 END;
    """,
    "state_metrics": """
        SELECT s.name AS state, COUNT(rs.id) AS samples, ROUND(AVG(rs.score)::numeric, 2) AS mean_crs
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY s.name
        ORDER BY s.name;
    """,
    "top_districts_by_mean_crs": """
        SELECT d.name AS district, s.name AS state, COUNT(rs.id) AS samples, ROUND(AVG(rs.score)::numeric, 2) AS mean_crs
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY d.name, s.name
        ORDER BY mean_crs DESC
        LIMIT 10;
    """,
    "top_parameters_by_exceedance": """
        SELECT r.parameter_key, COUNT(*) AS exceedances
        FROM readings r
        JOIN bis_parameters bp ON r.parameter_key = bp.key
        WHERE (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
           OR (bp.strategy = 'range' AND (r.value < bp.acceptable_limit OR r.value > bp.permissible_limit))
        GROUP BY r.parameter_key
        ORDER BY exceedances DESC;
    """
}

# 3. Execute queries
cur.execute(QUERIES["sample_count"])
sample_count = cur.fetchone()[0]

cur.execute(QUERIES["reading_count"])
reading_count = cur.fetchone()[0]

cur.execute(QUERIES["historical_event_count"])
historical_count = cur.fetchone()[0]

cur.execute(QUERIES["historical_distinct_villages"])
historical_distinct_villages = cur.fetchone()[0]

cur.execute(QUERIES["band_counts"])
band_counts = {row[0]: row[1] for row in cur.fetchall()}

cur.execute(QUERIES["state_metrics"])
state_metrics = {row[0]: {"samples": row[1], "mean_crs": float(row[2])} for row in cur.fetchall()}

cur.execute(QUERIES["top_districts_by_mean_crs"])
top_districts = [{"district": r[0], "state": r[1], "samples": r[2], "mean_crs": float(r[3])} for r in cur.fetchall()]

cur.execute(QUERIES["top_parameters_by_exceedance"])
top_parameters = [{"parameter": r[0], "exceedances": r[1]} for r in cur.fetchall()]

cur.close()
conn.close()

# 4. Get Git commit hash
codebase_dir = os.path.join(os.path.dirname(__file__), "../codebase")
git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=codebase_dir).decode().strip()
git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=codebase_dir).decode().strip()

# 5. Get Pytest count
test_proc = subprocess.run(
    ["bash", "-c", "source .venv/bin/activate 2>/dev/null || true; PYTHONPATH=backend .venv/bin/python -m pytest -q"],
    cwd=codebase_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
test_output = test_proc.stdout.strip()
# Expected line e.g. "23 passed, 1 skipped, 1 warning in 2.17s"
summary_line = [l for l in test_output.splitlines() if "passed" in l or "failed" in l]
test_summary = summary_line[-1] if summary_line else "unknown"

# 6. Assemble facts dictionary
facts = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "database": {
        "name": "jjm_triage",
        "host": "localhost:5432",
        "container": "watertriage-db",
        "canonical_sample_count": sample_count,
        "reading_count": reading_count,
        "historical_events_total": historical_count,
        "historical_distinct_villages": historical_distinct_villages
    },
    "severity_bands": band_counts,
    "state_metrics": state_metrics,
    "top_10_districts_by_mean_crs": top_districts,
    "top_parameters_by_exceedance": top_parameters,
    "repo": {
        "git_commit": git_hash,
        "git_branch": git_branch,
        "pytest_summary": test_summary
    }
}

os.makedirs("reports", exist_ok=True)

# 7. Write reports/facts.json
with open("reports/facts.json", "w") as f:
    json.dump(facts, f, indent=2)

# 8. Write reports/facts_queries.sql
with open("reports/facts_queries.sql", "w") as f:
    f.write("-- SQL Queries used to produce reports/facts.json\n")
    f.write(f"-- Generated on: {datetime.now(timezone.utc).isoformat()}\n\n")
    for name, q in QUERIES.items():
        f.write(f"-- [{name}]\n{q.strip()}\n\n")

print(f"Successfully generated reports/facts.json and reports/facts_queries.sql")
print(f"Samples: {sample_count}, Readings: {reading_count}, Bands: {band_counts}")
print(f"State metrics: {state_metrics}")
print(f"Git commit: {git_hash} ({git_branch})")
print(f"Tests: {test_summary}")
