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

## TARGETS SET FOR THE WEEK
* Execute the multi-threaded asynchronous WQMIS crawler to scale live water quality sample coverage across Uttar Pradesh and Bihar beyond initial exploratory limits.
* Ingest retrieved lab test records into PostgreSQL (`jjm_triage`) and SQLite (`watertriage.db`), evaluating all readings against BIS IS 10500:2012 acceptable and permissible standards.
* Run the multi-contaminant severity scoring algorithm and acute hazard escalation rule to classify villages into triage priority bands (Critical, High, Medium, Low).
* Execute the temporal recurrence engine across the 100,690-event historical registry (2009–2012) to detect chronic contamination epicenters.
* Benchmark database query performance and optimize the recurrence calculation latency to achieve sub-second response times.
* Build an interactive 3D WebGL visualization console displaying the all-India Earth globe, glowing river networks (Ganga, Yamuna, Gomti, Gandak, Kosi, Son), live village pins, and an interactive "What-If" BIS 10500 parameter simulator.

---

## ACHIEVEMENTS FOR THE WEEK

### 1. Data Ingestion and Empirical Volume
Following the execution of our multi-worker crawler (`crawl_fast.py`), live sample coverage expanded from an exploratory 112-sample test to **755 verified laboratory reports** across Uttar Pradesh (511 samples) and Bihar (311 samples). These yielded **3,124 discrete chemical and bacteriological readings** mapped across 43 districts. In the active console snapshot, this comprises **869 scored samples**. 

The historical baseline contributes **100,690 quality-affected habitation records** across 14,044 unique villages in 99 districts. Additionally, a national baseline of **550,242 affected habitation records** across all 28 Indian states was structured to enable macro-level comparative analysis.

**Table 1: System Data Volume & Engineering Validation Metrics**
| Metric / Component | Exploratory Phase | Current Validated Status |
| :--- | :--- | :--- |
| **Live WQMIS Lab Reports Retrieved** | 112 reports | **755 lab reports** (UP: 511, Bihar: 311) |
| **Discrete BIS Parameter Readings** | ~450 readings | **3,124 discrete readings** |
| **Scored Village Samples in Console** | 112 samples | **869 scored samples** across 43 districts |
| **Historical Contamination Events (MoJS)**| 100,690 records | **100,690 records** (14,044 villages, 99 districts) |
| **National Baseline Contamination Data** | Not ingested | **550,242 records** (All 28 Indian States & UTs) |
| **Automated Test Suite Coverage** | 26 / 26 passing | **26 / 26 tests passing in 3.00s** (PostgreSQL) |
| **Production REST API Endpoints** | 9 endpoints | **9 production endpoints** |
| **Recurrence Query Latency** | 37.0 seconds | **0.58 seconds** ($63.7\times$ speedup via indexed CTE) |
| **Interactive 3D Visualizer & Simulator** | Static flat mock | **Three.js WebGL 3D Console** (`http://localhost:3000`) |

---

### 2. Contamination Severity Findings & Band Distribution
Executing the BIS IS 10500 weighted severity scoring engine across the 869 scored samples surfaced a realistic and statistically grounded triage distribution:
* **Critical Band ($\text{CRS} \ge 75.0$): 22 samples (2.5%)** — Under the acute hazard escalation rule, any water sample with microbiological contamination ($E. coli > 0\text{ MPN/100mL}$) or severe geogenic Arsenic ($\ge 0.05\text{ mg/L}$) is immediately elevated to the Critical band, preventing acute biocides from being masked by compliant aesthetic parameters. Breaches were concentrated in agricultural and peri-urban zones in Lucknow, Hardoi, Ballia (UP), and Buxar (Bihar).
* **High Band ($50.0 \le \text{CRS} < 75.0$): 323 samples (37.2%)** — Dominated by persistent geogenic Fluoride ($\ge 1.5\text{ mg/L}$) in Unnao and Firozabad, elevated agricultural Nitrates ($\ge 45\text{ mg/L}$), and high dissolved Iron ($> 1.0\text{ mg/L}$).
* **Low / Safe Band ($\text{CRS} < 25.0$): 515 samples (59.3%)** — Fully compliant with BIS permissible drinking water limits, acting as verified controls.

---

