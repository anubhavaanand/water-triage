# WaterTriage

**Live Demo:** [https://water-triage.onrender.com](https://water-triage.onrender.com) · **GitHub Pages:** [anubhavaanand.github.io/water-triage](https://anubhavaanand.github.io/water-triage)


**A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar**

B.Tech NTCC Minor Project (ETMN100) — Anubhav Anand, Amity University Greater Noida
Guide: Dr. Girish Paliwal

---

## What This System Does

1. **Ingests** water quality test data from government sources (WQMIS / JJM).
2. **Scores** each village/sample against BIS IS 10500 limits using a weighted severity model.
3. **Ranks** villages into severity bands (Critical ≥ 40, High ≥ 20, Medium ≥ 10, Low ≥ 0) to produce an intervention priority list.
4. **Displays** results via an interactive dashboard: severity overview, priority queue, and district parameters.

## Key Results (v2 — 113 Districts)

| Metric | UP (75) | Bihar (38) | Total (113) |
|---|---|---|---|
| **Districts Scored** | 75 (100%) | 38 (100%) | 113 (100%) |
| **Critical** | 32 | 14 | 46 |
| **High** | 18 | 9 | 27 |
| **Medium** | 13 | 6 | 19 |
| **Low** | 12 | 9 | 21 |
| **Pathogen Overrides** (E. coli) | 27 | 5 | 32 |
| **Arsenic Escalations** | 3 | 10 | 13 |

**Lab-ID Resolution:** 302/354 missing districts resolved (85.3%) via ASP.NET session cookie handshake with `ejalshakti.gov.in`. Only 52 samples (2.99%) held back for multi-district regional lab L158.

**Village Coverage:** 305/1,741 samples (17.52%) now have named village/habitation locations — a 1,352% gain from the baseline of 21 samples.

## Data & Limitations

**Corpus:** 1,741 samples · 6,792 parameter readings · 10 scored parameters · 2022 collection year.

### Scored parameters and BIS IS 10500 limits

Severity per parameter is `(value − acceptable) / (permissible − acceptable)`, clamped to 0–1. Where a parameter has no permissible limit (or `permissible <= acceptable`), any exceedance is binary — full 1.0 severity. Zero values for arsenic, E. coli, and total coliform are treated as below detection limit and excluded from scoring.

| Parameter | Unit | Acceptable | Permissible | Weight | Strategy |
|---|---|---|---|---|---|
| Arsenic | mg/L | 0.01 | none | 1.0 | threshold (binary) |
| E. coli | CFU/100 mL | 0 | 0 | 0.9 | microbial (binary) |
| Total Coliform | CFU/100 mL | 0 | 0 | 0.9 | microbial (binary) |
| Fluoride | mg/L | 1.0 | 1.5 | 0.8 | threshold |
| Nitrate | mg/L | 45 | none | 0.7 | threshold (binary) |
| Sulphate | mg/L | 200 | 400 | 0.5 | threshold |
| Iron | mg/L | 0.3 | none | 0.4 | threshold (binary) |
| Turbidity | NTU | 1.0 | 5.0 | 0.3 | threshold |
| TDS | mg/L | 500 | 2000 | 0.3 | threshold |
| pH | — | 6.5 | 8.5 | 0.2 | range |

`TOTAL_BIS_WEIGHT = 6.0` (sum of the weights above). Composite score is `weighted_sum / 6.0 × 100`, which keeps scores comparable across samples with different parameter coverage. Bands: **Critical ≥ 40, High ≥ 20, Medium ≥ 10, Low ≥ 0**. Only acute hazards (arsenic, E. coli, total coliform) escalate a sample to Critical on a full breach; iron, fluoride, TDS, nitrate, and sulphate contribute to the score but do not force escalation.

### Recorded but not weighted

Chloride, Total Alkalinity, and Total Hardness are present in the WQMIS corpus but carry no weight in the severity model, so they affect neither the composite score nor the band assignment. They are retained for reference and future sensitivity analysis.

### Known data gaps by district

| District | State | Gap |
|---|---|---|
| Unnao | UP | Fluoride contamination concentrated; 33 affected villages recorded |
| Ferozabad | UP | Fluoride contamination concentrated; 33 affected villages recorded |
| Hardoi | UP | Microbial: E. coli 18, Total Coliform 41 |
| Katihar | Bihar | Iron exceedances; 6 affected villages recorded |
| Araria | Bihar | Turbidity exceedances; 1 affected village recorded |

### Provenance caveats

- **Source:** WQMIS (JJM / `ejalshakti.gov.in`) lab reports, extracted August–September 2026, verified against official Form WQ6 for all 75 UP + 38 Bihar districts.
- **Crawl is non-random.** The corpus describes what was published and retrievable, not a statistically representative sample. Comparisons between states or districts describe this corpus only.
- **Single year.** All water samples are from 2022; historical registry events span 2009–2012 and are used only for recurrence classification.
- **Village identifiability is partial.** 305/1,741 samples (17.52%) have named village/habitation locations. The remainder are mapped to district and lab only.
- **52 samples (2.99%)** are held back because they trace to multi-district regional lab L158.
- **Iron limit conflict.** 876 readings carry an acceptable limit of 1.0 mg/L in the raw records; scoring uses the stricter 0.3 mg/L from IS 10500:2012. A sensitivity run at 1.0 mg/L is exposed via `/api/meta`.
- **Panel size drives score.** Composite scores depend on how many parameters were tested, so single-parameter iron samples can score higher than multi-parameter samples with broader contamination. Treat cross-district score comparisons as indicative, not definitive.
- **Microbial coverage is thin.** E. coli was tested in 45 samples (2.6%); the acute-hazard Critical floor rests heavily on that small subset.
- **Synthetic data** exists only under `backend/tests/fixtures` for test purposes. No synthetic readings appear in reported results.

### Framework and tests

- **Framework:** React SPA frontend with Python FastAPI backend, Docker Compose for local deployment.
- **Tests:** 28 passed, 1 skipped (offline); 29 passed (with PostgreSQL).

## Data Gaps Recovery

| Before | After | Resolution |
|---|---|---|
| 354 Not Available (20.3%) | 52 (2.99%) | 302/354 resolved via 20 Lab IDs |
| 21 named villages (1.21%) | 305 (17.52%) | +284 extracted from source field |
| Bihar: 15 missing (L268) | 0 missing | L268 → Samastipur |
| UP: 35 missing (6 labs) | 0 missing | L405→Raebareli, L339→Sonbhadra, etc. |

## Documentation

| Document | What it covers |
|---|---|
| [DESIGN.md](DESIGN.md) | System architecture, data flow, scoring model, and design decisions |
| [AGENTS.md](AGENTS.md) | AI agent handoff — current project state, frozen decisions, conventions |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Acquisition → enrichment → serving pipeline diagram |
| [docs/agents/](docs/agents/) | Issue tracker, triage label, and domain-doc conventions |
| [docs/REVIEW_PACKET.md](docs/REVIEW_PACKET.md) | Review packet for evaluation |

### Scoring model summary

Per-parameter severity:

```
severity = (value − acceptable) / (permissible − acceptable)     # clamped to 0..1
```

Composite score:

```
composite = (Σ wᵢ · severityᵢ) / TOTAL_BIS_WEIGHT × 100          # TOTAL_BIS_WEIGHT = 6.0
```

Bands: **Critical ≥ 40 · High ≥ 20 · Medium ≥ 10 · Low ≥ 0**. Acute hazards (arsenic, E. coli, total coliform) escalate to Critical on a full breach. The full parameter table with limits and weights is in [Data & Limitations](#data--limitations); the canonical source is `BIS_10500` in `backend/app/engine/scoring.py`.

## API Reference

FastAPI generates an interactive schema at runtime — no separate build step required.

| URL | Description |
|---|---|
| `/docs` | Swagger UI — browse and call endpoints |
| `/redoc` | Read-only reference |
| `/openapi.json` | OpenAPI schema |

Key endpoints (all prefixed with `/api`):

| Endpoint | Purpose |
|---|---|
| `GET /api/samples` | Sample list, filterable by district, band, limit, offset |
| `GET /api/samples/{id}` | One sample with all readings and its risk score |
| `GET /api/districts` | Districts with band counts and data-quality tiers |
| `GET /api/districts/{id}` | District detail with villages and latest scores |
| `GET /api/districts/full-triage` | Full 113-district multi-tier triage payload |
| `GET /api/scoring/parameters` | BIS IS 10500 parameter table used by the engine |
| `GET /api/priority` | Ranked intervention queue, filterable by state and band |
| `GET /api/priority/top/{n}` | Top *n* priority items |
| `POST /api/scoring/recompute` | Recompute all risk scores |
| `GET /api/compare` | Per-state aggregate comparison |
| `GET /api/recurrence` | Recurrent districts ranked as chronic hotspots |
| `GET /api/recurrence/{village_id}` | Historical vs current comparison for one village |
| `GET /api/validation/cgwb` | CGWB pH compliance + WQ6 validation ground truth |
| `GET /api/meta` | Aggregate dashboard payload: corpus, bands, scoring, limitations |

Example:

```bash
curl "http://localhost:8000/api/priority?state=Bihar&band=critical"
```

```json
[
  {
    "rank": 1,
    "sample_id": 1204,
    "village": "Baraon",
    "block": "Baraon",
    "district": "Katihar",
    "state": "Bihar",
    "score": 71.67,
    "band": "Critical",
    "worst_parameter": "iron",
    "n_scored_params": 1,
    "collected_on": "2022-08-02T00:00:00"
  }
]
```

The API is read-only and unauthenticated, with open CORS. See [docs/api.md](docs/api.md) for request and response details on every endpoint.

## Stack

- **Backend:** Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (Docker)
- **Dashboard:** React + Vite · 6-tab interactive UI with dark mode
- **Tooling:** uv · Docker Compose · GitHub Actions (Playwright E2E)

## Security Notes

- `.env` is gitignored — never commit it (contains DB password)
- Use `.env.example` as a template for local development
- PostgreSQL password must be set via `POSTGRES_PASSWORD` environment variable
- Found a vulnerability or an exposed credential? See [SECURITY.md](SECURITY.md) for how to report it privately (not via public issues).
- Community expectations for respectful and inclusive participation are set out in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## How to Run

1. **Start the Database:**
```bash
docker start watertriage-db
```

2. **Run Backend (FastAPI):**
```bash
uv sync
uv run uvicorn backend.app.main:app --port 8000
```

3. **Run Dashboard (React):**
```bash
cd dashboard
npm install
npm run dev
```

## License

Released under the [MIT License](LICENSE). The WQMIS-derived data under `data/` originates from
government open data portals (JJM WQMIS, CGWB, IMIS) and remains subject to its own terms; see
[Data & Limitations](#data--limitations) for provenance.
