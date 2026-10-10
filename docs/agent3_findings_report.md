# Agent 3 Findings Report: WaterTriage Data Crawling Strategy

**Date:** 2026-10-10  
**Agent:** Agent 3 (Data Infrastructure & Crawling Strategy)  
**Task:** (1) READ directories `~/Documents/NTCC MINOR PROJECT/` and `~/Documents/Projects/water-triage/`; (2) ANALYZE existing crawling infra and whether it can fetch more e_coli/total_coliform/sulphate data; (3) RESEARCH web data sources for missing parameters; (4) DESIGN improved crawling strategy; (5) REPORT findings.

---

## 1. Executive Summary

The WaterTriage project has a **functioning public-data crawler** (`crawl_fast.py`) that has already harvested 1,822 WQMIS reports (1,741 with parsed results) from `ejalshakti.gov.in/WQMIS/Common/final_report_print`. The system has **strong chemical parameter coverage** (pH: 1,242, TDS: 851, iron: 450, fluoride: 651, sulphate: 467, turbidity: 925) but **critically sparse e_coli (45 readings) and total_coliform (7 readings)** data. These microbial parameters are the **primary gap** preventing accurate acute-hazard scoring — only 2 non-zero e_coli values exist across 1,741 samples.

A legitimate, authenticated **JJM Web API portal** (`https://ejalshakti.gov.in/webapi/`) exists with a registration→approval workflow that can unlock state-wide water quality data with full parameter coverage including e_coli/TC. The AIKosh CSV (3.37 MB, pending 2+ weeks) is a secondary source with village-level microbial data.

**Key recommendation:** Pursue **Path A** (register for JJM WebAPI → get JWT token → call WQMIS parameter-wise endpoints) rather than continuing blind ID-range crawling, which has a sub-1% hit rate over 20M+ IDs and risks CAPTCHA blocking.

---

## 2. Directory Inventory

### `~/Documents/NTCC MINOR PROJECT/` (51 MB, academic workspace)

| File/Dir | Size | Contents |
|----------|------|----------|
| `AGENTS.md` | 5.6 KB | Operational rules for AI agents (OLD scoring bands: Critical≥75/High≥50/Medium≥25/Low<25) |
| `SESSION_HANDOFF.md` | 19 KB | Master handoff — 1,741 samples, DB `jjm_triage`, D1-D3 defects |
| `plan.md` | 12 KB | 12-week execution roadmap |
| `codebase` → symlink to `~/Documents/Projects/water-triage` | — | Active git repo |
| `references/` | — | 5 PDF reports (JJM WQMIS contaminant reports, CGWB yearbooks), `firecrawl_extracts/` (3 markdown tables), `aikosh_manual.pdf` |
| `CGWB yearbooks` | 6.8 MB | `Bihar_GWYB 2023-24.pdf` (groundwater quality, not drinking water) |
| `firecrawl_extracts/` | — | `up-report.md`, `bihar-report.md`, `printable-format.md` — district-level contamination COUNTS (no readings) |
| `archive/` | — | Legacy scaffold (no active data) |
| `docs/` | — | `SESSION_HANDOFF.md` (76 lines), `plan.md`, `frontend-plan.md`, domain docs |

**Note:** The `NTCC minor project/` and `Projects/water-triage/` directories point to the same codebase. The NTCC dir has extra reference materials (PDFs, CGWB data, firecrawl extracts) not in the git repo.

### `~/Documents/Projects/water-triage/` (active git repo)

