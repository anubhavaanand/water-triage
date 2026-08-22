# WaterTriage

**A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar**

B.Tech NTCC Minor Project (ETMN100) — Anubhav Anand (A41105223039), Amity University Greater Noida
Guide: Dr. Girish Paliwal

---

## Status (as of 17 Aug 2026)

> **Phase:** Week 3–4 of 12 · Engineering just started · Data acquisition in progress

| Area | State |
|------|-------|
| Backend | Skeleton only (empty `backend/app`, `backend/etl` dirs) |
| Data | 5 WQMIS Excel files parsed (summary-level only); WQ4 lab reports verified publicly accessible |
| Dashboard | Not started (Streamlit planned) |
| WPRs | WPR-1 ✅ submitted (Satisfactory) · WPR-2 ✅ drafted · WPR-3 ✅ drafted · WPR-4 (Literature Review) due Week 4 |
| Repo | Pushed to GitHub, public |

## What This System Does

1. **Ingests** water quality test data (pH, TDS, fluoride, arsenic, nitrate, E. coli, iron, turbidity) from government sources (WQMIS / JJM).
2. **Scores** each village/sample against BIS IS 10500 limits using a weighted severity model.
3. **Ranks** villages into severity bands (Critical ≥ 75, High 50–74, Medium 25–49, Low < 25) to produce an intervention priority list.
4. **Displays** results via an interactive dashboard: severity-colored map, district tables, and UP vs Bihar comparisons.

## Stack

- **Backend:** Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (Docker)
- **Dashboard:** Streamlit (+ Folium maps)
- **Tooling:** uv · Docker Compose

## Data Acquisition Plan (priority order)

1. **WQMIS WQ4 manual exports** (primary) — per-district lab test exports from `ejalshakti.gov.in/WQMIS/Report/Report_p`; individual reports verified public via `final_report_print?s_id=` URLs
2. **AIKosh CSV** (backup) — village-level dataset, access pending
3. **Synthetic data** (fallback) — generated from known contamination patterns (Unnao/Ferozabad fluoride, Hardoi E. coli, Katihar iron)

**Scope: state-wide** — all of Uttar Pradesh (76 districts) + Bihar (38 districts); synthetic demo subset covers Unnao, Ferozabad, Hardoi, Katihar, Araria, Saharsa

## How to Run (once implemented)

```bash
uv sync                 # install deps
docker compose up -d postgres   # start DB
uv run uvicorn app.main:app --reload   # backend (from backend/)
uv run streamlit run app.py      # dashboard (from dashboard/)
```

## Project Layout (target)

```
backend/app/     FastAPI app (models, routers, scoring, recurrence)
backend/etl/     WQMS/AIKosh parsers + loaders
dashboard/       Streamlit pages
data/            raw/ processed/ synthetic/
tests/           pytest suites
```

## WPR Timeline

| WPR | Content | Status |
|-----|---------|--------|
| 1 | Topic submission | ✅ Submitted, Satisfactory |
| 2 | Abstract & Keywords | ✅ Drafted |
| 3 | Introduction | ✅ Drafted |
| 4 | Related Work / Literature Review | Due Week 4 |
| 5–8 | Methodology, Results, Discussion, Conclusion | Upcoming |
| 9–11 | Full paper, plagiarism, completion | Final |

## Docs for Agents

- **`AGENTS.md`** — handoff context: decisions, data findings, next steps (read this first)
- `plan.md` in the NTCC project folder — full 12-week execution plan
- `SESSION_HANDOFF.md` in the NTCC project folder — session-by-session context