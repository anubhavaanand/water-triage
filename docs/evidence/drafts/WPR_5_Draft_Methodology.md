# AMITY SCHOOL OF ENGINEERING & TECHNOLOGY
**Amity University Uttar Pradesh, Greater Noida**
**Minor Project (ETMN100)**
**WEEKLY PROGRESS REPORT (WPR) – 5**

**For the week commencing:** 17/08/2026 – 23/08/2026
**Enrollment Number:** A41105223039
**Student Name:** Anubhav Anand
**Program:** B.Tech CSE
**Faculty Guide's Name:** Dr. Girish Paliwal, Professor
**Project Title:** WaterTriage: A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar

---

# Methodology

This section outlines the system architecture, database schema, and mathematical scoring framework implemented in WaterTriage. The system is designed to ingest raw water quality reports, calculate risk metrics, flag recurring contamination, and rank villages for remediation.

```
       +--------------------------------------------------------+
       |                  Streamlit Dashboard                   |
       |  (Geospatial Map, KPI Metrics, Priority Queue Table)   |
       +---------------------------+----------------------------+
                                   |
                                   | HTTP REST
                                   v
       +--------------------------------------------------------+
       |                    FastAPI Backend                     |
       |  (Endpoints, Scoring Engine, Recurrence Detection)     |
       +---------------------------+----------------------------+
                                   |
                                   | SQLAlchemy ORM
                                   v
       +--------------------------------------------------------+
       |                  PostgreSQL Database                   |
       |  (Administrative Tables, Test Samples, Risk Rankings)  |
       +--------------------------------------------------------+
```

## 1. System Architecture
WaterTriage is structured as a decoupled, multi-tier web application fully containerized using Docker and Docker Compose:
1.  **Data Tier (PostgreSQL):** Stores administrative hierarchies, parameter safety standards (BIS 10500), water samples, parameter readings, computed risk scores, and recommended interventions.
2.  **Logic Tier (FastAPI Backend):** Written in Python, utilizing SQLAlchemy ORM. It exposes REST API endpoints, performs risk calculations, runs the recurrence detection engine, and manages the database state.
3.  **Presentation Tier (Streamlit Dashboard):** Communicates with the FastAPI backend to visualize key indicators, display interactive geospatial maps, and present filterable priority tables.

## 2. Database Schema
To support tracking water quality across administrative boundaries, the database is normalized into the following entities:
-   **Administrative Levels:** `states` $\to$ `districts` $\to$ `blocks` $\to$ `panchayats` $\to$ `villages`. This structure matches the LGD (Local Government Directory) codes used in India.
-   **BIS Safety Limits (`bis_limits`):** Stores parameters, acceptable limits, permissible limits, units, and health weights.
-   **Water Quality Testing (`water_samples` & `parameter_readings`):** A single sample is taken at a village on a specific date, containing multiple readings (e.g. Arsenic, Fluoride, TDS).
-   **Analytical Results (`risk_scores` & `interventions`):** Store computed risk metrics, severity bands, and ranked recommendations.

## 3. Mathematical Scoring Engine
The scoring engine computes the risk level of each village based on the deviation of water readings from BIS 10500 standards.

### A. Parameter Severity ($S_p$)
For each chemical or biological parameter $p$ in a sample, the severity $S_p \in [0.0, 1.0]$ is calculated as follows:

$$\text{Let } v_p = \text{tested value, } A_p = \text{acceptable limit, and } P_p = \text{permissible limit.}$$

1.  **Standard Chemical Contaminant:**
    $$S_p = \begin{cases} 
      0 & \text{if } v_p \le A_p \\
      1.0 & \text{if } v_p \ge P_p \text{ or } A_p = P_p \\
      \frac{v_p - A_p}{P_p - A_p} & \text{if } A_p < v_p < P_p 
   \end{cases}$$
2.  **Bacteriological Contaminant (E. coli, Total Coliform):**
    $$S_p = \begin{cases} 
      0 & \text{if } v_p = 0 \\
      1.0 & \text{if } v_p > 0 
   \end{cases}$$
3.  **pH (Acceptable Range 6.5 - 8.5):**
    $$S_p = \begin{cases} 
      0 & \text{if } 6.5 \le v_p \le 8.5 \\
      \min\left(1.0, \frac{6.5 - v_p}{1.0}\right) & \text{if } v_p < 6.5 \\
      \min\left(1.0, \frac{v_p - 8.5}{1.0}\right) & \text{if } v_p > 8.5
   \end{cases}$$

### B. Composite Risk Score ($CRS$)
The composite risk score is a weighted average of individual parameter severities, scaled from 0 to 100:

$$CRS = \left( \frac{\sum_{p=1}^{n} (S_p \times W_p)}{\sum_{p=1}^{n} W_p} \right) \times 100$$

Where $W_p$ is the health-risk weight assigned to parameter $p$ (e.g., Arsenic = 1.0, E. coli = 0.9, Fluoride = 0.8, TDS = 0.3, pH = 0.2).

### C. Severity Bands
Based on the composite score, the village is categorized into one of four severity bands:
-   **Critical:** $CRS \ge 75$
-   **High:** $50 \le CRS < 75$
-   **Medium:** $25 \le CRS < 50$
-   **Low (Safe):** $CRS < 25$

## 4. Recurrence Detection Heuristics
A village is flagged with `recurring = True` if the dataset indicates persistent contamination over time. The system evaluates historical samples for two conditions:
1.  **Temporal Recurrence:** The village has at least one parameter marked as `is_contaminated = True` on two or more distinct testing dates (e.g., in 2024 and 2026).
2.  **Parameter Recurrence:** The same contaminant is flagged as exceeding limits in two or more separate water samples, even if the samples were collected on the same date from different sources.

## 5. Intervention Priority Ranking
The system generates a ranked queue of required interventions. The priority rank is determined by sorting villages based on the following hierarchy:
1.  **Severity Band:** Critical > High > Medium > Low (Safe).
2.  **Toxicity Level:** Priority is given to villages contaminated with heavy metals or pathogens (Arsenic > E. coli > Fluoride > Nitrates > Others).
3.  **Recurrence Status:** Recurring contamination is ranked higher than isolated occurrences.
4.  **Composite Risk Score:** Sort descending to resolve ties within the same band.
5.  **Intervention Action Mapping:** Safe villages receive a rank of `NULL` (Routine Monitoring), while contaminated villages are assigned ranks from 1 (highest priority) to $N$.
