# Literature Review Research Notes — WPR-4 (Related Work)

> Compiled 17 Aug 2026 · Feeds WPR-4 "Related Work / Literature Review"
> All sources verified via Firecrawl Research (PubMed/paper index) and web search.

---

## 1. Water Quality Index Methods (scoring foundation)

WaterTriage's scoring engine is a **weighted arithmetic WQI** adapted for triage. Key literature:

| Source | Relevance |
|--------|-----------|
| **Groundwater quality assessment using weighted arithmetic index method** — Butchayyapeta Mandal, Visakhapatnam, AP (PMID: 34633550) | Direct methodological precedent: 10 physicochemical parameters → weighted arithmetic WQI for village-level groundwater |
| **Standard and AHP-based WQI at MSW landfill, Ranchi, Jharkhand** (PMID: 27155859) | Shows WQI coupling with Analytical Hierarchy Process — supports our health-based weight assignment (As 1.0 > E.coli 0.9 > F⁻ 0.8 …) |
| **Integrating WQI, GIS and multivariate statistics** (PMC8989949) | Compares weighted arithmetic vs entropy-weighted WQI; justifies choice of weighted arithmetic for interpretability in policy contexts |
| **Entropy-weights in water quality indexing: ambiguities and proposal** (PMID: 34043163) | Critique of data-driven weighting; argues expert/standard-driven weights remain defensible — backs our BIS-derived severity bands |
| **Piped water supply assessment using WQI method** (PMC12618970) | ~10 parameters tested via weighted arithmetic WQI on *piped* systems — closest to JJM supply context |

**Takeaway for WPR-4:** Weighted arithmetic WQI is the dominant, policy-legible method in Indian groundwater studies; our innovation is applying it as a *relative triage score* (0–100 bands) rather than an absolute quality class.

## 2. Jal Jeevan Mission / WQMIS Context

| Source | Relevance |
|--------|-----------|
| **JJM-WQMIS portal** (ejalshakti.gov.in/WQMIS) | Official data source: lab + FTK test records, village-level; our primary data pipeline |
| **Drinking Water Quality Monitoring & Surveillance Framework** (PIB PRID 1910082; MJWS) | Mandates FTK + lab testing frequency per habitation — explains data availability & gaps our ETL must handle |
| **Access to safe drinking water, Etawah district, UP** (PMC10652157) | Cross-sectional JJM-era study: physical/chemical quality of tap water in a UP district — comparable geography |
| **In-line chlorination RCT, rural Odisha** (medRxiv 2025.07.10.25331308) | Documents intermittent, untreated supply post-JJM — motivates why monitoring + prioritization matters |
| **Rural drinking water supply & societal development: early JJM evidence** (PMC11581310) | JJM implementation review — background for Introduction recap in WPR-4 |
| **Risk assessment & water safety planning, Uttarakhand** (PMID: 34773150) | WHO Water Safety Plan applied to rural Indian utilities — adjacent framework; we automate the *prioritization* step WSPs do manually |
| **Microbial monitoring tool selection for rural communities** (PMID: 37804981) | Tiered microbial testing feasibility — context for E. coli data reliability in WQMIS |

## 3. ML / Data-Driven Contamination Assessment (related computational work)

| Source | Relevance |
|--------|-----------|
| **Groundwater quality assessment in Bihar's aquifers: a machine learning approach** (PMID: 42189468) | ⭐ Closest prior work: state-scale Bihar groundwater, WQI + RMS-WQI comparison. Cite and differentiate: they *assess*, we *prioritize intervention* |
| **Arsenic contamination ML classification, Varanasi, UP** (wh_2022_015) | Indo-Gangetic arsenic safe/unsafe classification — our Hardoi/UP districts overlap this risk zone |
| **Predicting groundwater arsenic: regions at risk in highest populated state of India** (PMID: 31078753) | UP-wide arsenic risk mapping (~100M people exposed nationally) — motivation statistic |
| **Siamese transfer learning for geogenic contamination** (PMID: 35816418) | Handles class-imbalanced contamination data — future work direction for WaterTriage prediction module |
| **Stacking ensemble As/F⁻ prediction, North China Plain** (PMID: 38824797) | Shows env-factor-based prediction is mature internationally; gap: none operationalize it as an *intervention queue* |
| **Data-mining vulnerability assessment, Indo-Gangetic Plain** (PMID: 35772277) | IGP-specific vulnerability framing — matches our UP+Bihar study area justification |

## 4. Prioritization / Decision-Support Systems (the triage gap)