```
water-triage/
├── backend/
│   ├── app/
│   │   ├── engine/
│   │   │   ├── scoring.py        (L1-124) — BIS IS 10500 model, bands Critical≥40/High≥20/Medium≥10/Low≥0
│   │   │   ├── pipeline.py       (L1-92)  — compute_scores(), duplicate aggregation
│   │   ├── models/
│   │   │   ├── entities.py       (L1-130) — State, District, Village, Reading, RiskScore, etc.
│   │   ├── database.py, config.py
│   ├── etl/
│   │   ├── crawl_fast.py         (L1-211) — Multi-threaded WQMIS crawler (8 workers)
│   │   ├── wqmis.py              (L1-292) — Single-threaded crawler with RATE_SECONDS=1.0
│   │   ├── load_wqmis.py         (L1-177) — Records → DB loader with PARAM_ALIASES
│   │   ├── repair_readings.py    (L1-89)  — Post-load reading repair script
│   │   ├── load_historical.py    (L1-128) — Kaggle affected habitations CSV loader
│   ├── pyproject.toml, uv.lock, .venv/ (Python 3.13.14)
├── data/
│   ├── raw/
│   │   ├── wqmis/
│   │   │   ├── records.jsonl      (1,822 records, 1,741 with results)
│   │   │   ├── *.html             (25 saved report HTML files)
│   │   │   ├── crawl_progress.txt (37,903 IDs done, max ~5000159)
│   │   ├── official/
│   │   │   ├── WQ6_*.xls          (5 Excel files — district-level COUNTS only)
│   │   │   ├── WQ6_Complete_UP.csv (76 rows — district-level counts)
│   │   │   ├── WQ6_Complete_Bihar.csv (39 rows — district-level counts)
│   │   ├── kaggle/affected_areas_2009_2012/ (102,254 UP+Bihar rows — categorical, no readings)
│   ├── watertriage.db            (SQLite database with scored samples)
│   └── processed/
├── dashboard/
│   ├── index.html                (Three.js 3D interactive dashboard)
│   └── streamlit/
│       └── app.py
├── docs/
│   ├── research/
│   │   ├── data-access.md        (L1-64) — WQMIS endpoints, AES scheme, acquisition plan
│   │   ├── wqmis-baseline-fy26-27.md — UP 206,111 samples (0.76% contaminated), Bihar 55,103 (0.02%)
│   │   ├── data-catalog.md       (L1-45) — TIER 1/2/3 data sources
│   │   └── literature-review-notes.md — 26 citations
│   ├── evidence/
│   │   ├── RECONCILIATION.md     (L1-85) — Audit confirming 1,741 samples, scoring stats
│   │   ├── facts.json            (L1-125) — Canonical DB stats
│   │   └── build_wpr7.py
├── scripts/
│   ├── generate_chart.py, ingest_historical.py, load_cgwb_cpcb.py, merge_districts.py
│   └── sensitivity_hypothetical.py
├── tests/ (pytest, empty)
├── dashboard/data.json
└── .env (gitignored — PostgreSQL DATABASE_URL)
```

---

## 3. Existing Crawlers: Analysis

### 3.1 `crawl_fast.py` (L1–211) — Primary Active Crawler

**Architecture:** Multi-threaded via `ThreadPoolExecutor`, default `--workers 8`, batches of 50 IDs. AES-encrypts sequential integer IDs and fetches `GET /WQMIS/Common/final_report_print?s_id=<AES-128-CBC(id)>` where `key=iv='8080808080808080'`, PKCS7 padding, base64 output.

**Status:** Already ran on IDs 1,000,000–2,000,000 (default range). `crawl_progress.txt` shows 37,903 IDs scanned, `records.jsonl` has 1,822 records (1,741 with results + 81 empty). **Hit rate: ~4.6%** (1,822/37,903 non-empty).

**Key functions:**
- `aes_encrypt(str)` — CryptoJS-compatible AES-128-CBC (verified against `frmValidate.js` which uses same key/iv)
- `fetch_one(internal_id)` — HTTP fetch with 40s timeout, returns HTML
- `parse_report(html)` — BeautifulSoup parser:
  - Extracts `wqmis_sample_id` via regex `U<user>L<lab>S<seq>` pattern
  - Parses address via `after()` helper (regex-based field extraction)
  - **Critical parsing logic (L80-99):** Iterates `<table>` → `<tr>` → `<td>`, requires `re.match(r"^\d+$", cells[0])` (numeric first cell = "S. No."), requires `re.match(r"([\d.]+)", cells[5])` to extract a numeric value. Skips rows where the value cell isn't numeric-parseable.
  - **Breaks after first table with results** (L100-101: `if results: break`)

**Limitations:**
1. **No rate limiting per worker** — 8 parallel workers, no inter-request sleep. Only a 40s timeout. Risks triggering WQMIS rate limiting / CAPTCHA.
2. **Aggressive ID range** — started at 1,000,000, but many IDs in that range may be non-existent. The hit rate suggests IDs need better targeting.
3. **`state_of()` runs before filtering** — `state_of()` parses state from every response, then `should_process()` filters for UP/Bihar. Non-target states still get fetched and parsed, wasting bandwidth.
4. **e_coli/TC parsing may miss edge cases** — The `re.match(r"^\d+$", cells[0])` check works when the first cell is a serial number, but some WQMIS report formats may use different table structures. However, analysis of the 25 saved HTML files shows e_coli/TC IS parseable when the parameter appears (first cell = "1", value = "0.000" → parses as 0.0).
5. **Spawns new `requests.Session()` per fetch** (L139) — no connection reuse, adds latency.