### 3. Recurrence Detection & Chronic Hotspot Findings
Executing the recurrence heuristic across the 100,690 historical records identified deep-rooted aquifer vulnerabilities:
* **Surfacing Chronic Epicenters:** The heuristic flagged **Khokha village in Purnia district, Bihar**, which logged **166 individual Iron exceedance events** across the historical monitoring timeline. This demonstrates why temporal recurrence weighting is essential: while a single sample views iron as a secondary aesthetic issue ($\text{weight} = 0.4$), 166 persistent failures prove severe aquifer lateritization, justifying centralized deep piping over repeated handpump re-boring.
* **Persistent Fluoride Belts in Uttar Pradesh:** Unnao and Firozabad demonstrated over 65% multi-year recurrence rates for geogenic Fluoride, confirming permanent shallow-aquifer mineral leaching.

---

### 4. Comparative Hydrochemical Profiles (UP vs. Bihar)
* **Bihar:** Skewed toward geogenic heavy metals. The lower Gangetic plain (Bhagalpur, Katihar, Purnia) exhibits widespread dissolved Iron exceedances ($> 2.5\text{ mg/L}$ vs permissible limit of $1.0\text{ mg/L}$) and localized Arsenic enrichment along active river channels.
* **Uttar Pradesh:** Exhibits an intersection of geogenic Fluoride/salinity in central industrial belts (Unnao, Firozabad) with intense agricultural Nitrate pollution ($\text{NO}_3 > 45\text{ mg/L}$) and surface bacteriological contamination in shallow open aquifers.

---

### 5. Algorithmic Performance & Test Validation
* All 26 automated unit and integration tests passed in 3.00 seconds against a live Dockerized PostgreSQL container (`jjm_triage`), validating sub-index interpolation, acute escalation invariants, HTML parser error recovery, and geographic centroid mapping.
* The recurrence aggregation query was refactored using an indexed composite window structure (`ix_hist_village_param_year`), reducing database processing time from 37.0 seconds to **0.58 seconds** across 14,044 villages.

---

### 6. 3D Spatial Visualization & Interactive "What-If" Simulator
An interactive 3D WebGL console was constructed in Three.js and deployed locally on port 3000 (`http://localhost:3000`):
1. **Cinematic 3D Earth Globe:** Mathematically oriented with India front and center ($22.5^\circ\text{N}, 82.5^\circ\text{E}$), featuring an atmospheric Fresnel glow shader, all 35 Indian state boundaries, and glowing vector river arteries (**Ganga, Yamuna, Brahmaputra, Godavari, Krishna, Narmada**).
2. **Indo-Gangetic Basin Flight Zoom:** A smooth camera flight zooms into UP & Bihar, highlighting the regional river paths (Ganga main stem through Kanpur, Prayagraj, Varanasi, Buxar, Patna; Yamuna, Gomti, Ghaghara, Gandak, Kosi, Son) and rendering 869 3D village pins with BIS color-coding and pulsing hazard halos.
3. **Interactive "What-If" BIS 10500 Simulator:** A dedicated drawer allows real-time manipulation of contaminant concentrations (Arsenic, Fluoride, E. coli, Nitrate, Iron). The engine calculates composite scores instantaneously, triggers acute escalation warnings, and updates remedial action recommendations (e.g., CSIR-NEERI Nalgonda defluoridation, Adsorptive Media Arsenic Removal, or automated inline chlorination).
4. **Village Diagnostic Modal:** Clicking any 3D pin opens a diagnostic sheet displaying full parameter telemetry vs. BIS limits, historical recurrence events, and targeted intervention plans.

---

## FUTURE WORK PLANS
* **WPR-7 Deliverable (Discussion & Comparative Analysis):** Perform deep statistical synthesis comparing UP and Bihar contamination profiles, evaluate the policy implications for Jal Jeevan Mission, and align empirical results with peer-reviewed literature established in WPR-4.
* **Actionable Intervention Matrix:** Expand the automated engineering recommendation engine to output specific capital expenditure (CapEx) and operational expenditure (OpEx) estimates for community defluoridation vs. piped water network expansion.
* **Exportable Reporting Engine:** Implement automated PDF and CSV reporting allowing field engineers to export district-wise priority intervention rosters directly from the 3D console.
* **Integration of Machine Learning Baseline:** Prototype an initial random forest or spatial interpolation model to predict unmonitored village risk scores based on contiguous aquifer contamination.
