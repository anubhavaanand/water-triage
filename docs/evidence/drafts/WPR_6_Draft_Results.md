# AMITY SCHOOL OF ENGINEERING & TECHNOLOGY
**Amity University Uttar Pradesh, Greater Noida**  
**Minor Project (ETMN100)**  
**WEEKLY PROGRESS REPORT (WPR) – 6**

**For the week commencing:** 24/08/2026 – 30/08/2026  
**Enrollment Number:** A41105223039  
**Student Name:** Anubhav Anand  
**Program:** B.Tech CSE  
**Faculty Guide's Name:** Dr. Girish Paliwal  
**Project Title:** WaterTriage: A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar  

---

# Results

### 4.1 Data Volume and Coverage
Table 1 summarises the data processed by the system as of this reporting period. The live WQMIS crawler has retrieved 822 raw public records, yielding 755 verified and scored individual laboratory reports across Uttar Pradesh (511 samples) and Bihar (311 samples) to date, containing 3,124 discrete chemical and bacteriological parameter readings evaluated against BIS IS 10500 limits. In the active dashboard snapshot, this is represented by 869 scored samples across 43 districts. While this reflects a significant expansion beyond the initial 112-sample exploratory crawl, it remains a partial sample rather than exhaustive state coverage across all WQMIS identifier ranges. The supplementary historical contamination registry provides substantially broader longitudinal coverage, contributing 100,690 quality-affected habitation events across 14,044 tracked villages for the 2009–2012 period, forming the primary basis for the recurrence analysis in Section 4.3.

**Table 1: Data Volume and Engineering Metrics**
| Metric | Value |
| :--- | :--- |
| **Live WQMIS samples retrieved and scored** | 755 (UP: 511, Bihar: 311; 869 in console snapshot) |
| **Discrete BIS parameter readings evaluated** | 3,124 |
| **Historical contamination registry events loaded (2009–2012)** | 100,690 |
| **Villages tracked in geographic hierarchy** | 14,044 |
| **Districts represented in database hierarchy** | 99 |
| **Automated test cases passing** | 26 / 26 (PostgreSQL) |
| **REST API endpoints exposed** | 9 |
| **Recurrence-query optimisation** | 37 s → 0.58 s (identical output) |

---

### 4.2 Contamination Severity Findings
Applying the BIS 10500-based scoring engine (Section 3.3) across the retrieved live samples surfaced a verified severity distribution: 22 samples in the Critical band (2.5%), 323 samples in the High band (37.2%), and 515 samples in the Low/Safe band (59.3%). 

Under the band-escalation rule, any sample returning an acute microbiological detection (E. coli > 0 MPN/100mL) or severe geogenic Arsenic (≥ 0.05 mg/L) is classified as Critical irrespective of its composite numeric score, consistent with the rule's intent of not allowing an acute microbiological or toxic hazard to be diluted by unaffected parameters in the same report. Samples from Lucknow and Hardoi in Uttar Pradesh exhibited verified microbiological breaches, while Ballia and Buxar demonstrated severe geogenic Arsenic exceedances along the active Gangetic floodplains. High-band samples were primarily driven by geogenic Fluoride in central Uttar Pradesh (Unnao and Firozabad) and elevated agricultural Nitrate concentrations.

---

### 4.3 Recurrence and Chronic Hotspot Findings
The recurrence detection module was run against the full 100,690-event historical registry to classify village-parameter combinations into the four verdict categories defined in Section 3.4 (chronic-hotspot, recurring, watchlist, no-history). Among the results produced, the village of Khokha in Purnia district, Bihar, was confirmed as a chronic-hotspot for iron contamination, with 166 recorded exceedance events across the historical registry period — the type of result the recurrence module is specifically designed to surface, since a single-reading severity score alone would not distinguish this village from one with a single isolated iron exceedance. Similarly, shallow aquifers across Unnao and Firozabad in Uttar Pradesh exhibited over 65% multi-year recurrence rates for geogenic Fluoride, confirming permanent aquifer contamination that requires centralized piped water rather than repeated handpump re-boring. A full quantitative breakdown of verdict-category counts across all 14,044 villages is planned as an extension of this analysis in the final report.

---

### 4.4 Comparative Observations (Uttar Pradesh vs. Bihar)
The district-level spatial view across both states allows visual and statistical comparison of sample density and contamination severity by state. The expanded dataset confirms distinct hydrochemical patterns between the two regions:
* **Bihar:** Heavily skewed toward geogenic heavy metals and sediment-linked parameters. The lower Indo-Gangetic plain (Bhagalpur, Katihar, Purnia) exhibits widespread dissolved Iron exceedances (> 2.5 mg/L vs. permissible limit of 1.0 mg/L) and localized Arsenic contamination along active river channels.
* **Uttar Pradesh:** Exhibits a dual challenge of geogenic Fluoride and salinity in central industrial districts (Unnao, Firozabad) combined with intensive agricultural Nitrate pollution (NO₃ > 45 mg/L) and surface microbial contamination in shallow open aquifers.

---

### 4.5 System Performance and Validation Results
All twenty-six automated test cases pass in 3.00 seconds against a live Dockerized PostgreSQL container (jjm_triage), covering scoring correctness, API contract behaviour, WQMIS parser edge cases, and recurrence logic including a PostgreSQL integration suite. The nine REST endpoints and the browser-based 3D console (deployed on port 3000) were verified to function correctly against both the live and offline-snapshot data paths. The recurrence-ranking performance issue identified during development was resolved, reducing execution time from approximately 37 seconds to 0.58 seconds across the full 14,044-village set, with output verified identical to the original implementation via regression tests.
