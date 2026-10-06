import subprocess
import os
import json
import hashlib

def run(cmd, env=None):
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True, env=env)
    out = res.stdout.strip()
    if res.stderr.strip():
        if out:
            out += "\n" + res.stderr.strip()
        else:
            out = res.stderr.strip()
    return out

report_pdf = "docs/WaterTriage_Final_Report.pdf"
report_docx = "docs/WaterTriage_Final_Report.docx"
report_txt = "docs/report_text.txt"

# Ensure report_text.txt is generated
run(f"pdftotext {report_pdf} {report_txt}")

packet = []

packet.append("# REVIEW PACKET — Comprehensive Raw Verification")
packet.append("Generated on: 2026-10-06\n")

# ----------------------------------------------------
# 1. REPORT ORIGIN & STATS
# ----------------------------------------------------
packet.append("## 1. Report Origin, Inputs, and Statistics\n")
packet.append("- **Model / Tool:** Claude 3.5 Sonnet (via interactive chat session, transcript provided by student).")
packet.append("- **Inputs:** Conversation context, reconciled canonical figures (1,741 samples, 6,792 readings, 100,690 historical events), state comparison audit (mean/median skew in Madhepura), WPR-10/11 handoff text, and G-32 formatting requirements.")
packet.append("- **File Modification Times:**")
packet.append("```")
packet.append(run(f"stat -c '%n: %y' {report_docx} {report_pdf}"))
packet.append("```")
packet.append("\n- **pdfinfo (pages, size):**")
packet.append("```")
packet.append(run(f"pdfinfo {report_pdf}"))
packet.append("```")
packet.append("\n- **Heading List:**")
packet.append("```")
packet.append(run(f"pdftotext {report_pdf} - | grep -E '^[1-9]\\. |^[A-Z][a-zA-Z &]+$' | head -n 35"))
packet.append("```")

# ----------------------------------------------------
# 2. REPORT FORMAT RULES
# ----------------------------------------------------
packet.append("\n## 2. Report Format Rules and Source Document\n")
packet.append("- **Rules followed:** Amity University Guidelines for Non-Teaching Credit Courses (NTCC) / Supervised Independent Learning (G-32).")
packet.append("- **Source File:** `/home/anubhavanand/Downloads/NTCC G32.pdf`")
packet.append("- **Raw Guidelines Text Extraction:**")
packet.append("```")
packet.append(run("pdftotext /home/anubhavanand/Downloads/NTCC\\ G32.pdf - | grep -i -C 3 'Paper size'"))
packet.append("```")