| Source | Relevance |
|--------|-----------|
| **Water Access Index (WAI), Brazilian semi-arid** (PMID: 35092461) | ⭐ Precedent for index-*driven intervention targeting*: "decision-makers can identify and prioritize areas needing state intervention" — same goal, different domain/data |
| **Decision support tool for placing drinking water sources** (PMID: 35398131) | Spatial DSS for rural water placement — shows DSS genre in rural WASH |
| **Bayesian Belief Network decision model, Solomon Islands** (PMID: 31986388) | Data-poor rural decision support — parallels our synthetic-data fallback strategy |
| **Synthetic index for rural drinking water quality of service** (PMID: 31276915) | Argues infrastructure presence ≠ service quality; composite indices needed — philosophical anchor for our composite score |
| **Multicriteria analysis for rainwater harvesting selection** (PMC11219541) | MCDA in rural water tech selection — methodology cousin of our weighted scoring |

## 5. Standards Basis

- **BIS IS 10500:2012** — acceptable vs permissible limits used verbatim in our `bis_limits` table:
  - Fluoride: acceptable 1.0 mg/L, permissible 1.5 mg/L (confirmed by PMID: 22049700)
  - Heavy metals exceedance framing confirmed by tribal-region central India study (PMID: 42501124 — Pb/Cd up to 33× limits)
  - WHO 1984 fluoride guideline 1.5 mg/L historical alignment (PMID: 17915775)

## 6. Existing Dashboards / Tools (gap analysis)

- RS-WaterQuality Mapper (QGIS plugin, PMC12996000) — remote-sensing, surface-water focused; not consumption-point triage
- Esri/ArcGIS Ganga monitoring dashboards — commercial, pollution-source monitoring, not rural supply
- WQDV open-source regional viewer (MDPI Hydrology 8(2):91) — visualization-only; no scoring or prioritization
- **Gap:** No open system combines WQMIS-sourced village data → BIS-based severity scoring → ranked intervention queue → public dashboard for UP/Bihar.

## 7. Gap Statement (for WPR-4 closing paragraph)

Existing literature offers (a) mature WQI methods, (b) state-scale ML assessment (incl. Bihar), and (c) general water-access DSS — but no operational, open-source pipeline that converts routine government surveillance data (WQMIS) into a *severity-ranked intervention queue* at village level for the Indo-Gangetic states. WaterTriage fills exactly this gap.

---

## How this maps to the build

| System component | Backed by |
|------------------|-----------|
| `scoring.py` weighted severity | §1 (weighted arithmetic WQI lineage) |
| Health weights (As 1.0 … pH 0.2) | §1 AHP precedent + §5 BIS limits |
| Severity bands Critical≥75…Low<25 | §1 policy-legible classing + §4 index-driven targeting |
| ETL from WQMIS | §2 framework docs |
| Priority queue `/api/priority` | §4 WAI/DSS precedents |
| Future ML prediction module | §3 (roadmap item in Discussion/WPR-7) |

## Citation list (quick copy)

1. PMID 34633550 — Weighted arithmetic WQI, Visakhapatnam villages
2. PMID 27155859 — AHP-coupled WQI, Ranchi
3. PMC8989949 — WQI + GIS + multivariate integration
4. PMID 34043163 — Entropy-weight critique
5. PMC12618970 — Piped-supply WQI
6. PMC10652157 — Etawah (UP) JJM water access
7. medRxiv 2025.07.10.25331308 — In-line chlorination RCT, Odisha
8. PMC11581310 — JJM early implementation evidence
9. PMID 34773150 — Water Safety Plan, Uttarakhand
10. PMID 37804981 — Microbial tool selection, rural
11. PMID 42189468 — ⭐ Bihar aquifers ML WQI
12. wh_2022_015 — Varanasi (UP) arsenic ML
13. PMID 31078753 — UP arsenic risk prediction
14. PMID 35816418 — Siamese transfer learning, geogenic
15. PMID 38824797 — Stacking ensemble As/F⁻, N. China
16. PMID 35772277 — IGP vulnerability data-mining
17. PMID 35092461 — ⭐ Water Access Index, Brazil
18. PMID 35398131 — DSS source placement
19. PMID 31986388 — BBN decision support, Solomons
20. PMID 31276915 — Rural QoS synthetic index
21. PMC11219541 — MCDA RWHS selection
22. PMID 22049700 — BIS 10500 fluoride limits confirmation
23. PMID 42501124 — Heavy metals vs BIS 10500:2012
24. PMID 17915775 — Fluoride health impacts/history
25. PMC12996000 — RS-WaterQuality Mapper
26. MDPI Hydrology 8(2):91 — WQDV viewer
