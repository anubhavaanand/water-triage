# WaterTriage — System Architecture

> v1.0 · 23 Aug 2026 · Companion to `docs/research/data-catalog.md` and WPR-5 (Methodology)

## 1. System Overview

```
┌────────────────────── ACQUISITION ──────────────────────┐
│  WQMIS public crawler      Registry loader   Kaggle     │
│  (etl/wqmis.py)            (etl/load_historical) mirrors│
│  s_id = AES(id), 1 rps     CSV → geo upsert  data/raw/ │
└──────────────┬──────────────────────────────────────────┘
               ▼
       ┌───────────────┐   jsonl cache: data/raw/wqmis/records.jsonl
       │ PostgreSQL 16 │   (docker-compose, volume pgdata)
       │ jjm_triage    │
       └──────┬────────┘
              ▼
┌────────────────────── ENRICHMENT ────────────────────────┐
│ scoring engine  (engine/scoring.py)                      │
│   severity = f(value, BIS acceptable/permissible)        │
│   composite = Σ wᵢsᵢ / Σ wᵢ ×100 + band escalation       │
│ recurrence engine (engine/recurrence.py)                 │
│   persistent | historical-only | new per param           │
└──────────────┬───────────────────────────────────────────┘
               ▼
┌────────────────────── SERVING ───────────────────────────┐
│ FastAPI (app/main.py :8000)                              │
│  /api/priority[/top/{n}]  ranked intervention list       │
│  /api/samples[/{id}]      samples + readings             │
│  /api/districts[/{id}]    district summaries             │
│  /api/recurrence[/{vid}]  hotspot ranking                │
│  /api/compare             state comparison               │
│ CORS open · lifespan seeds bis_parameters                │
└──────────────┬───────────────────────────────────────────┘
               ▼
      dashboard/index.html — zero-dependency console
      (baked snapshot + live-API layer with OFFLINE fallback;
       queue / compare / map / drill-down views)
```

## 2. Storage Schema (PostgreSQL)

| Table | Purpose |
|-------|---------|
| states, districts, villages | geo hierarchy; village carries block + panchayat |
| bis_parameters | BIS IS 10500 limits + health weight + strategy (`threshold`/`range`/`microbial`) — seeded at startup |
| water_samples | one lab report (wqmis_ref unique, source, dates) |
| readings | parameter_key + value per sample |
| risk_scores | composite score, band, worst_parameter (recomputable) |
| historical_contamination | registry events (village, parameter, year) 2009–2012 |
| interventions | planned action log (schema-ready, UI pending) |

**State-name canonicalization:** both loaders map to Title Case ("Uttar Pradesh", "Bihar"); enforced after two merge incidents.

## 3. Scoring Model (design rationale)

1. **Per-parameter severity** interpolates linearly between BIS acceptable and permissible limits — policy-legible, auditable. No-relaxation params (nitrate, iron) and microbial hits saturate at 1.0.
2. **Composite** is the weighted mean over *tested* parameters (weights = documented health severity, cf. AHP-WQI literature in `docs/research/literature-review-notes.md`).
3. **Band escalation** fixes the dilution flaw of pure averages: any full-severity breach ⇒ min High; acute hazards (E. coli, total coliform, arsenic) ⇒ Critical regardless of numeric score.
4. **Recurrence score** blends registry history (years present, capped at 4) with current exceedance: persistent ≫ new > historical-only; verdicts `chronic-hotspot / recurring / watchlist / no-history`.

## 4. Acquisition Strategy

| Channel | Mode | Rate limit | Notes |
|---------|------|-----------|-------|
| final_report_print crawler | public, sequential AES(id) | 1 req/s, cached HTML, resume file | primary; ID-space clusters geographically → dense-range crawling |
| parameter-wise API | session-gated | — | Public User role denied; revisit with official role |
| AIKosh CSV | pending approval | — | drop-in replacement schema already mapped |

Politeness: single-threaded, honest UA, off-peak windows, everything cached under `data/raw/wqmis/`.

## 5. Performance Notes

- `list_recurrent_villages` was N+1 over 14k villages (37 s). Rewritten as 4 set-based queries + in-memory compute: **0.58 s**, identical output. Regression-guarded by tests.
- Dashboard ships a baked snapshot for instant/offline load and upgrades to LIVE when the API is reachable (header chip); drill-downs degrade gracefully.

## 6. Known Limitations / Roadmap

1. Crawler coverage: 2k of ~20M IDs mapped so far — dense-range expansion is mechanical but slow; consider FY-targeted ranges once more boundaries are mapped.
2. Duplicate parameter rows within one report (e.g., two pH entries) currently take the last reading in scoring; dedupe rule pending.
3. `interventions` table unused by UI yet — feeds WPR-7 discussion (action tracking loop).
4. Alembic migrations not yet introduced (create_all dev mode) — required before any multi-env deploy.

## 7. Testing

26 pytest cases: scoring purity (interpolation, escalation, bands), API contract via TestClient on seeded SQLite, WQMIS parser fixtures (incl. malformed decimals), recurrence units + PG integration suite (skips cleanly without DB).
