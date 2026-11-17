# WaterTriage API Reference

Base URL: `http://localhost:8000`

All application endpoints are served under the `/api` prefix. Every router is mounted in `backend/app/main.py`, and FastAPI's auto-generated schema is always available.

## Interactive documentation

| URL | What it is |
|---|---|
| `/docs` | Swagger UI — browse and call every endpoint with a real request |
| `/redoc` | ReDoc — read-only reference rendering of the same schema |
| `/openapi.json` | Machine-readable OpenAPI 3.1 schema |

These routes exist in every environment because FastAPI registers them by default; `docs_url`, `redoc_url`, and `openapi_url` are not overridden in `backend/app/main.py`. In production the dashboard is served from `/`, and `/docs` remains reachable at the same origin (for example `https://water-triage.onrender.com/docs`).

```bash
uv run uvicorn backend.app.main:app --port 8000
# then open http://localhost:8000/docs
```

To regenerate a static copy of the schema:

```bash
uv run python -c "import json, backend.app.main as m; open('docs/openapi.json','w').write(json.dumps(m.app.openapi(), indent=2))"
```

## Conventions

- **Responses are JSON** unless stated otherwise.
- **Not found** returns `404` with `{"detail": "<message>"}`.
- **Validation errors** return `422` with FastAPI's standard error body.
- **No authentication.** The API is read-only and open (`CORS allow_origins=["*"]`). The only mutating route is `POST /api/scoring/recompute`.
- **Offline mode.** If the database is unreachable, the app still starts and most endpoints fall back to the bundled JSON snapshots; `/api/meta` returns reduced data rather than failing.

## Endpoints

### Samples

#### `GET /api/samples`

List water samples with their risk scores, newest first.

| Query | Type | Default | Notes |
|---|---|---|---|
| `district` | string | — | Case-insensitive partial match on district name |
| `band` | string | — | `Critical`, `High`, `Medium`, or `Low` |
| `limit` | int | `50` | Maximum `500` |
| `offset` | int | `0` | Pagination |

```bash
curl "http://localhost:8000/api/samples?district=Unnao&band=critical&limit=5"
```

```json
[
  {
    "id": 1612,
    "village": "Bangarmau",
    "district": "Unnao",
    "state": "Uttar Pradesh",
    "source_type": "wqmis_wq4",
    "collected_on": "2022-09-14T00:00:00",
    "wqmis_ref": "UP-2022-09-14-1612"
  }
]
```

#### `GET /api/samples/{sample_id}`

Return one sample with all parameter readings and its computed risk score.

```bash
curl "http://localhost:8000/api/samples/1612"
```

```json
{
  "id": 1612,
  "village": "Bangarmau",
  "district": "Unnao",
  "state": "Uttar Pradesh",
  "source_type": "wqmis_wq4",
  "collected_on": "2022-09-14T00:00:00",
  "wqmis_ref": "UP-2022-09-14-1612",
  "readings": [
    { "parameter_key": "fluoride", "value": 3.2, "unit": "mg/L", "label": null },
    { "parameter_key": "ph", "value": 7.8, "unit": "none", "label": null }
  ],
  "risk_score": {
    "score": 58.33,
    "band": "Critical",
    "worst_parameter": "fluoride",
    "n_scored_params": 2,
    "computed_at": "2026-10-09T11:20:04"
  }
}
```

`404` if the sample does not exist.

### Geography

#### `GET /api/states`

Returns the list of state names present in the corpus.

```json
["Bihar", "Uttar Pradesh"]
```

#### `GET /api/districts`

Returns every district with its data-quality tier and band distribution. This route takes **no** query parameters.

```json
[
  {
    "id": 12,
    "name": "Unnao",
    "state_id": 3,
    "state": "Uttar Pradesh",
    "parameter_count": 10,
    "data_quality": "high_coverage",
    "band_counts": { "Critical": 12, "High": 9, "Medium": 8, "Low": 12 }
  }
]
```

> **Duplicate route.** `dashboard.py` and `districts.py` both define `/districts`. Because `dashboard_router` is registered before `districts_router` in `backend/app/api/__init__.py`, the dashboard version above is the one served — it has no `state`/`band` filters. Use `/api/districts/full-triage` or `/api/districts/{id}` for richer or filtered payloads.

#### `GET /api/districts/{district_id}`

Returns district summary plus every village with its latest score and band. `404` if the district does not exist.

#### `GET /api/districts/full-triage`

Returns the complete 113-district (75 UP + 38 Bihar) multi-tier BIS IS 10500 triage payload from `dashboard/public/full-113-triage.json`, regenerating it from `scripts/build_full_113_district_triage.py` if the file is missing.

| Query | Type | Notes |
|---|---|---|
| `state` | string | Filters `districts[]` by state |
| `band` | string | Filters `districts[]` by band |

Unlike the other geography routes, this one reads a prebuilt snapshot and does not require a database.