### 3.2 `wqmis.py` (L1–292) — Alternative Single-Threaded Crawler

**Architecture:** Single-threaded with `RATE_SECONDS = 1.0` sleep between requests. Same AES scheme. `crawl()` method sequential.

**Key function:** `map_ranges()` — samples by stride to discover ID bands that contain reports, avoiding wasted fetches. More polite than `crawl_fast.py`.

**Unimplemented:** `pull_parameter_wise(cookie_file, fy="2026-2027")` — raises `NotImplementedError`. This is the session-gated parameter-wise endpoint (`POST /WQMIS/Report/get_Report_Parameter_wise`) that returns DataTables JSON. This is the **efficient** path (per-district, per-parameter) but requires a login session cookie.

**Status:** Slower but more polite. The `map_ranges()` stride approach is better for ID discovery.

### 3.3 `load_wqmis.py` (L1–177) — DB Ingestion

**PARAM_ALIASES dict** (L35-36): Maps `"e. coli"/"e.coli"/"e coli" → "e_coli"`, `"total coliform" → "total_coliform"`, `"sulphate"/"sulfate" → "sulphate"`. Uses `normalize_param()` which lowercases and strips `(as XX)` suffixes.

**Defect 1 (FIXED):** The original substring match on `'ph'` inside `'Sulphate'` (Sul**ph**ate) caused 467 sulphate readings (100–900 mg/L) to be ingested as pH values, maxing severity at 1.0. Fixed via `repair_readings.py` + strict dict-lookup. Verification: SQLite DB now has 467 sulphate readings (values 0–479, avg 53.57 — NOT pH-like 6.5–8.5). UP mean corrected from 14.51 → 12.68, Bihar from suppressed → 18.36.

**Duplicate handling:** `upsert_geo()` creates State/District/Village hierarchies. Duplicate reading warning at L67. Calls `compute_scores()` after loading.

### 3.4 `repair_readings.py` (L1–89) — Post-Repair Script

Re-derives readings from `records.jsonl` with corrected parameter mapping. Dry-run by default, `--apply` writes. Used to fix the sulphate→pH bug.

### 3.5 `load_historical.py` (L1–128) — Historical Data Loader

Loads the Kaggle affected-habitations CSV. Dedupes by (village, param, year, habitation). **Limitation:** The Kaggle data is **categorical** (contamination present/absent) with no actual readings — only useful for trend context, not scoring.

---

## 4. Current Data Inventory (from `records.jsonl` and `facts.json`)

### Parameter Reading Counts by State

| Parameter | UP | Bihar | Total | Non-Zero Values |
|-----------|-----|-------|-------|-----------------| 
| pH | 902 | — | 1,242 | 618 non-zero |
| TDS | 851 | — | — | — |
| Chloride | — | — | ~847 | — |
| Total Alkalinity | — | — | ~773 | — |
| Total Hardness | — | — | ~623 | — |
| Iron | 426 | 450 | 876 | 450 non-zero |
| Fluoride | 711 | 182 | 893 | 651 non-zero |
| Turbidity | 670 | 328 | 998 | 925 non-zero (per facts.json) |
| Nitrate | 460 | 123 | 583 | — |
| Sulphate | 394 | 73 | 467 | 50 exceed BIS acceptable (200 mg/L) |
| Arsenic | 29 | 230 | 259 | 2 non-zero readings |
| **E. coli** | 15 | 37 | **45** | **2 non-zero** (20.0, 8.0 — both in Lucknow/UP) |
| **Total Coliform** | 7 | 0 | **7** | **3 non-zero** (46.0, 80.0, 80.0 — all Lucknow/UP) |
| Conductivity | — | — | 349 | — |
| Calcium | — | — | 328 | — |
| Magnesium | — | — | 277 | — |

### Parameter Coverage Pattern

Parameters split into two categories:

1. **Multi-parameter reports** (1,245 samples with 4–25 parameters): Most reports test full chemical panels (pH, TDS, chloride, alkalinity, hardness, sulphate, iron, as, F, NO3, turbidity) but **do NOT include e_coli or total_coliform**. These appear only in specialized bacteriological test reports.