# ----------------------------------------------------
# 3. CLAIMS LEDGER
# ----------------------------------------------------
packet.append("\n## 3. Claims Ledger\n")
packet.append("| Claim | Value in Report | Script / Query / File Source | Status |")
packet.append("| :--- | :--- | :--- | :--- |")
packet.append("| Total Scored Samples | 1,741 | `SELECT count(*) FROM water_samples;` | Verified against DB |")
packet.append("| Uttar Pradesh Samples | 966 | `SELECT count(*) FROM water_samples ws JOIN villages v ON ws.village_id=v.id JOIN districts d ON v.district_id=d.id JOIN states s ON d.state_id=s.id WHERE s.name='Uttar Pradesh';` | Verified against DB |")
packet.append("| Bihar Samples | 775 | `SELECT count(*) FROM water_samples ws JOIN villages v ON ws.village_id=v.id JOIN districts d ON v.district_id=d.id JOIN states s ON d.state_id=s.id WHERE s.name='Bihar';` | Verified against DB |")
packet.append("| Discrete BIS Readings | 6,792 | `SELECT count(*) FROM readings;` | Verified against DB |")
packet.append("| Historical Contamination Events | 100,690 | `SELECT count(*) FROM historical_contamination;` | Verified against DB |")
packet.append("| Distinct Registry Villages | 14,006 | `SELECT count(distinct village_id) FROM historical_contamination;` | Verified against DB |")
packet.append("| Critical Band Count | 89 (5.1%) | `SELECT count(*) FROM risk_scores WHERE band='Critical';` | Verified against DB |")
packet.append("| High Band Count | 392 (22.5%) | `SELECT count(*) FROM risk_scores WHERE band='High';` | Verified against DB |")
packet.append("| Medium Band Count | 28 (1.6%) | `SELECT count(*) FROM risk_scores WHERE band='Medium';` | Verified against DB |")
packet.append("| Low Band Count | 1,232 (70.8%) | `SELECT count(*) FROM risk_scores WHERE band='Low';` | Verified against DB |")
packet.append("| Bihar Mean CRS | 18.36 | `backend/app/api/meta.py` (SQL aggregation on Bihar) | Verified against DB |")
packet.append("| UP Mean CRS | 12.68 | `backend/app/api/meta.py` (SQL aggregation on UP) | Verified against DB |")
packet.append("| Bihar Median CRS | 0.00 | `backend/app/api/meta.py` (Median of Bihar scores) | Verified against DB |")
packet.append("| UP Median CRS | 4.08 | `backend/app/api/meta.py` (Median of UP scores) | Verified against DB |")
packet.append("| Madhepura Critical Samples | 70 | SQL query on Madhepura district sample scores | Verified against DB |")
packet.append("| Madhepura Share of Critical Band | 78.7% | 70 / 89 = 78.65% | Verified calculation |")
packet.append("| Bihar Critical Samples | 75 | `SELECT count(*) FROM risk_scores rs ... WHERE s.name='Bihar' AND band='Critical';` | Verified against DB |")
packet.append("| UP Critical Samples | 14 | `SELECT count(*) FROM risk_scores rs ... WHERE s.name='Uttar Pradesh' AND band='Critical';` | Verified against DB |")
packet.append("| Bihar High Samples | 158 | SQL aggregation | Verified against DB |")
packet.append("| UP High Samples | 234 | SQL aggregation | Verified against DB |")
packet.append("| Automated Pytest Tests | 28 passed, 1 skipped | `pytest -q` | Verified live |")
packet.append("| Supeseded Intermediate Sample Counts | 755, 1,245, 1,855 | Historical WPR snapshots (WPR-6, WPR-7, WPR-8) | Typed by hand in narrative |")

# ----------------------------------------------------
# 4. EXACT SENTENCE AND PAGE VERIFICATION
# ----------------------------------------------------
packet.append("\n## 4. Specific Content Checks in Final Report PDF\n")

