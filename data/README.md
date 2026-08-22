# Data Directory — Layout Contract

> For any agent: all acquired data lives here. Never commit bulk files (gitignored);
> READMEs and small manifests are versioned.

```
data/
├── raw/
│   ├── wqmis/            WQMIS (ejalshakti.gov.in) individual lab reports
│   │   ├── *.html        cached report pages (bulk, gitignored)
│   │   ├── records.jsonl one JSON record per parsed sample (append-only)
│   │   └── crawl_progress.txt  internal ids already processed
│   ├── kaggle/           third-party Kaggle datasets (CSV, gitignored if large)
│   ├── imis/             IMISReports aggregate tables (state/GP-wise testing)
│   └── aikosh/           AIKosh village-level CSV (when access granted)
└── processed/            cleaned, schema-aligned parquet/csv ready for DB load
```

## Sources

| Dir | Source | Access | Status |
|-----|--------|--------|--------|
| raw/wqmis | `ejalshakti.gov.in/WQMIS/Common/final_report_print?s_id=AES(id)` | public, sequential ids, AES-128 key `8080808080808080` | ✅ crawler live (`backend/etl/wqmis.py`) |
| raw/imis | `ejalshakti.gov.in/IMISReports/Reports/WaterQuality/rpt_WQM_GPwiseTesting_*.aspx` | public pages | 🔍 probing |
| raw/kaggle | kaggle.com/datasets/rishabchitloor/indian-water-quality-data-2021-2023 | kagglehub | see raw/kaggle/README.md |
| raw/aikosh | AIKosh portal dataset | pending approval | ⏳ |

## records.jsonl schema (one line per WQMIS sample)

```json
{"wqmis_sample_id": "U695645L661S1", "internal_id": 123, "state": "Uttar Pradesh",
 "district": "Baghpat", "block": null, "village": "Gauna", "gram_panchayat": null,
 "source": "Hand Pump", "collected_on": "2022-08-10T00:00:00",
 "lab": "...", "results": [{"parameter": "...", "unit": "...",
 "acceptable": 1.0, "permissible": 1.5, "value": 0.4}]}
```

## Loading into the database

```bash
cd backend && uv run python -m etl.load_data          # synthetic demo
# wqmis jsonl -> db loader lands in etl/load_wqmis.py once volume justifies it
```