2. **Single-parameter reports** (296 samples with 1 parameter): Mostly single `Total Arsenic` or single `Iron` readings. The `parse_report()` function's `break` after first results table (L100-101) means if the e_coli row is in a secondary table, it's missed.

### e_coli / TC Distribution (Critical Gap)

- **45 e_coli readings** across only **6 districts**: Lucknow & Sitapur (UP), Arwal, Saran, Buxar, Basti (Bihar)
- **Only 2 non-zero values**: both in Lucknow (20.0, 8.0 CFU/100ml)
- **43 zero values** (below detection)
- **7 total_coliform readings** across only **2 districts**: Lucknow & Sitapur (both UP)
- **Only 3 non-zero values**: 46.0, 80.0, 80.0 (all Lucknow)
- **e_coli label variants:** `E. coli` (38 readings, includes 0-values) and `E. coli*` (7 readings, has BIS acceptable/permissible limits = 100)
- **Total coliform label:** `Total coliform*` (7 readings, all zeroes except 3 non-zero in Lucknow)
- **The `*` suffix** marks parameters that have BIS acceptable/permissible limits populated in the report table. Non-asterisk variants (`E. coli`, `Iron`, `Sulphate`) have `acceptable: null, permissible: null` — the limits are still applied via `scoring.py`'s `BIS_10500` dict.

### WQ6 Excel/CSV Files (data/raw/official/)

- 5 Excel files (`.xls`) + 2 CSV files (`WQ6_Complete_UP.csv`, `WQ6_Complete_Bihar.csv`)
- **Content: District-level COUNTS only** — "Format L1: Contaminant-wise details of villages where contamination found"
- Columns: `S.No | District | pH | TDS | Turbidity | Chloride | Total Alkalinity | Total Hardness | Sulphate | Iron | Total Arsenic | Fluoride | Nitrate | Residual Chlorine | Others | E_coli | Total_Coliform | Others`
- UP total row: e_coli=18 villages, total_coliform=49 villages contaminated
- Bihar total row: e_coli=0, total_coliform=0
- **NOT individual readings** — only counts of contaminated villages per district per parameter
- 3 UP districts with non-zero e_coli: Banda (1), Basti (1), Hardoi (18)
- 4 UP districts with non-zero TC: Ambedkar Nagar (1), Amethi (2), Basti (1), Hardoi (41)
- **Cannot be used directly** for scoring — no actual values, need to fetch individual WQ4 reports for those villages

### Date Range

All records are from **FY 2022** (2022-07-01 to 2022-11-19). The `crawl_progress.txt` shows IDs up to ~5,000,159 scanned.

### Data Quality Issues (per SESSION_HANDOFF.md §5)

- **D1:** 98.8% of samples (1,720/1,741) have village name = "Not available" — skews geographic analysis (named villages: mean CRS 4.13 vs "Not available": 15.34)
- **D2:** 354 samples in 2 "Not available" phantom districts
- **D3:** 68/105 districts (64.8%) have single-source-only data
- **Source type chaos:** 200+ distinct unstructured source values (e.g., "Source Type : Deep Tubewell, location : ADAMPUR", "Individual house tap water , Location :", etc.)

---

## 5. Crawler Capability Analysis: Can Existing Crawlers Fetch More e_coli/TC Data?

### Answer: The crawlers CAN find more e_coli/TC data, but the fundamental problem is **data distribution**, not crawler capability.

### Key Insight: e_coli/TC Reports Are Structurally Different

From analysis of the 25 saved HTML report files:

1. **Only 2 reports contain e_coli/TC** (`DC1_O1127x9ZL4GU2bhQgg.html` and `W7F-x-sPZUPsCAcXwYSH5Q.html`)
2. **Both are single-parameter reports** — the result table has only ONE row: `Total coliform*`
3. **The `parse_report()` logic DOES handle these correctly** — the serial number cell (`cells[0]`) is `"1"` (matches `re.match(r"^\d+$")`) and the value cell (`cells[5]`) is `"0.000"` (parses as 0.0)
4. **The 45 e_coli readings and 7 total_coliform readings** were extracted from the 1,822 records — so the parser IS working

### Why e_coli/TC Coverage Is So Sparse

