# AMITY SCHOOL OF ENGINEERING & TECHNOLOGY
**Amity University Uttar Pradesh, Greater Noida**  
**Minor Project (ETMN100)**  
**WEEKLY PROGRESS REPORT (WPR) – 7**

**For the week commencing:** 31/08/2026 – 06/09/2026  
**Enrollment Number:** A41105223039  
**Student Name:** Anubhav Anand  
**Program:** B.Tech CSE  
**Faculty Guide's Name:** Dr. Girish Paliwal  
**Project Title:** WaterTriage: A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar  

---

## Discussion

### 5.1 Hydrochemical Characterization and the Regional Divide
The empirical results produced across the verified WaterTriage database—comprising 1,245 scored live laboratory reports and 100,690 historical contamination events across 14,044 habitations—substantiate a fundamental hydrogeochemical bifurcation across the Indo-Gangetic plain. Rather than exhibiting uniform contamination patterns, the upper/middle basin (Uttar Pradesh) and lower alluvial floodplain (Bihar) are governed by distinct lithological formations, flow velocities, and anthropogenic pressure gradients. Table 1 synthesizes this verified regional contrast based on live database queries.

**Table 1: State-Level Severity Band & Hydrochemical Comparison**
| Hydrochemical Metric / Determinant | Uttar Pradesh (Upper/Middle Plain) | Bihar (Lower Alluvial Floodplain) |
| :--- | :---: | :---: |
| **Live Sample Distribution** | **687 samples (55.2%)** | **558 samples (44.8%)** |
| **Mean Composite Risk Score (CRS)** | **14.51 ± 17.52 (High Multi-Parameter Load)** | **9.34 ± 17.67 (Heavy Metal Dominance)** |
| **Severity Profile (Critical / High / Med / Low)** | **6 Critical (0.9%) \| 318 High \| 11 Med \| 352 Low** | **8 Critical (1.4%) \| 144 High \| 0 Med \| 406 Low** |
| **Dominant Chemical Exceedances** | Turbidity (395), TDS (210), Fe (130), F⁻ (94), NO₃⁻ (8) | Iron (93), Turbidity (86), TDS (42), F⁻ (1) |
| **Acute Microbial Detections (E. coli)** | 2 samples (Lucknow: U691097, U695845) | 0 live samples (Historical riverine vulnerability) |

In Uttar Pradesh, contamination exhibits a dual origin: geogenic mineral leaching combined with non-point agricultural and domestic runoff. In central districts such as Unnao and Firozabad, geogenic Fluoride frequently exceeds 1.5 mg/L (averaging 1.73 mg/L with spikes up to 12.6 mg/L in Agra), driven by fluorite weathering in granitic basement rocks. Concurrently, agricultural runoff drives groundwater Nitrate well beyond the 45 mg/L BIS limit (averaging 49.82 mg/L). Conversely, Bihar’s groundwater is governed by reducing alluvial hydrochemistry in Holocene aquifers. Dissolved Iron exceedances are pervasive across North Bihar (Purnia, Katihar, Madhepura), while geogenic Arsenic clusters along the active Ganga meander belt (Buxar, Bhojpur, Bhagalpur) due to reductive dissolution of iron oxyhydroxides.

### 5.2 Mathematical Validation of the Acute Hazard Escalation Rule
A central algorithmic contribution of WaterTriage is its departure from conventional weighted arithmetic Water Quality Index (WQI) formulations (Horton, 1965; Brown et al., 1970). Standard arithmetic models suffer from the well-documented "eclipsing" or dilution anomaly (Ott, 1978; Swamee & Tyagi, 2000): when a sample contains a lethal concentration of a single acute toxin alongside several pristine physical parameters (neutral pH, low turbidity, moderate TDS), linear averaging dilutes the lethal breach, falsely classifying dangerous water as "Good" or "Moderate". In public health triage, such false-negative classifications expose rural populations to severe toxicity.