checks = [
    ("Both iron limits (0.3 BIS vs 1.0 lab/permissible) and two-scoring table", [
        "Section 3.3 (Page 5): \"During development, iron and nitrate were initially found to have no defined permissible ceiling in the scoring model... corrected by assigning iron a BIS-aligned permissible limit of 1.0 mg/L, restoring graded linear interpolation consistent with every other parameter.\"",
        "Section 4.3 (Page 7): Mentions scoring under 1.0 mg/L. Note: The explicit side-by-side 'two-scoring table' comparing 0.3 vs 1.0 side by side is present in WPR-11 Table 2 and /api/meta sensitivity run, but is NOT formatted as a full two-scoring table in the 10-page final report text (discussed narratively instead)."
    ]),
    ("The Madhepura finding (70 single-parameter iron samples) and medians", [
        "Abstract (Page 3): \"median scores (0.00 for Bihar, 4.08 for Uttar Pradesh) reveal that Bihar's elevated mean is substantially driven by a concentrated cluster of single-parameter iron panels in Madhepura district rather than uniformly elevated risk.\"",
        "Section 4.3 (Page 7): \"70 of the 89 Critical-band samples (78.7%) originate from Madhepura district alone, where all 70 samples were tested under a single-parameter panel for iron only. Under the corrected scoring rule, any iron reading at or above the permissible limit saturates to maximum severity... the composite score for each equals 100 by construction.\""
    ]),
    ("Crawl wording: batches, up to 6 workers, no request log retained", [
        "Status: NOT IN FINAL REPORT. Section 3.5 (Page 5) states only: 'The primary acquisition channel is a crawler against WQMIS\\'s public, unauthenticated report-printing endpoint, operating with caching and resume checkpoints.' Batch size (500) and worker count (6) are not specified."
    ]),
    ("Arsenic: 0 exceedances, 150 of 259 recorded as 0, mostly a few labs", [
        "Status: NOT IN FINAL REPORT. The final report discusses arsenic escalation rules and regional hydrogeology, but does not state the '150 of 259 recorded as 0' laboratory distribution metric."
    ]),
    ("Fluoride 12.6 reading as 'Not available' district (not Agra)", [
        "Status: NOT IN FINAL REPORT. The 12.60 mg/L fluoride reading from earlier drafts (WPR-9 draft) was omitted from the final 10-page report text."
    ]),
    ("Khokha as registry-only", [
        "Section 4.5 (Page 7-8): \"The historical registry confirms Khokha village (Purnia district, Bihar) as the single most frequently recorded location for iron-related events in the 2009–2012 registry... this historical finding could not be linked to a corresponding live risk score for the same village during this reporting period, and an earlier characterisation of Khokha as a \\\"confirmed chronic contamination hotspot\\\" based on live system output has accordingly been withdrawn. The historical figure is reported here as a registry-level finding only, and the identifier-mapping gap is recorded as an open limitation (Section 6).\""
    ]),
    ("354 unassigned samples; village names for 1.21% of samples", [
        "Status: NOT IN FINAL REPORT. These specific numbers are exposed via `/api/meta` (`village_name_coverage_pct: 1.21`, `unassigned_district_samples: 354`) and documented in WPR-11, but the exact numeric percentages '354' and '1.21%' were omitted from the final report text (Section 6 discusses the limitation qualitatively)."
    ]),
    ("Revision note on WPR-6 to WPR-9 figures", [
        "Section 4.1 (Page 6): \"The canonical, frozen corpus used for all results in this section comprises 1,741 scored live laboratory reports (Uttar Pradesh: 966; Bihar: 775), 6,792 discrete parameter readings, and 100,690 historical contamination registry events. This figure supersedes several intermediate sample counts (755, 1,245, and 1,855) reported in earlier weekly progress reports during active development; those counts reflected partial crawls and an interim SQLite-to-PostgreSQL migration and are not used in this final report.\""
    ])
]

for title, entries in checks:
    packet.append(f"### {title}")
    for e in entries:
        packet.append(f"- {e}")
    packet.append("")

# ----------------------------------------------------
# 5. GREP REPO & REPORT
# ----------------------------------------------------
packet.append("\n## 5. Keyword Grep Across Codebase and Documentation\n")
packet.append("*(Excluding `node_modules`, `.venv`, `.git`, and `docs/REVIEW_PACKET.md`)*\n")

buzzwords = [
    "validated", "triangulation", "PASS", "90,000", "1.5M", 
    "highly accurate", "robust", "bulletproof", "Unnao", "Firozabad", 
    "Katihar", "6,000", "102,254", "109 districts", "Svelte", "synthetic"
]

for b in buzzwords:
    packet.append(f"### Grep: `{b}`")
    res = run(f"grep -rni '{b}' . --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git --exclude='REVIEW_PACKET.md' | head -n 12")
    packet.append("```")
    packet.append(res if res else "No matches found.")
    packet.append("```\n")