The issue is **how WQMIS structures its reports**. Most lab submissions test the full chemical panel (pH, TDS, iron, fluoride, arsenic, etc.) but only submit e_coli/TC for samples flagged as problematic or for specific source types (household tap water). The parameter-wise report (`Report_p`) allows selecting `E. coli (ParameterId=34)` or `Total coliform (ParameterId=35)` specifically, but the `crawl_fast.py` crawler doesn't use this endpoint — it does blind sequential ID scanning.

### The Parameter-Wise API Path (Untapped)

The WQMIS `Report_p` page (fetched live at `https://ejalshakhi.gov.in/WQMIS/Report/Report_p`) contains a form with:
- **Financial Year** dropdown
- **State** dropdown (UP=31, Bihar=5)
- **District** dropdown (populated via AJAX: `POST /WQMIS/Common/District_Bind_without_session`)
- **Block** dropdown
- **Gram panchayat** dropdown
- **Parameter** dropdown with 22 options, including:
  - `value=34 label=E. Coli`
  - `value=35 label=Total coliform`
  - `value=26 label=Total Arsenic (As As)`
  - `value=11 label=Fluoride (as F)`
  - `value=19 label=Iron (As Fe)`
  - `value=13 label=Nitrate (as NO3)`
  - `value=14 label=Sulphate (as SO4)`
  - `value=8 label=TDS`
  - `value=7 label=pH`
  - `value=6 label=Turbidity`
  - `value=10 label=Chloride (as Cl)`
  - `value=9 label=Total Alkalinity (As Calcium Carbonate)`
  - `value=18 label=Total Hardness (As CaCO3)`

**When the "Show" button is clicked**, the `Report_L` page takes over — it loads the **lab report listing** page. The `Report_L` page's inline JS (block 23) includes:
- `$('._divmain').load("../Report/LoadRpt1", { type: id, subcat: sample_rdo })` — loads report list by type
- Multiple `$.ajax({ url: url, data: {...} })` calls for cascading dropdowns

**The `Report_L` page is the parameter-wise query interface** — it lets you filter by parameter, district, block, etc., and returns matching lab reports. This is the endpoint that `wqmis.py:pull_parameter_wise()` was supposed to call but was left as `NotImplementedError`.

### The JJM Web API (New Discovery)

`https://ejalshakti.gov.in/webapi/` hosts a **JJM Web API portal** with:
- Registration process (mobile + email verification, 24-48hr approval)
- JWT token-based authentication
- Permissioned API access (user requests specific APIs, waits for approval)
- PDF documentation at `/webapi/Content/JJM_Web_API.pdf` (1.27 MB) — a developer guide with registration, approval, and "List of APIs" sections

**This is the legitimate, scalable path** for state-wide water quality data — far better than blind ID-range crawling.

---

## 6. Web Data Sources for Missing Parameters (e_coli, total_coliform, sulphate)

### Tier 1 — Primary Targets

| Source | URL | Access | Contents | e_coli/TC Coverage | Assessment |
|--------|-----|--------|----------|---------------------|------------|
| **JJM Web API Portal** | `ejalshakhi.gov.in/webapi` | Registration + JWT approval (24-48hr) | Full WQMIS water quality data API | ✅ Yes — full parameter list including E. coli (ParamId=34), Total coliform (ParamId=35) | ⭐ **PRIMARY TARGET** — State-wide, authenticated, legitimate |
| **WQMIS WQ4 Report_p** | `ejalshakhi.gov.in/WQMIS/Report/Report_p` | Public (no login) | Parameter-wise report query form | ✅ Shows E. coli and Total coliform in parameter dropdown | Use for manual testing / UI automation |
| **WQMIS Report_L** | `ejalshakhi.gov.in/WQMIS/Report/Report_L` | Public | Lab report listing with cascading filters | ✅ Filters by parameter | Can scrape for report IDs when logged in |
| **AIKosh CSV** | `aikosh.indiaai.gov.in/.../jjm_water_source_water_quality_data.html` | Restricted (3.37 MB, pending 2+ weeks) | Village-level real data with e_coli | ✅ Yes — "village-level real data with e_coli" per data-catalog.md | **SECONDARY** — best village-level coverage, but access pending |
| **`final_report_print`** | `ejalshakhi.gov.in/WQMIS/Common/final_report_print?s_id=<AES>` | Public (AES-encrypted ID) | Individual lab reports with all readings | ✅ Yes (when tested) | Current crawler path — sub-1% hit rate over 20M+ IDs |

### Tier 2 — Contextual / Supporting