The WaterTriage engine resolves this anomaly via an explicit non-linear Escalation Invariant in `backend/app/engine/scoring.py`. Any sample detecting E. coli (> 0 CFU/100mL) or acute Arsenic (≥ 0.05 mg/L) is automatically escalated to the Critical band (floor index 3), regardless of its arithmetic score. Empirically, in sample `U691097L158S1903` (Lucknow, UP), the arithmetic composite score was only 24.35 (Low band) due to benign physical parameters; however, the escalation engine classified it as Critical due to confirmed E. coli contamination. Across the live database, this invariant successfully prevented false-negative dilution across all acute pathogen and severe chemical breaches.

### 5.3 Temporal Recurrence Dynamics and Aquifer Vulnerability
Cross-sectional water testing captures only an instantaneous snapshot, frequently failing to distinguish between transient surface ingress and chronic hydrogeological aquifer failure. Running the WaterTriage recurrence engine across 100,690 historical quality-affected habitation events (2009–2012) resolved this diagnostic gap. The most prominent manifestation is Khokha village in Purnia district, Bihar (Village ID 7568), which logged 166 distinct Iron exceedances across every single observation year (2009, 2010, 2011, and 2012). It represents the single most contaminated habitation in the entire national historical repository. While single-sample indexes treat Iron as an aesthetic issue (w = 0.4), 166 persistent failures definitively demonstrate systemic regional aquifer oxidation.

This longitudinal finding carries direct engineering consequences: conventional administrative remediation consists of re-drilling shallow handpumps in adjacent locations within the same village. In chronically recurring geogenic zones like Khokha and central UP (where Fluoride recurrence exceeds 65% in Unnao and Firozabad), shallow re-boring simply taps into the same contaminated hydrostratigraphic unit, squandering public funds. Longitudinal triage dictates that these habitations bypass piecemeal handpump repairs in favor of deep confined aquifer bores (> 180 m) fitted with sanitary grout seals, or integration into centralized Multi-Village Piped Water Supply Schemes (MVS).

### 5.4 Targeted Intervention Strategies and Policy Feasibility
To operationalize data science for field engineers under the Jal Jeevan Mission (JJM), WaterTriage translates composite scores into a hierarchical intervention matrix balancing capital expenditure (CapEx), operational maintenance (OpEx), and institutional feasibility across four distinct contamination archetypes:

**Table 2: Actionable JJM Intervention Matrix by Contamination Archetype**
| Contaminant Archetype | Recommended Engineering Solution | Cost Profile | Institutional Lead |
| :--- | :--- | :--- | :--- |
| **Acute Microbial (E. coli > 0)** | Inline electro-chlorination units; wellhead sanitary apron sealing | Low CapEx / Low OpEx | Gram Panchayat & VWSC Chlorination Drive |
| **Geogenic Fluoride (F⁻ > 1.5 mg/L)** | Community Activated Alumina Defluoridation or CSIR-NEERI Nalgonda plants | Medium CapEx / Moderate OpEx | PHED Subdivision Engineering Office |
| **Dissolved Iron (Fe > 1.0 mg/L)** | Handpump-attachable Aeration-Sedimentation-Filtration (IRP) gravity sand filters | Low CapEx / Very Low OpEx | Village Paani Samiti local backwashing |
| **Geogenic Arsenic (As ≥ 0.05 mg/L)** | Immediate well capping; transition to piped surface water (MVS) schemes | High CapEx / High OpEx | State Water & Sanitation Mission (SWSM) |

### 5.5 Methodological Limitations and Threats to Validity
Honest methodological caveats must be acknowledged. First, the 1,245 live laboratory samples analyzed represent an empirical sample extracted across targeted identifier ranges rather than a spatially uniform census of all rural water sources in Uttar Pradesh and Bihar; district-level sample densities reflect crawler coverage rather than absolute population vulnerability. Second, temporal discontinuity exists between the historical registry (2009–2012) and current WQMIS testing (2022–2026), meaning historical recurrence flags long-term hydrogeological vulnerability rather than real-time daily contamination. Third, geocoding for rural habitations currently relies on administrative hierarchy matching rather than precise GPS coordinates, introducing spatial approximation in choropleth displays. In Week 8 and beyond, integrating spatial Kriging and geospatial random forest interpolation will address these coverage gaps by estimating unmonitored habitations between known test clusters.
