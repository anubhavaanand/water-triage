# Kaggle Datasets — Local Catalog

> Downloaded via kagglehub into this folder. Bulk CSVs are gitignored (kept local);
> this README + row counts are the versioned source of truth.

## affected_areas_2009_2012 / IndiaAffectedWaterQualityAreas.csv ⭐ CORE

Government registry of **quality-affected habitations**, village-level.
550,242 rows × 8 cols · Years 2009–2012 · encoding latin-1.

Columns: `State Name, District Name, Block Name, Panchayat Name, Village Name,
Habitation Name, Quality Parameter, Year` (names carry LGD codes in parens).

**UP+Bihar subset = 102,254 rows:**

| State | Rows | Districts | Dominant parameter |
|-------|------|-----------|--------------------|
| Bihar | 92,336 | 38→28 present | Iron (73K overall), Fluoride |
| Uttar Pradesh | 9,918 | 65 | Fluoride, Arsenic, Salinity |

Parameters overall: Iron 73,346 · Fluoride 18,796 · Arsenic 8,284 · Salinity 1,808 · Nitrate 20

Uses: (1) historical validation layer for triage scores, (2) village-name dictionary
for fuzzy-matching WQMIS pulls, (3) WPR-5 baseline maps.

## iwq_2021_2023 / Indian_water_data.csv

CPCB monitoring-station data, 17 states, years 2021–2023. Station-level surface-water
quality (Temp, DO, pH, Conductivity, …). Not village-level; use for context/WPR only.

## historical_avg / water_dataX.csv

Legacy CPCB station averages: STATION CODE, LOCATIONS, STATE, Temp, D.O., pH,
Conductivity, B.O.D., Nitrate+Nitrite, Fecal/Total Coliform, year. Surface-water focus;
coliform columns useful as historical microbiology reference.

## NOT yet pulled (tracked)

- `amandeepdutta/india-s-ground-water-quality-statewise` (2012–2021 groundwater statewise) — fetch next
- AIKosh JJM Water Source Water Quality Data — access still pending