# ----------------------------------------------------
# 6. REFERENCES & IS 10500:2012
# ----------------------------------------------------
packet.append("\n## 6. References Audit\n")
packet.append("- **References List from Report:**")
packet.append("```")
packet.append(run(f"grep -i -A 25 'References' {report_txt}"))
packet.append("```")
packet.append("\n- **Verification Status of References:**")
packet.append("| # | Citation | URL / DOI | Access Date | Opened in Session? | Status |")
packet.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
packet.append("| [1] | DDWS, Jal Jeevan Mission, 2019 | jaljeevanmission.gov.in | None cited | Yes (data source) | Verified |")
packet.append("| [2] | NJJM, Water Quality Framework | jaljeevanmission.gov.in | None cited | Yes (guidelines) | Verified |")
packet.append("| [3] | Chauhan et al., Water Supply 2024 | None cited | None cited | No | [UNVERIFIED] |")
packet.append("| [4] | Chakraborti et al., Water Supply 2024 | None cited | None cited | No | [UNVERIFIED] |")
packet.append("| [5] | Mid-Gangetic Plain Bihar, ResearchGate 2024 | None cited | None cited | No | [UNVERIFIED] |")
packet.append("| [6] | Muzaffarpur Groundwater, Bull. Nat. Res. 2025 | None cited | None cited | No | [UNVERIFIED] |")
packet.append("| [7] | WQI Review, J. Geol. Soc. India 2025 | None cited | None cited | No | [UNVERIFIED] |")
packet.append("| [8] | Evaluation of WQI, JGEESI | None cited | None cited | No | [UNVERIFIED] |")
packet.append("\n- **Is IS 10500:2012 cited with its table number?**")
packet.append("  - **NO.** IS 10500:2012 is cited in the body of the paper (Sections 1, 2.4, 3.2, 3.3), but is NOT cited in the References section, and its specific table number (e.g., Table 1: Organoleptic and Physical Parameters, Table 2: General Parameters Concerning Substances Undesirable in Excessive Amounts) is NOT specified.")

# ----------------------------------------------------
# 7. FIGURES AND TABLES
# ----------------------------------------------------
packet.append("\n## 7. Figures and Tables in Final Report\n")
packet.append("- **Images / Embedded Figures:** Only 1 embedded image exists: the Amity University Logo on Page 1.")
packet.append("```")
packet.append(run(f"pdfimages -list {report_pdf}"))
packet.append("```")
packet.append("\n- **Tables in Report:**")
packet.append("- **Table 1:** Severity Band Distribution (Page 6, Section 4.2)")
packet.append("- **Table 2:** Comparative State Analysis: Mean, Median, and Panel-Size Artifact (Page 6-7, Section 4.3)")
packet.append("- **Table 3:** Corpus Invariants via `/api/meta` (Page 5, referenced Section 3.6 and Section 4.6)")
packet.append("- **Table 4:** Synopsis Objectives vs. Delivered Outcomes (Page 9, Section 7 / Conclusion)")

# ----------------------------------------------------
# 8. PYTEST RESULTS
# ----------------------------------------------------
packet.append("\n## 8. Automated Pytest Test Suite\n")
packet.append("- **Without `INTEGRATION_DB_URL`:**")
packet.append("```")
packet.append(run(".venv/bin/pytest -rs -q"))
packet.append("```")
packet.append("\n- **With `INTEGRATION_DB_URL=\"postgresql://jjm_user:postgres@localhost:5432/jjm_triage\"`:**")
env = os.environ.copy()
env["INTEGRATION_DB_URL"] = "postgresql://jjm_user:postgres@localhost:5432/jjm_triage"
packet.append("```")
packet.append(run(".venv/bin/pytest -rs -q", env=env))
packet.append("```")
packet.append("- **Skipped Test Name:** `backend/tests/test_recurrence_service.py::test_postgres_recurrence_integration` (skipped when live database credentials are not provided in environment).")

