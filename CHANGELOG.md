# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until the first tagged release, the version in `pyproject.toml` stays at `0.1.0` and dates are used as the primary marker.

## How to add an entry

Add your line under `## [Unreleased]` in the section that matches the type of change. Use these categories:

- **Added** — new features, endpoints, parameters, or capabilities
- **Changed** — changes to existing behaviour, including scoring model or band changes
- **Deprecated** — features that will be removed
- **Removed** — features that were removed
- **Fixed** — bug fixes
- **Security** — vulnerability fixes and hardening
- **Data** — corpus refreshes, ETL changes, coverage changes

Rules of thumb:

- One bullet per user-visible change. Do not list every commit.
- Start the bullet with a verb, and put the affected area in parentheses: `Fixed (scoring) clamp severity at 1.0 for iron exceedances.`
- If the change alters risk scores, band counts, or headline figures, say so explicitly and update the Key Results table in `README.md` in the same pull request.
- Reference the issue or PR number at the end of the bullet.
- Breaking changes go under **Changed** with a `**Breaking:**` prefix and a migration note.

When a version is released, rename `## [Unreleased]` to `## [x.y.z] - YYYY-MM-DD` and open a fresh empty `## [Unreleased]` section above it.

## [Unreleased]

### Added

- `SECURITY.md` at the repo root documenting supported versions, the private vulnerability reporting channel, expected response timelines, and the credential rotation procedure (#83).
- Issue templates for bug reports and feature requests under `.github/ISSUE_TEMPLATE/`, plus a config that routes security reports to private advisories (#82).
- `CONTRIBUTING.md` covering setup, pull request expectations, and the rules for changing the scoring model or data corpus (#82).
- `CODE_OF_CONDUCT.md` based on Contributor Covenant 2.1 (#76).
- `docs/api.md` — full endpoint reference with example requests and responses, linked from the README (#80).
- A Documentation section in the README linking `DESIGN.md`, `AGENTS.md`, and `docs/`, with a summary of the scoring model and severity bands (#79).

### Changed

- The README Data & Limitations section now lists every scored parameter with its BIS IS 10500 acceptable and permissible limits, identifies the recorded-but-unweighted parameters (chloride, total alkalinity, total hardness), and documents the known district-level data gaps and provenance caveats (#78).

## [0.1.0] - 2026-11-16

First tagged baseline. All work below is pre-1.0 and describes how the system reached its current state.

### Added

- **Backend skeleton (Aug 9):** FastAPI + SQLAlchemy 2 + Alembic + pytest scaffold with a PostgreSQL target and SQLite fallback for local development.
- **Scoring engine (Aug 22):** `backend/app/engine/scoring.py` implementing the BIS IS 10500 weighted severity model with per-parameter severity, acute-hazard escalation, and severity bands. 15 tests.
- **API layer (Aug 22 – Oct 15):** endpoints for samples, districts, priority queue, state comparison, recurrence, validation, and metadata, all mounted under `/api`.
- **WQMIS crawler (Aug 23):** `backend/etl/wqmis.py` replicating the ASP.NET session handshake and AES `s_id` scheme to fetch public lab reports; fixture-tested parser.
- **Historical registry loader (Aug 23):** loads 100,690 UP + Bihar contamination events (2009–2012) from the national registry into PostgreSQL.
- **Recurrence engine (Aug 23):** classifies each parameter as persistent, historical-only, or new, with a recurrence score and chronic hotspot ranking; exposed at `/api/recurrence`.
- **Dashboard (Aug 23 – Oct 15):** console v1 → 3-view SPA → 6-tab React + Vite dashboard with priority queue, district drill-down, UP + Bihar choropleth map, validation view, and dark mode. Offline JSON fallbacks baked in for GitHub Pages.
- **113-district state-wide scoring (Oct 15):** v2 crawler and multi-tier BIS IS 10500 scoring covering all 75 UP and 38 Bihar districts. Recovered 6 districts lost to a `data[3:]` slice bug.
- **CI (Sep 20):** Playwright E2E workflow on push and pull request to `main`.
- **Deployment:** multi-stage Dockerfile, `docker-compose.yml` (PostgreSQL 16 + backend + nginx-served dashboard), and a live Render deployment.
- **Final report artefacts (Oct 22):** G-32 compliant final report and Turnitin manuscript under `docs/`.

### Changed

- **Scoring model frozen at commit `7331a9b` (Oct 9):** per-parameter severity `severity = (value − acceptable) / (permissible − acceptable)` clamped to 0–1; `composite = weighted_sum / TOTAL_BIS_WEIGHT × 100` with `TOTAL_BIS_WEIGHT = 6.0`. Weights: arsenic 1.0, E. coli 0.9, total coliform 0.9, fluoride 0.8, nitrate 0.7, sulphate 0.5, iron 0.4, turbidity 0.3, TDS 0.3, pH 0.2.
- **Bands set to Critical ≥ 40, High ≥ 20, Medium ≥ 10, Low ≥ 0 (Oct 9).** The original 75/50/25 thresholds were unreachable given the escalation logic; the Medium band previously held 1.6% of samples and now holds 7.2%.
- **Escalation narrowed to acute hazards only (Oct 9).** Arsenic, E. coli, and total coliform force a Critical floor on a full breach; iron, fluoride, TDS, nitrate, and sulphate contribute to the score without forcing escalation.
- **Scope upgraded to state-wide (Aug 23)** — all of UP (75 districts) + Bihar (38), 113 total, replacing the earlier 6-district subset.
- **Frontend re-platformed twice:** Svelte + Tailwind v4 (Sep 23) → React 18 + Vite (Oct 4) → sketch design system applied to the React dashboard (Oct 10).

### Fixed

- Sanitized malformed decimal readings such as `7..9` in the WQMIS report parser.
- Canonical state names in the historical loader; merged case-duplicate states in the database.
- Arsenic permissible limit set to `None` to match IS 10500 (no relaxation), making any exceedance binary.
- Recovered 6 missing districts from a `data[3:]` slice bug and validated the 113-district offline payload.
- N+1 query in the district endpoint, reducing response time from 37s to 0.58s.
- Dashboard offline fallbacks made base-path aware so the GitHub Pages build renders; two crash bugs fixed.
- Vite `BASE_PATH` made dynamic so the Render deployment no longer shows a blank screen.
- App made resilient to `DATABASE_URL` failures by falling back to SQLite.

### Security

- Removed the hardcoded PostgreSQL password from `docker-compose.yml`; credentials now come from `POSTGRES_PASSWORD`, with `.env.example` as the template.
- Bound PostgreSQL exclusively to `127.0.0.1` in the Docker Compose port mapping.
- Dropped a hardcoded test credential from the recurrence service and ported the query to `string_agg`.
- Removed a sensitive evidence folder from git tracking.

### Data

- **Corpus:** 1,741 samples, 6,792 parameter readings across 10 scored BIS IS 10500 parameters, extracted from WQMIS lab reports Aug–Sep 2026 and verified against Form WQ6 (75 UP + 38 Bihar districts).
- **Lab-ID resolution:** 302 of 354 missing districts resolved (85.3%) via 20 lab IDs using the ASP.NET session cookie handshake; only 52 samples (2.99%) held back for multi-district regional lab L158.
- **Village coverage:** 305 of 1,741 samples (17.52%) now carry named village/habitation locations, up from 21 samples — a 1,352% gain.
- **Current headline results:** 113/113 districts scored; 46 Critical, 27 High, 19 Medium, 21 Low; 32 pathogen overrides (E. coli); 13 arsenic escalations.

[Unreleased]: https://github.com/anubhavaanand/water-triage/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/anubhavaanand/water-triage/releases/tag/v0.1.0