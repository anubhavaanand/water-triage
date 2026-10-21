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

- **Dataset:** 1,741 samples, 6,792 parameter readings across 10 scored BIS IS 10500 parameters (pH, TDS, Turbidity, Sulphate, Iron, Arsenic, Fluoride, Nitrate, Total Coliform, E. coli). Chloride, Total Alkalinity and Total Hardness are recorded in the corpus but are not weighted in the severity model.
- **Data Provenance:** Extracted from WQMIS lab reports between August and September 2026. Data verified against official Form WQ6 (75 UP + 38 Bihar districts).
- **Framework:** React SPA frontend with Python FastAPI backend, Docker Compose for local deployment.
- **Tests:** 28 passed, 1 skipped (offline); 29 passed (with PostgreSQL).

## Data Gaps Recovery

| Before | After | Resolution |
|---|---|---|
| 354 Not Available (20.3%) | 52 (2.99%) | 302/354 resolved via 20 Lab IDs |
| 21 named villages (1.21%) | 305 (17.52%) | +284 extracted from source field |
| Bihar: 15 missing (L268) | 0 missing | L268 → Samastipur |
| UP: 35 missing (6 labs) | 0 missing | L405→Raebareli, L339→Sonbhadra, etc. |

## Stack

- **Backend:** Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (Docker)
- **Dashboard:** React + Vite · 6-tab interactive UI with dark mode
- **Tooling:** uv · Docker Compose · GitHub Actions (Playwright E2E)

## Security Notes

- `.env` is gitignored — never commit it (contains DB password)
- Use `.env.example` as a template for local development
- PostgreSQL password must be set via `POSTGRES_PASSWORD` environment variable

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
