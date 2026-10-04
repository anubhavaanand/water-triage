# WaterTriage

**A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar**

B.Tech NTCC Minor Project (ETMN100) — Anubhav Anand (A41105223039), Amity University Greater Noida
Guide: Dr. Girish Paliwal

---

## What This System Does

1. **Ingests** water quality test data from government sources (WQMIS / JJM).
2. **Scores** each village/sample against BIS IS 10500 limits using a weighted severity model.
3. **Ranks** villages into severity bands (Critical ≥ 75, High 50–74, Medium 25–49, Low < 25) to produce an intervention priority list.
4. **Displays** results via an interactive dashboard: severity overview, priority queue, and district parameters.

## Data & Limitations

- **Dataset:** 1,741 samples, 6,792 parameter readings.
- **Data Provenance:** Extracted from WQMIS lab reports between August and September 2026.
- **Framework:** The dashboard was redesigned as a React SPA with a Python FastAPI backend.
- **Tests:** 29 passed. 

## Stack

- **Backend:** Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (Docker)
- **Dashboard:** React
- **Tooling:** uv · Docker Compose

## How to Run

1. **Start the Database:**
```bash
docker start watertriage-db
```

2. **Run Backend (FastAPI):**
```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --port 8000
```

3. **Run Frontend (React):**
```bash
cd frontend
npm run dev
```