# ----------------------------------------------------
# 9. GIT LOG & DIFF (Changes since 04/10)
# ----------------------------------------------------
packet.append("\n## 9. Git Log and Scoring/Data Changes\n")
packet.append("- **Git Log (-15):**")
packet.append("```")
packet.append(run("git log --format='%h %ad %s' --date=short -15"))
packet.append("```")
packet.append("\n- **Note on Commit `8c58108`:** Commit `8c58108` does not exist in this repo branch. The diff below shows all changes to `backend/app/engine` and `data` since October 4 (from `1452c2f` to `HEAD`):")
packet.append("```")
packet.append(run("git diff --stat 1452c2f..HEAD -- backend/app/engine data"))
packet.append("```")
packet.append("\n- **Exact scoring code delta:**")
packet.append("```")
packet.append(run("git diff 1452c2f..HEAD -- backend/app/engine/scoring.py"))
packet.append("```")

# ----------------------------------------------------
# 10. CANONICAL DATABASE TABLES
# ----------------------------------------------------
packet.append("\n## 10. Canonical PostgreSQL Database Counts and District Renames\n")
packet.append("```")
packet.append(run("""docker exec watertriage-db psql -U jjm_user -d jjm_triage -c "
SELECT 'water_samples' AS table_name, count(*) FROM water_samples
UNION ALL
SELECT 'readings', count(*) FROM readings
UNION ALL
SELECT 'risk_scores', count(*) FROM risk_scores;

SELECT band, count(*) FROM risk_scores GROUP BY band ORDER BY count(*) DESC;

SELECT s.name AS state, count(ws.id) AS samples
FROM water_samples ws
JOIN villages v ON ws.village_id = v.id
JOIN districts d ON v.district_id = d.id
JOIN states s ON d.state_id = s.id
GROUP BY s.name;

SELECT 
    CASE WHEN d.name ILIKE '%not available%' OR d.name = '' OR d.name IS NULL THEN 'Not available' ELSE 'Named' END AS district_type,
    count(DISTINCT d.name) AS distinct_districts,
    count(ws.id) AS sample_count
FROM water_samples ws
JOIN villages v ON ws.village_id = v.id
JOIN districts d ON v.district_id = d.id
GROUP BY 1;
" """))
packet.append("```")
packet.append("\n- **District Renames and Duplicate Check in Database:**")
packet.append("```")
packet.append(run("""docker exec watertriage-db psql -U jjm_user -d jjm_triage -c "
SELECT d.id, d.name, s.name as state, count(v.id) as village_count, count(ws.id) as sample_count
FROM districts d
JOIN states s ON d.state_id = s.id
LEFT JOIN villages v ON v.district_id = d.id
LEFT JOIN water_samples ws ON ws.village_id = v.id
WHERE d.name ILIKE '%prayagraj%' OR d.name ILIKE '%allahabad%'
   OR d.name ILIKE '%bara banki%' OR d.name ILIKE '%barabanki%'
   OR d.name ILIKE '%siddharth%'
   OR d.name ILIKE '%kushinagar%'
   OR d.name ILIKE '%kaimur%'
GROUP BY d.id, d.name, s.name;
" """))
packet.append("```")
packet.append("- **Are the renames still in the DB?** YES. Separate rows exist with samples mapped to newer title-case spellings (`Prayagraj` with 5 samples, `Bara Banki` with 48 samples, `Kushinagar` with 11 samples, `Siddharthnagar` with 2 samples), while uppercase legacy rows (`ALLAHABAD`, `BARABANKI`, `SIDDHARTH NAGAR`) remain with 0 samples.")

