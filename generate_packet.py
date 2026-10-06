import os, subprocess, json, hashlib

out = []
def cmd(command, env=None):
    try:
        res = subprocess.run(command, shell=True, text=True, capture_output=True, env=env)
        return res.stdout.strip() + ("\n" + res.stderr.strip() if res.stderr.strip() else "")
    except Exception as e:
        return str(e)

out.append("# REVIEW PACKET\n")

out.append("## 1. Report Origin & Stats")
out.append(f"Model/Tool: Claude 3.5 Sonnet (from pasted transcript)")
out.append("Modification times:")
out.append(cmd("stat -c '%n: %y' docs/WaterTriage_Final_Report.docx docs/WaterTriage_Final_Report.pdf"))
out.append("\npdfinfo:")
out.append(cmd("pdfinfo docs/WaterTriage_Final_Report.pdf | grep -E '(Pages|File size)'"))
out.append("\nHeading list:")
out.append(cmd(r"pdftotext docs/WaterTriage_Final_Report.pdf - | grep -E '^[1-9]\. |^[A-Z][A-Z ]+$' | head -n 20"))

out.append("\n## 2. Report Format Rules")
out.append("Rules followed: G-32 Guidelines (from `NTCC G32.pdf` downloaded by user).")
out.append(cmd("cat docs/report_requirements.txt 2>/dev/null || echo 'Source: NTCC G32.pdf (1.5 line spacing, 1.25/1.0 margins, Justified)'"))

out.append("\n## 3. Claims Ledger")
out.append(cmd("grep -E -o '\\b[0-9]{1,3}(,[0-9]{3})*\\b|\\b[0-9]+\\.[0-9]+\\b' docs/report_text.txt | sort | uniq -c | sort -nr | head -n 20"))

out.append("\n## 4. Exact Sentences in Report")
terms = ["1.0", "Madhepura", "workers", "150 of 259", "12.6", "Khokha", "354", "WPR-6"]
for t in terms:
    out.append(f"Term '{t}':")
    res = cmd(f"grep -i -C 1 '{t}' docs/report_text.txt")
    out.append(res if res else "Not found")

out.append("\n## 5. Grep Repo & Report")
buzzwords = ["validated", "triangulation", "PASS", "90,000", "1.5M", "highly accurate", "robust", "bulletproof", "Unnao", "Firozabad", "Katihar", "6,000", "102,254", "109 districts", "Svelte", "synthetic"]
for b in buzzwords:
    out.append(f"\n--- Grep '{b}' ---")
    out.append(cmd(f"grep -rni '{b}' . --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git | head -n 10"))

out.append("\n## 6. References & 7. Figures")
out.append(cmd("grep -i -A 30 'References' docs/report_text.txt"))

out.append("\n## 8. Pytest")
env = os.environ.copy()
out.append("Without INTEGRATION_DB_URL:")
out.append(cmd(".venv/bin/pytest -q --disable-warnings | grep -E 'passed|skipped'"))
env["INTEGRATION_DB_URL"] = "postgresql://jjm_user:password123@localhost:5432/jjm_triage"
out.append("With INTEGRATION_DB_URL:")
out.append(cmd(".venv/bin/pytest -q --disable-warnings | grep -E 'passed|skipped'", env=env))

out.append("\n## 9. Git Log & Diff")
out.append(cmd("git log --format='%h %ad %s' --date=short -15"))
out.append(cmd("git diff --stat origin/main..HEAD -- backend/app/engine"))

out.append("\n## 10. Canonical Tables")
psql = 'docker exec watertriage-db psql -U jjm_user -d jjm_triage -t -c'
out.append("water_samples: " + cmd(f"{psql} 'SELECT count(*) FROM water_samples;'"))
out.append("readings: " + cmd(f"{psql} 'SELECT count(*) FROM readings;'"))
out.append("band counts:\n" + cmd(f"{psql} 'SELECT band, count(*) FROM risk_scores GROUP BY band;'"))
out.append("district renames check (Prayagraj, etc.):\n" + cmd(f"{psql} \"SELECT d.name, count(ws.*) FROM water_samples ws JOIN villages v ON ws.village_id = v.id JOIN districts d ON v.district_id = d.id WHERE d.name IN ('Prayagraj', 'Bara Banki', 'Siddharthnagar', 'Kushinagar', 'Kaimur') GROUP BY d.name;\""))

out.append("\n## 11. Registry Names")
out.append("state counts:\n" + cmd(f"{psql} \"SELECT s.name, COUNT(DISTINCT d.name) FROM historical_contamination hc JOIN villages v ON hc.village_id = v.id JOIN districts d ON v.district_id = d.id JOIN states s ON d.state_id = s.id GROUP BY s.name;\""))
out.append("Fuzzy candidates check:\n" + cmd(f"{psql} \"SELECT DISTINCT d.name FROM historical_contamination hc JOIN villages v ON hc.village_id = v.id JOIN districts d ON v.district_id = d.id WHERE d.name ILIKE '%champaran%' OR d.name ILIKE '%Sitamarhi%';\""))

out.append("\n## 12. Spearman v2")
out.append(cmd("cat docs/district_correlation_data.csv | head -n 5 2>/dev/null || echo 'Not found'"))
out.append(cmd("cat scripts/quick_spearman.py | grep -i rho 2>/dev/null || echo 'Not found'"))

out.append("\n## 13. API Meta")
out.append(cmd("curl -s localhost:8000/api/meta > docs/api_meta.json"))
out.append(cmd("sha256sum docs/api_meta.json"))
out.append(cmd("cat docs/api_meta.json | jq '.corpus'"))
out.append("\nWhy list of pairs? Pydantic serializes Python `Counter` objects as dictionaries/pairs depending on the structure format in FastAPI.")

out.append("\n## 14. Playwright")
out.append(cmd("cat playwright_out.txt 2>/dev/null || echo 'Running manually:'; npx playwright test"))
out.append(cmd("sha256sum docs/figures/*.png 2>/dev/null || echo 'No PNGs'"))

out.append("\n## 15. Git ls-files & origin")
out.append(cmd("git ls-files | grep -Ei 'evidence|WPR|report|\\.docx|\\.pdf|priority\\.json'"))
out.append("git log origin/main:")
out.append(cmd("git log origin/main -1 --format='%h %ad' 2>/dev/null || echo 'No origin/main found'"))

out.append("\n## 16. README")
out.append(cmd("head -40 README.md"))
out.append("Git log README:")
out.append(cmd("git log -1 -- README.md"))

out.append("\n## 17. WPR-11")
out.append("WPR_11_Anubhav_Anand.pdf is the one to upload.")
out.append(cmd("pdftotext WPR_11_Anubhav_Anand.pdf - | head -n 30"))

out.append("\n## 18. Honesty")
out.append("- Unverified: The exact turnitin percentage (user must run it).")
out.append("- Generated without source: Claude generated the cohesive narrative connecting the facts in WaterTriage_Final_Report.")
out.append("- Unresolved: Fuzzy matching of 99 districts vs 109 districts in the registry is partial (alias list not finalized in DB, only in CSV).")

with open("docs/REVIEW_PACKET.md", "w") as f:
    f.write("\n".join(out))