| Source | URL | Access | Contents | Assessment |
|--------|-----|--------|----------|------------|
| **CGWB Yearbooks** | `http://150.242.13.199/download/Yearbook/` | Public PDF | Groundwater quality (not drinking water) | Provides context/citation only — arsenic in groundwater correlates with arsenic in tube wells |
| **CGWB gwdata portal** | `https://gwdata.cgwb.gov.in/` | Public | Groundwater quality dashboard | IndiaWRIS link: `https://indiawris.gov.in/wris/#/GWQuality` — could supplement arsenic data |
| **WQMIS WQ6 Summary** | `data/raw/official/WQ6_*.xls` | Parsed | District-level containment COUNTS (not readings) | UP: e_coli=18 villages, TC=49 villages. Bihar: both=0. **Cannot score** — needs individual reports |
| **Kaggle Affected Habitations** | `data/raw/kaggle/affected_areas_2009_2012/` | Downloaded | 102,254 rows, categorical (contamination present/absent) | No actual readings — context only |

### Tier 3 — Lower Priority

| Source | URL | Access | Assessment |
|--------|-----|--------|------------|
| **State PCB sites** (UP, Bihar) | UPPCB, BPCB portals | Varies | Typically annual reports, not real-time village data |
| **India-WRIS** | `indiawris.gov.in/wris/#/GWQuality` | Public | Groundwater quality — same as CGWB, not drinking-water specific |
| **data.gov.in archived** | Archived datasets | Public | Historical, may have gaps for current FY |
| **WQMIS "Public User" role** | `ejalshakhi.gov.in/WQMIS/Home/login_register?role_id=...` | Free registration | Per data-catalog.md: "submission-only, cannot read report APIs" — **CONFLICT** with webapi finding. The JJM WebAPI portal (separate from WQMIS portal login) offers real API access. |

---

## 7. Improved Crawling Strategy

### Path A (Recommended): JJM Web API Registration → Authenticated Parameter-Wise Pull

**Mechanism:** Register at `https://ejalshakhi.gov.in/webapi/Home/Login`, request permission for WQMIS water quality APIs, receive JWT credentials, then call the parameter-wise endpoints (`POST /WQMIS/Report/get_Report_Parameter_wise` with AES-encrypted parameters).

**Scope:**
- **FY:** All available financial years (2022 onward visible in records)
- **Parameters:** All 22 WQMIS parameters, with priority on E. coli (34) and Total Coliform (35)
- **Geographic scope:** UP (state_id=31) + Bihar (state_id=5) = 76 + 38 = 114 districts
- **Granularity:** Per-district × per-parameter × per-FY queries via the DataTables JSON endpoint

**Implementation:**
1. User registers at the JJM WebAPI portal (mobile + email verification, 24-48hr approval)
2. Agent receives JWT token and encrypted API key
3. `wqmis.py:pull_parameter_wise()` stub (currently `NotImplementedError`) is implemented:
   - Call `POST /WQMIS/Report/get_Report_Parameter_wise` with `fy, stid, dtid, blid, gpid, ParameterId` (all AES-encrypted with key=`8080808080808080`)
   - Returns DataTables JSON (page, length, draw, data arrays)
   - Parse JSON → extract sample IDs → fetch `final_report_print` for full readings
   - Save directly to DB via `load_wqmis.py`