# ----------------------------------------------------
# 11. REGISTRY NAMES & FUZZY CANDIDATES
# ----------------------------------------------------
packet.append("\n## 11. Historical Registry Distinct Districts and Missing District Audit\n")
packet.append("```")
packet.append(run("""docker exec watertriage-db psql -U jjm_user -d jjm_triage -c "
SELECT s.name as state, count(DISTINCT d.name) as distinct_districts
FROM historical_contamination hc
JOIN villages v ON hc.village_id = v.id
JOIN districts d ON v.district_id = d.id
JOIN states s ON d.state_id = s.id
GROUP BY s.name;
" """))
packet.append("```")
packet.append("- **Counts:** Bihar = 28 distinct districts; Uttar Pradesh = 65 distinct districts in historical contamination registry.")
packet.append("- **Fuzzy Check for Requested Districts:**")
packet.append("  - Pilibhit, Shahjahanpur, Sitapur, Budaun, Amethi (UP): **0 occurrences** in IMIS 2009–2012 registry.")
packet.append("  - Sitamarhi, Arwal, Jehanabad, Pashchim Champaran, Purbi Champaran (Bihar): **0 occurrences** in IMIS 2009–2012 registry.")
packet.append("  - *Reason:* The IMIS Quality-Affected Habitations registry only reports habitations with detected chemical exceedances. These districts had zero reported affected habitations during the 2009–2012 reporting window.")

# ----------------------------------------------------
# 12. SPEARMAN CORRELATION v2
# ----------------------------------------------------
packet.append("\n## 12. Spearman Correlation v2 Status\n")
packet.append("- **Status:** `not done` / `unknown` (no script or CSV exists on disk).")
packet.append("- Neither `district_correlation_data.csv` nor `quick_spearman.py` is present in the git repository or workspace filesystem.")
packet.append("- The master validation tables (`data/validation_reports/Master_Validation_Bihar.csv` and `Master_Validation_Uttar Pradesh.csv`) exist, but cross-source rank correlation metrics (rho, p, Bonferroni threshold) were not executed as an automated script in the repository.")

# ----------------------------------------------------
# 13. RAW /api/meta AND EXPLANATION OF READINGS PAIRS
# ----------------------------------------------------
packet.append("\n## 13. Live `/api/meta` Response and Readings Key Diagnostic\n")
run("curl -s http://localhost:8000/api/meta > docs/api_meta.json")
packet.append("- **SHA256 of `docs/api_meta.json`:**")
packet.append("```")
packet.append(run("sha256sum docs/api_meta.json"))
packet.append("```")
packet.append("\n- **jq '.corpus' Output:**")
packet.append("```json")
packet.append(run("cat docs/api_meta.json | jq '.corpus'"))
packet.append("```")
packet.append("\n- **Root Cause Analysis: Why `corpus.readings` was a list of pairs:**")
packet.append("In `backend/app/api/meta.py`, line 29 originally defines the total reading count:")
packet.append("```python")
packet.append("readings = db.execute(text(\"SELECT COUNT(*) FROM readings\")).scalar()  # integer: 6792")
packet.append("```")
packet.append("However, in the subsequent sensitivity analysis block on line 238, the loop variable reused the name `readings`:")
packet.append("```python")
packet.append("for sid, readings in samples_dict.items():")
packet.append("```")
packet.append("In Python, loop variables leak into function scope. When the loop terminated, `readings` retained the value of the final iteration: a list of `(parameter_key, value)` pairs for the last sample (`[('fluoride', 0.186), ('iron', 0.198), ...']`). On line 296, `\"readings\": readings` serialized this shadowed list rather than the scalar count 6,792. This is an unedited, live Python variable shadowing defect.")

# ----------------------------------------------------
# 14. PLAYWRIGHT E2E RUN AND SCREENSHOTS
# ----------------------------------------------------
packet.append("\n## 14. Playwright E2E Run Output and Screenshots\n")
packet.append("- **Backend URL Used:** `http://localhost:8000`")
packet.append("- **Frontend Base URL:** `http://localhost:4173` (via Vite preview server)")
packet.append("- **Raw Playwright Test Execution:**")
packet.append("```")
packet.append(run("npx playwright test"))
packet.append("```")
packet.append("\n- **Screenshots SHA256 (`docs/figures/`):**")
packet.append("```")
packet.append(run("sha256sum docs/figures/*.png"))
packet.append("```")

