# Master Data Catalog — WaterTriage

> All sources evaluated for the project, with status. Local copies under `data/raw/`.
> Project needs: village/habitation-level, UP+Bihar, BIS-10500 params (As/F/NO3/Fe/turbidity/E.coli/TDS/pH), multi-year 2022–2025 for recurrence scoring.

## TIER 1 — In hand, core to the build

| # | Dataset | What it gives | UP+Bihar coverage | Location |
|---|---------|---------------|-------------------|----------|
| 1 | **WQMIS individual lab reports** (live crawler) | Real test readings + BIS limits per sample; sequential public IDs (20M+ space) | ✅ live pulls working (UP verified) | `data/raw/wqmis/` |
| 2 | **Quality-Affected Habitations registry** (Kaggle mirror of data.gov.in catalog) | 550K rows of village→habitation contamination records by parameter, 2009–2012. **102,254 UP+Bihar rows** (Bihar 92K iron-dominated / UP 10K fluoride+arsenic, 65 districts) | ✅ full | `data/raw/kaggle/affected_areas_2009_2012/` |
| 3 | **India Ground Water Quality Statewise 2012–2021** (Kaggle/amandeepdutta) | Year-wise CSVs 2012–2021, state groundwater quality w/ pH, conductivity nodes | 🔍 inspecting | `data/raw/kaggle/gw_quality_2012_2021/` |
| 4 | Synthetic generator (`etl/synthetic.py`) | 114-sample demo across signature districts for dev/demo | ✅ | in-repo |

## TIER 2 — Verified sources, queued for integration

| # | Source | What it adds | How |
|---|--------|--------------|-----|
| 5 | **CGWB Ground Water Quality annual reports** 2019–2023 (cgwb.gov.in/en/ground-water-quality) | National hydrograph-surveillance quality PDFs incl. nitrate-exceedance maps; official citations for WPRs | download PDFs → cite + extract state tables |
| 6 | **India-WRIS GWQuality portal** (indiawris.gov.in/wris/#/GWQuality) | Interactive groundwater quality queries; CGWB station data free download | manual export or WRIS API |
| 7 | **NWDP Village Boundaries** (nwdp.nwic.gov.in/dataset/village-boundary) | Village polygon shapefiles/GeoJSON — geo-join layer for the map dashboard | direct download |
| 8 | **WQMIS lab_parameterlist** pages (public, st_id=31=UP) | Lab infrastructure per district (context metadata) | scrape when needed |
| 9 | **IMISReports GP-wise testing pages** (rpt_WQM_GPwiseTesting_S/D.aspx) | Aggregate lab-vs-FTK testing counts per GP/state — validation totals | ReportViewer POST flow (pending) |

## TIER 3 — Pending / dead ends (do not spend more time)

| Source | Status |
|--------|--------|
| AIKosh JJM Water Source Water Quality CSV | ⏳ access approval pending (weeks) — keep chasing, it's the exact target schema |
| data.gov.in "Water Quality Affected Habitations" catalog page | ☠️ archived/empty SPA; Kaggle mirror (#2) is canonical |
| data.gov.in CKAN/API for water quality | ☠️ requires paid API key; group page empty |
| Public User role on WQMIS | ☠️ submission-only, cannot read report APIs |
| Kaggle iwq_2021_2023 + historical_avg (CPCB surface water) | ⚠️ downloaded; surface-water focus — context/WPR only, not triage core |

## Coverage vs. project requirements

| Requirement | Met by |
|-------------|--------|
| Village-level UP+Bihar | #1 (current), #2 (historical) |
| Multi-year recurrence (2022–2025) | #1 crawler (multi-FY ids) + #3 bridge decade |
| All 8 BIS parameters incl. E.coli | #1 full set; #2 categorical (Iron/Fluoride/Arsenic/Salinity/Nitrate) |
| Ground-truth validation | #2 = govt's own affected list; IMIS aggregates (#9) |
| Geo layer for dashboard | #7 village boundaries |

**Verdict:** data foundation is sufficient to complete the project without AIKosh; treat AIKosh as a bonus upgrade when approved.