### Scoring

#### `GET /api/priority`

The full ranked intervention queue — one entry per sample, ordered by band severity then score, with a 1-based `rank`.

| Query | Type | Notes |
|---|---|---|
| `state` | string | Case-insensitive filter |
| `band` | string | Case-insensitive filter |

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

#### `GET /api/priority/top/{n}`

The first `n` entries of the same queue.

```bash
curl "http://localhost:8000/api/priority/top/10"
```

#### `GET /api/scoring/parameters`

The BIS IS 10500 parameter table used by the scoring engine, ordered by key. The dashboard renders its severity bars from this rather than restating the limits, so a change in the engine propagates to the UI.

```json
[
  {
    "key": "arsenic",
    "label": "Arsenic",
    "unit": "mg/L",
    "acceptable": 0.01,
    "permissible": null,
    "weight": 1.0,
    "strategy": "threshold",
    "binary_exceedance": true
  }
]
```

`binary_exceedance` is `true` when there is no permissible uplift (or `permissible <= acceptable`): any exceedance is full severity, and a proportional bar would be misleading.

#### `POST /api/scoring/recompute`

Recomputes `risk_scores` for every sample in the database. This is the only mutating endpoint.

```bash
curl -X POST "http://localhost:8000/api/scoring/recompute"
```

```json
{ "recomputed": 1741 }
```

#### `GET /api/compare`

Per-state aggregate comparison: sample counts, average score, band counts, and the most frequent exceedance parameter.

```json
{
  "states": [
    {
      "state": "Bihar",
      "sample_count": 512,
      "avg_score": 24.81,
      "critical_count": 14,
      "high_count": 9,
      "top_exceedance_parameter": "iron"
    }
  ]
}
```

### Recurrence

#### `GET /api/recurrence/{village_id}`

Historical-versus-current comparison for one village, classifying each parameter as persistent, historical-only, or new, with a recurrence score and verdict.

```json
{
  "village_id": 88,
  "village": "Baraon",
  "district": "Katihar",
  "state": "Bihar",
  "historical": { "iron": [2011, 2012] },
  "current_exceedances": ["iron"],
  "classifications": { "iron": "persistent" },
  "persistent_params": ["iron"],
  "recurrence_score": 0.82,
  "verdict": "chronic"
}
```

`404` if the village does not exist.

#### `GET /api/recurrence`

Returns recurrent districts ranked by chronic hotspot severity.

### Validation

#### `GET /api/validation/cgwb`

CGWB groundwater pH compliance by state and year, the parameters available per state, plus the 113-district WQ6 and master validation ground truth. Falls back to bundled files when the `cgwb_readings` table is empty.

#### `GET /api/validation/districts`

Returns all 113 canonical districts (75 UP + 38 Bihar) with WQMIS, IMIS, and WQ6 counts, plus the WQ6 summary.

### Metadata

#### `GET /api/meta`

The single aggregate payload the dashboard Overview tab consumes: corpus counts, band distribution, per-state comparison, parameter exceedance rates, scoring model weights and escalation rules, declared limitations, and the iron-limit sensitivity run.

| Field | Contents |
|---|---|
| `generated_at`, `git_commit` | Provenance of the payload |
| `corpus` | Samples, readings, distinct historical events, district coverage, village-name coverage, unassigned samples by state |
| `bands` | Sample counts per band |
| `band_thresholds` | `{ "Critical": 40, "High": 20, "Medium": 10, "Low": 0 }` |
| `scoring` | Model name, standard, per-parameter weights, escalation rules |
| `state_comparison[]` | Samples, mean/median score, band counts, zero-score share, per-parameter exceedance rates |
| `top_parameters[]` | Top 15 state/parameter pairs by exceedance count |
| `sensitivity` | Iron-limit sensitivity run (acceptable = 1.0 mg/L) |
| `limitations[]` | Declared limitations with `id`, `title`, `detail`, `status` (`accepted`, `open`, `resolved`) |
| `critical_concentration` | District with the most critical samples, incl. single-parameter iron cases |
| `caveats` | Sampling caveats and the minimum sample count for reporting a mean |

### Dashboard helpers

These back the dashboard shell and require no parameters.

| Endpoint | Returns |
|---|---|
| `GET /api/districts` | Districts with band counts and data-quality tiers |
| `GET /api/districts/coverage` | Coverage summary grouped by data-quality tier |
| `GET /api/health` | Backend health and database connectivity |
| `GET /api/dashboard-data` | Combined payload for the dashboard (districts, bands, meta) |

> The dashboard data contract is generated into `docs/api_meta.json`. If a field the UI needs is missing from the API, regenerate that snapshot rather than hardcoding the value in the frontend.

## Error handling

```json
{ "detail": "sample not found" }
```

FastAPI's default `HTTPException` shape. Client code should treat any non-2xx response as an error and read `detail` for a human-readable message.