# ----------------------------------------------------
# 15. GIT TRACKED FILES & ORIGIN PUSH STATUS
# ----------------------------------------------------
packet.append("\n## 15. Tracked Reports and Origin Push Audit\n")
packet.append("- **git ls-files matching reports / deliverables:**")
packet.append("```")
packet.append(run("git ls-files | grep -Ei 'evidence|WPR|report|\\.docx|\\.pdf|priority\\.json'"))
packet.append("```")
packet.append("\n- **git log origin/main -1:**")
packet.append("```")
packet.append(run("git log origin/main -1 --format='%h %ad %s'"))
packet.append("```")
packet.append("\n- **Has the final report or any WPR file been pushed to origin?**")
packet.append("  - **NO.** No `.pdf` or `.docx` file has ever been added to git tracking or pushed to remote `origin/main`.")

# ----------------------------------------------------
# 16. README STATE
# ----------------------------------------------------
packet.append("\n## 16. Current README.md Inspection\n")
packet.append("- **head -40 README.md:**")
packet.append("```markdown")
packet.append(run("head -40 README.md"))
packet.append("```")
packet.append("\n- **git log -1 -- README.md:**")
packet.append("```")
packet.append(run("git log -1 -- README.md"))
packet.append("```")

# ----------------------------------------------------
# 17. WPR-11 AUDIT & COMPARISON
# ----------------------------------------------------
packet.append("\n## 17. WPR-11 Verification and pdftotext Comparison\n")
packet.append("- **File to upload:** `/home/anubhavanand/Desktop/WaterTriage_Deliverables_05-10-2026/WPR_11_Anubhav_Anand.pdf` (or `reports/submitted_pdfs/WPR_11_Anubhav_Anand.pdf`).")
packet.append("- **Page count:** 2 pages.")
packet.append("- **Raw pdftotext of WPR-11 PDF:**")
packet.append("```")
packet.append(run("pdftotext /home/anubhavanand/Desktop/WaterTriage_Deliverables_05-10-2026/WPR_11_Anubhav_Anand.pdf -"))
packet.append("```")
packet.append("\n- **Does Achievement 4 match 'first React dashboard prototype'?**")
packet.append("  - **NO.** In the PDF, Achievement 4 literally states: `• Rebuilt the dashboard as a React application reading /api/priority and /api/meta.` The revised softer phrasing (`first React dashboard prototype`) was proposed in review notes but never compiled into this uploaded PDF.")

# ----------------------------------------------------
# 18. HONESTY & UNRESOLVED ITEMS
# ----------------------------------------------------
packet.append("\n## 18. Complete Honesty Disclosure and Unresolved Items\n")
packet.append("1. **Institutional Plagiarism Scan:** Has NOT been run through Turnitin/iThenticate. Must be executed by student via Amizone before final university submission.")
packet.append("2. **Academic References [3]–[8]:** Generated from Claude training data; original PDFs have not been verified locally or checked against DOIs.")
packet.append("3. **Missing IS 10500:2012 Reference:** Cited extensively throughout report narrative, but omitted from the formal References section and does not cite specific IS 10500 table numbers.")
packet.append("4. **Variable Shadowing in `/api/meta`:** `corpus.readings` returns the last sample's parameter list instead of the integer 6,792 due to a Python loop variable leak (`readings`).")
packet.append("5. **Playwright E2E Suite Failure:** 4 of 4 tests currently fail because the test locators expect earlier wireframe HTML IDs rather than the refactored React DOM components.")
packet.append("6. **District Name Duplication in PostgreSQL:** 12 duplicate district rows (e.g., `Prayagraj` vs `ALLAHABAD`, `Bara Banki` vs `BARABANKI`) remain unmerged in the database.")
packet.append("7. **Village Recurrence Resolution:** Only 21 of 1,741 samples carry real village names (1.21%). Recurrence matching between live WQMIS and historical IMIS at the village level remains impossible and unresolved.")

with open("docs/REVIEW_PACKET.md", "w") as f:
    f.write("\n".join(packet))

print("REVIEW_PACKET.md generated successfully.")
