# AGENTS.md — Handoff for AI Agents Working on WaterTriage

> Read this first. It gives any agent (Claude, Kimi, ChatGPT, opencode, etc.) the current project state without re-deriving it.

**Last updated:** 17 Aug 2026
**Owner:** Anubhav Anand · NTCC Minor Project (ETMN100) · Deadline: 09/10/2026 (final report 26/10, viva 2–6 Nov)

---

## 1. Project Goal

Build **WaterTriage**: a system that scores water quality risk at village level for UP + Bihar using BIS IS 10500 limits, and produces an **intervention priority list** — "which village gets a repair team first and why" — visualized on a professional dashboard.

## 2. Decisions Already Made (Do NOT Re-Open)

1. **Stack:** FastAPI + SQLAlchemy 2 + PostgreSQL (Docker) + Alembic + Streamlit dashboard
   - React was explicitly rejected (overkill; backend-focused student)
2. **Scope:** 6 districts only (3 UP + 3 Bihar), NOT all 113 districts
   - UP: Unnao, Ferozabad, Hardoi · Bihar: Katihar, Araria, +1 TBD
3. **Data path:** WQMIS WQ4 manual exports → AIKosh CSV → synthetic fallback (in that order)
4. **Scoring model:** per-parameter severity = (value − acceptable)/(permissible − acceptable), clamped 0–1; composite = weighted avg × 100. Weights: As 1.0, E. coli 0.9, F 0.8, Nitrate 0.7, Iron 0.4, Turbidity 0.3, TDS 0.3, pH 0.2. Bands: Critical ≥75, High 50–74, Medium 25–49, Low <25
5. **Guide name:** "Dr. Girish Paliwal" (no extra designation)
6. **WPR sequence:** 2=Abstract, 3=Introduction, 4=Related Work, 5=Methodology, 6=Results, 7=Discussion, 8=Conclusion, 9=Full Paper, 10=Plagiarism, 11=Completion

## 3. Data Situation (Critical — read before building ETL)

| Source | Status | Contents |
|--------|--------|----------|
| WQMIS WQ4 (`ejalshakti.gov.in/WQMIS/Report/Report_p`) | ⚠️ NEEDS MANUAL EXPORT TEST (1 district, Unnao) | Individual lab reports with real readings (pH, TDS, As, F, NO3, E. coli) |
| WQMIS PDFs (`up report contaminent wise.pdf`, `bihar report contaminent wise.pdf`) | ✅ Parsed | District-level contamination COUNTS only (no readings) |
| WQMIS Excel files (5 in Downloads) | ✅ Parsed | Summary-level only (HTML tables saved as .xls, village counts, FTK usage) |
| AIKosh CSV (3.37 MB) | ❌ Pending 2+ weeks | Village-level real data, MIT license |
| Individual WQ4 reports | ✅ VERIFIED public | `https://ejalshakti.gov.in/WQMIS/Common/final_report_print?s_id=<base64>` — 2 samples fetched (Raebareli, Lucknow) |

**Known problem districts:** Unnao (fluoride 33), Ferozabad (fluoride 33), Hardoi (E. coli 18, TC 41) [UP]; Katihar (iron 6), Araria (turbidity 1) [Bihar]. Bihar much cleaner overall (~7 contaminated villages in FY 2026-27).

**Do NOT attempt bulk scraping of WQMIS** — session auth + CAPTCHA + rate limits; manual export test decides the automation approach.

## 4. Current Progress (Week 3–4)

- ✅ Git repo initialized, pushed to `github.com/anubhavaanand/water-triage` (public)
- ✅ `pyproject.toml` deps declared (fastapi, sqlalchemy, alembic, psycopg2-binary, pandas, pydantic, uvicorn, python-dotenv)
- ✅ `uv.lock` resolved, `.venv` created (Python 3.13.14)
- ✅ `.env` configured with DATABASE_URL (PostgreSQL `jjm_triage` db)
- ✅ WPR-1 submitted (Satisfactory); WPR-2, WPR-3 drafted
- ✅ All 5 Excel files parsed; WQ4 individual reports verified accessible
- ⬜ Backend code: NOT started (empty `backend/app`, `backend/etl`)
- ⬜ Dashboard: NOT started
- ⬜ Docker compose: NOT created
- ⬜ Data: NOT downloaded/loaded

## 5. Next Steps (priority order)

1. **User action:** manual WQ4 export for Unnao district → confirm data format for ETL
2. **Build backend skeleton:** `backend/app/{main.py, config.py, database.py, models.py, schemas.py, scoring.py, recurrence.py}` + `routers/` (samples, districts, scoring, priority)
3. **DB schema** (target tables): states, districts, blocks, panchayats, villages, bis_limits, water_samples, parameter_readings, risk_scores, interventions
4. **API endpoints:** `/api/samples`, `/api/samples/{id}`, `/api/districts`, `/api/districts/{id}`, `/api/scoring`, `/api/priority`, `/api/priority/top/{n}`, `/api/compare`
5. **ETL parser** for confirmed WQ4 format → load 6-district subset
6. **Docker compose:** postgres + backend + dashboard
7. **Streamlit dashboard:** map (severity-colored markers) + district table + priority list + UP/Bihar comparison
8. **WPR-4 (Literature Review)** — due Week 4, draft from existing research (JJM WQMIS, BIS 10500, JalRakshak comparison)

## 6. Environment Facts

- Linux (CachyOS/Arch), fish shell, KDE Plasma Wayland
- Python 3.13.14 in repo venv; system Python 3.14.6; uv 0.11.30
- Node 24.18.0, Docker available, Git 2.55.0
- 11 GB RAM, 4 cores, btrfs root
- User runs commands with `yay`/`paru` for AUR

## 7. Conventions

- No code comments unless asked; minimal, surgical changes
- Learning style: user wants important parts explained, boilerplate skipped
- Python ≥3.13, uv-managed deps (edit `pyproject.toml` → `uv sync`)
- Tests: pytest (empty `tests/` for now)
- `.env` is gitignored — never commit it (DB password inside)