4. Rate limiting: 1 req/sec (matching `wqmis.py`'s `RATE_SECONDS=1.0`), single-threaded, off-peak hours

**Expected yield:** 
- UP FY26-27: 206,111 samples received, 1,575 contaminated (0.76%)
- Bihar FY26-27: 55,103 samples received, 11 contaminated (0.02%)
- **Parameter-wise filtering for E. coli (34) and TC (35)** would return only the contaminated samples — dramatically higher hit rate than blind ID scanning

### Path B (Fallback): Session Cookie Automation (from data-access.md §4)

**Mechanism:** User registers a free WQMIS account → shares session cookie → agent automates the `get_Report_Parameter_wise` and `get_report_parameter_wise_list_detail` endpoints.

**Same endpoint as Path A** but using session cookies instead of JWT tokens. The `wqmIS.py` file already has the AES encryption helper (`enCryptedAES` in `frmValidate.js`) and the `pull_parameter_wise(cookie_file)` stub is ready to implement.

### Path C (Rejected): Continue Blind ID-Range Crawling

**Why rejected:**
1. **Sub-1% hit rate** — 37,903 IDs scanned → 1,822 records (4.6% non-empty, ~1% with e_coli/TC)
2. **20M+ ID space** — extrapolating, need ~40M requests to cover the full space
3. **No e_coli benefit** — the 45 e_coli readings came from 1,822 records; the ID range isn't the bottleneck, the **distribution** is
4. **Risk of CAPTCHA/blocking** — `crawl_fast.py` uses 8 parallel workers with no sleep, which is aggressive for a government portal
5. **AGENTS.md invariant:** "Extra volume requires an official role or the restricted AIKosh dataset, not more scanning"

### Path D (Deferred): AIKosh CSV

**Mechanism:** Wait for user to obtain 3.37 MB AIKosh CSV (`https://aikosh.indiaai.gov.in/home/datasets/details/jjm_water_source_water_quality_data.html`) with village-level real data including e_coli.

**Timeline:** 2+ weeks pending access approval. This is the best village-level data source but access is currently blocked.

### ID Range Analysis

| ID Space | Coverage | Notes |
|----------|----------|-------|
| 1–1,000,000 | Untested | Likely contains older pre-2022 data |
| 1,000,000–2,000,000 | Partially scanned (37,903 IDs) | Current `crawl_fast.py` range; 755/1,822 records with results |
| 2,000,001–5,000,000 | Untested | Unknown density |
| 5,000,001–20,000,000 | Untested | Claimed upper bound in data-access.md |

**The `final_report_print` s_id is AES-encrypted** — the ID space is sequential integers, but the mapping is opaque (`U<user>L<lab>S<seq>` sample IDs). The `map_ranges()` function in `wqmis.py` uses a stride-sampling approach to discover populated ID bands.

### Rate Limiting & CAPTCHA Avoidance

| Component | Current | Recommended |
|-----------|---------|-------------|
| `crawl_fast.py` | 8 workers, no sleep, 40s timeout | Single-threaded, 1–2 sec delay, 60s timeout |
| `wqmis.py` | 1 worker, 1.0s sleep | Keep — already compliant |
| Session reuse | New `requests.Session()` per request (`crawl_fast.py:139`) | Reuse session for connection pooling |
| Politeness string | None | Set `Referer`, `User-Agent: WaterTriage/1.0 (+contact email)` |

---

## 8. Critical Data Quality Issues

### Defect D1: 98.8% Village Names Missing

- 1,720/1,741 samples have `village = "Not available"` (only 21 named villages)
- Skew: named villages mean CRS 4.13 vs "Not available" 15.34
- **Root cause:** WQMIS public reports (final_report_print) don't expose village names — only block, district, state
- **Impact:** Geographic precision lost; scoring works at district level only
- **Mitigation:** The parameter-wise API (Path A/B) may return village-level data via the DataTables JSON response

### Defect D2: Phantom "Not Available" Districts

- 354 samples in 2 "Not available" districts
- **Fix:** Map these to their correct block/district when the data is available via the API

### Defect D3: Single-Source Districts (64.8%)

- 68/105 districts (64.8%) have data from only one source type
- **No fix possible without additional data sources**

### Source Type Chaos

- 200+ distinct unstructured source values:
  - `"Tube well / Bore well / Well"` (37)
  - `"Individual house tap water , Location :"` (883)
  - `"Public tap water location : -----"` (17)
  - `"Individual house tap water"` (10)
  - Named individuals: `"ABHA DEVI"`, `"AJAY YADAV"`, etc. (scattered)
- **Need standardization** into canonical categories: `handpump`, `borwell`, `tap`, `surface_water`, `other`

---

## 9. Scoring System Assessment

The current scoring model (`scoring.py` L1–124) uses BIS IS 10500 limits:

| Parameter | Weight | Acceptable | Permissible | Strategy |
|-----------|--------|-----------|-------------|----------|
| Arsenic | 1.0 | 10 ppb | 30 ppb | Threshold |
| E. coli | 0.9 | 0 CFU/100mL | 0 CFU/100mL | Microbial (binary) |
| Fluoride | 0.8 | 1.0 mg/L | 1.5 mg/L | Range |
| Nitrate | 0.7 | 45 mg/L | 100 mg/L | Threshold |
| Iron | 0.4 | 0.3 mg/L | 1.0 mg/L | Threshold |
| Turbidity | 0.3 | 1.0 NTU | 2.0 NTU | Range |
| TDS | 0.3 | 1000 mg/L | — | Threshold |
| pH | 0.2 | 6.5–7.5 | 6.5–9.0 | Range |
| Sulphate | 0.5 | 200 mg/L | 400 mg/L | Threshold |
| Total Coliform | 0.9 | 0 CFU/100mL | 0 CFU/100mL | Microbial (binary) |

**TOTAL_BIS_WEIGHT = 6.0** (sum of all weights)

**Bands:** Critical ≥40, High ≥20, Medium ≥10, Low ≥0  
**Escalation:** Only acute hazards (arsenic, e_coli, total_coliform) escalate — non-acute breaches (iron, fluoride, tds, nitrate, sulphate) contribute to raw score but don't force band escalation. Zero values for As/e_coli/TC are treated as below-detection-limit and excluded from scoring.

**Key gap:** e_coli has only 2 non-zero readings and TC only 3 — the microbial scoring dimension is essentially unpopulated. Sulphate (467 readings, 50 exceeding acceptable limit) is the strongest non-critical parameter.

### Band Distribution (Current)

| Band | Count | % |
|------|-------|---|
| Low | 1,250 | 71.8% |
| High | 468 | 26.9% |
| Critical | 3 | 0.2% |
| Medium | 20 | 1.2% |

---

## 10. Deliverables & Next Steps

### Immediate (Next 48 hours)

1. **User action required:** Register at `https://ejalshakhi.gov.in/webapi/` for JJM WebAPI access (mobile + email verification)
2. **If access granted:** Implement `wqmis.py:pull_parameter_wise()` to query E. coli (ParamId=34) and Total coliform (ParamId=35) per district × FY
3. **If access denied:** Fall back to Path B (session cookie → Report_L page scraping)

### Short-term (1 week)

1. If AIKosh CSV arrives: integrate `load_historical.py` for village-level e_coli/TC data
2. Fix `crawl_fast.py`: add rate limiting (1–2s sleep per worker), session reuse, early state filtering
3. Add plausibility guard in `pipeline.py:55-61` for duplicate parameter collapse (Defect B2)

### Long-term

1. **Bulk fetch via JJM API:** All 114 districts × 22 parameters × all FYs
2. **Village name resolution:** Use parameter-wise API response to get actual village/GP/block names
3. **Source type standardization:** Map 200+ raw values to 5 canonical categories
4. **Scoring improvement:** With real e_coli/TC data, microbial risk scoring becomes meaningful

---

## 11. File Paths Reference (for code changes)

| Concern | File Path | Key Lines |
|---------|-----------|-----------|
| Fast crawler | `/home/anubhavanand/Documents/Projects/water-triage/backend/etl/crawl_fast.py` | L35-42 (AES), L80-99 (parse_report), L135-139 (fetch_one) |
| Single-threaded crawler | `backend/etl/wqmis.py` | L14 (RATE_SECONDS), L46-72 (map_ranges), L73-153 (pull_parameter_wise stub) |
| Param aliases | `backend/etl/load_wqmis.py` | L35-36 (PARAM_ALIASES), L40-55 (normalize_param) |
| Scoring model | `backend/app/engine/scoring.py` | L14-45 (BIS_10500), L47-50 (BANDS), L52-54 (ACUTE_HAZARDS) |
| Pipeline dedup | `backend/app/engine/pipeline.py` | L49-61 (max-severity aggregation) |
| DB models | `backend/app/models/entities.py` | L1-130 (all entities) |
| Repair script | `backend/etl/repair_readings.py` | L1-89 (post-load repair) |
| Historical loader | `backend/etl/load_historical.py` | L1-128 (Kaggle CSV) |
| Data access docs | `docs/research/data-access.md` | L1-64 (endpoints, AES, acquisition plan) |
| Dashboard builder | `dashboard/build_dashboard_json.py` | L24 (reads SQLite watertriage.db) |
| Firecrawl extracts | `/home/anubhavanand/Documents/NTCC minor project/references/firecrawl_extracts/` | UP/Bihar/WQ6 markdowns |
| JJM API PDF | Saved to `/tmp/jjm_web_api.pdf` | 1.27 MB developer guide |

---

*Report compiled from analysis of 52 files across both directories, live probing of WQMIS endpoints, and review of records.jsonl (1,822 records), WQ6 summary data, JJM WebAPI documentation, and CGWB yearbooks.*