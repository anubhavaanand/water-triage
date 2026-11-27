# Benchmarks & Methodology

Measured 2026-11-27 by `benchmarks/run_bench.py` on the committed corpus.
Machine-readable receipt: [`results.json`](results.json). Re-run with:

```sh
python3 benchmarks/run_bench.py
```

## Dataset (MEASURED)

| Metric | Value | Source |
|---|---|---|
| Records in `data/raw/wqmis/records.jsonl` | **1,822** | counted |
| Unique WQMIS sample IDs | **1,822** | counted |
| Enriched records | **1,822** | counted |
| Parameter readings | **11,779** | summed across records |
| Distinct districts present in raw records | **57** | counted |
| States | Uttar Pradesh, Bihar | counted |

### District / lab-ID resolution (MEASURED)

| Resolution path | Records |
|---|---|
| `submitter_address` (already resolved) | 1,444 |
| Resolved via lab probe (`aspnet_session_lab_probe`, `single_district_lab`) | **305** |
| Held back, multi-district regional lab | 73 |
| **Resolution rate over the unresolved pool** | **80.7% (305/378)** |

## Scoring outputs (MEASURED)

| File | Rows |
|---|---|
| `WQ6_Complete_UP.csv` | 75 |
| `WQ6_Complete_Bihar.csv` | 38 |
| `Full_113_District_Risk_Triage.csv` | **113** |

The 113-district figure is confirmed: 75 UP + 38 Bihar.

## Query timing — **BLOCKED**

Not measured in this environment: no PostgreSQL reachable, no `DATABASE_URL`,
no Docker daemon. Recorded as `BLOCKED` in `results.json` rather than estimated.

- `set_based_group_by` — `BLOCKED` (no database)
- `n_plus_one_baseline` — `BLOCKED` (the legacy per-row query path is not present
  in the current codebase, so there is nothing to time)

**Note:** the widely-quoted "37 s → 0.58 s (63×)" figure does **not** appear in
this repository's README and has no supporting artifact. It should not be cited
until it is re-measured against a restored N+1 implementation.

## Corrections to previously published claims

| Previously stated | Measured | Verdict |
|---|---|---|
| 1,741 samples | **1,822** | understated by 81 |
| 6,792 parameter readings | **11,779** | understated by 4,987 |
| 85.3% lab-ID resolution | **80.7%** | overstated by 4.6 pts |
| 113 districts scored | **113** | confirmed |
