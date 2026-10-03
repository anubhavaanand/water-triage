# RECONCILIATION.md — Complete Data & Narrative Audit

**Generated on:** 2026-10-04  
**Audit Source:** `reports/facts.json` (queried live against PostgreSQL `watertriage-db` / `jjm_triage`)  
**Git Commit:** `96d2803e0adf1195f64e03a420c67963b3d84d63` (`final-frontend-cleanup`)  

---

## 1. Truth Matrix: Canonical Database vs. Prior Reports & Documents

| Metric | Canonical (`facts.json`) | WPR-6 (24–30 Aug) | WPR-7 (31 Aug–06 Sep) | WPR-8 (07–13 Sep) | WPR-9 Submitted (20 Sep) | WPR-9 Revised Draft (`v2.1`) | `AGENTS.md` / `SESSION_HANDOFF` | `dashboard/data.json` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Total Samples** | **1,741** | 755 (869 scored) | 1,245 | 1,245 | 1,245 | **1,741** | **1,741** | **1,741** (rebuilt in `96d2803`) |
| **UP Samples** | **966** | 511 | 687 | 687 | 687 | **966** | **966** | **966** |
| **Bihar Samples** | **775** | 311 | 558 | 558 | 558 | **775** | **775** | **775** |
| **Total Readings** | **6,792** | 3,124 | ~4,900 | ~4,900 | 4,912 | **6,792** | **6,792** | — |
| **Historical Events** | **100,690** | 100,690 | 100,690 | 100,690 | 100,690 | **100,690** | **100,690** | 100,690 |
| **Critical Band (≥75)** | **89** | ~14 | 14 (UP 6, BH 8) | 14 | 14 (UP 6, BH 8) | **89** (UP 14, BH 75) | **89** | **89** |
| **High Band (50–74)** | **392** | — | 462 (UP 318, BH 144) | 462 | 462 | **392** (UP 234, BH 158) | **392** | **392** |
| **Medium Band (25–49)**| **28** | — | 11 (UP 11, BH 0) | 11 | 11 | **28** | **28** | — |
| **Low Band (<25)** | **1,232** | — | 758 (UP 352, BH 406) | 758 | 758 | **1,232** | **1,232** | **1,232** |
| **UP Mean CRS** | **12.68** | — | 14.51 ± 17.52 | 14.51 | 14.51 | **12.68** | **12.68** | **12.68** |
| **Bihar Mean CRS** | **18.36** | — | 9.34 ± 17.67 | 9.34 | 9.34 | **18.36** | **18.36** | **18.36** |
| **Comparison Direction**| **Bihar > UP** | — | **UP > Bihar** (WRONG) | **UP > Bihar** (WRONG) | **UP > Bihar** (WRONG) | **Bihar > UP** (CORRECT) | **Bihar > UP** (CORRECT) | **Bihar > UP** (CORRECT) |

---

## 2. Root Cause Analysis: What Went Wrong in Prior Reports

### Defect 1: The Ingest Substring Parser Defect (Sulphate mis-tagged as pH)
- **Mechanism:** In `backend/etl/load_wqmis.py`, parameter aliases were matched via substring `ph` inside `Sulphate` (`Sul<u>ph</u>ate`). 
- **Impact:** 467 sulphate concentration readings (ranging from 100 to 900 mg/L) were ingested as pH values. Because pH severity is clamped deviation from [6.5, 8.5], values like 250 mg/L maxed out severity at 1.0.
- **Geographic Bias:** 394 of the 467 mis-tagged rows were in Uttar Pradesh. This artificially inflated Uttar Pradesh's mean score to 14.51 and depressed the relative risk of Bihar.
- **The Reversal:** Once repaired via `backend/etl/repair_readings.py` and strict exact parameter matching, Uttar Pradesh's true mean CRS dropped to **12.68**, while Bihar's true mean CRS was calculated at **18.36**.
- **Status:** Repaired in DB, verified live.

### Defect 2: Synthetic Samples Removal & Snapshot Growth
- WPR-6 used an early crawl snapshot (755 samples).
- WPR-7, WPR-8, and the originally submitted WPR-9 used an intermediate 1,245-sample snapshot that included 114 synthetic `SYN-*` demonstration rows and preceded crawler completion.
- Once crawler reached ID 1,100,118 and synthetic rows were pruned, the verified canonical corpus stabilized at **1,741 real laboratory reports**.
- A brief hallucination of a 47,243-row bulk table in Postgres was investigated, identified as an unverified external bulk insert, and purged via `TRUNCATE` and full reload from `records.jsonl`.
- `dashboard/data.json` had temporarily held 47,243 rows but was completely rebuilt to the canonical 1,741 rows in commit `96d2803`.

### Defect 3: The Recurrence Disconnect & Khokha Hotspot Claim
- **Prior Claim in WPR-6, 7, 8, and WPR-9 submitted:** Claimed Khokha village (Purnia, Bihar) was classified as an active, live "chronic hotspot" by the live API.
- **The Empirical Reality:**
  - `water_samples` and `historical_contamination` have **disjoint village identifiers** (0 shared village IDs).
  - Khokha has **166 historical iron records** in the historical registry (2009–2012) — the highest in the entire database.
  - BUT Khokha has **0 scored WQMIS samples** in the 2022 dataset.
  - In `backend/app/engine/recurrence_service.py`, `village_recurrence` is a stub that returns `None`.
  - The live system has district-level recurrence via `list_recurrent_districts`, but village-level drill-down does not exist.
- **Status:** WPR-9 Revised (`v2.1`) withdrew the village claim and honestly restated recurrence as district-level.

---

## 3. Sections in Prior Reports Requiring Complete Narrative Rewrite

The reversal from **UP (14.51) > Bihar (9.34)** to **Bihar (18.36) > UP (12.68)** is not a cosmetic typo; it reverses the primary geographic thesis of the paper.

### Sections Requiring Rewrite:
1. **WPR-7 §5.1 / WPR-9 §4.3 ("Regional Divide & State Comparison"):**
   - *Old False Narrative:* Claimed UP suffered higher overall multi-parameter contamination load due to non-point agricultural runoff and high nitrate/turbidity, while Bihar was mild except for isolated metals.
   - *New Defensible Narrative:* Bihar is the materially more hazardous state, exhibiting an aggregate Mean CRS of **18.36 vs UP's 12.68**. Furthermore, Bihar accounts for **75 of the 89 Critical-band samples (84.3%)** despite having fewer total samples (775 vs 966). Bihar's hazard profile is dominated by acute geogenic exceedances (high-severity Iron clustering, Turbidity, and Arsenic in the alluvial belt), whereas UP's lower mean is driven by widespread aesthetic/turbidity exceedances with localized extreme chemical spikes (e.g., Fluoride 12.60 mg/L in Agra).
2. **WPR-7 §5.3 / WPR-9 §4.5 ("Recurrence & Khokha Village"):**
   - *Old False Narrative:* "The live recurrence API flagged Khokha as an active chronic hotspot."
   - *New Defensible Narrative:* Acknowledge that public WQMIS data strips village identifiers (only 21 of 1,741 samples carry village names). Khokha is a historical registry phenomenon (166 iron events across 2009–2012). The recurrence engine was validated offline via unit tests; live API recurrence operates at district resolution across 32 shared districts.
3. **WPR-8 §6 / WPR-9 §5 ("Discussion & Policy Interventions"):**
   - Intervention priority must shift: Bihar habitations require immediate capital-intensive intervention (deep confined aquifer extraction, adsorption filters for iron/arsenic), whereas UP requires targeted fluoride remediation in central districts (Agra/Unnao) alongside source protection against agricultural runoff.
4. **WPR-9 §6 / Final Report ("Conclusion"):**
   - Replace all legacy sample numbers (755, 1,245) with **1,741**.
   - State the honest resolution boundary: The system achieves defensible intervention prioritization at the **district** level, while village-level triage remains an explicit limitation subject to future administrative data access (e.g. IndiaAI AIKosh).

---

## 4. Current File Status & Artifact Audit

1. **`reports/drafts/WPR_9_Revised_FullPaper.md`:**
   - Already fully updated with the corrected narrative (Bihar 18.36 > UP 12.68, 1,741 samples, Khokha withdrawal).
   - Audited and verified by subagent Kilo against live PostgreSQL.
2. **`reports/submitted_pdfs/WPR_9_Anubhav_Anand_Final.pdf`:**
   - Compiled from `WPR_9_Revised_FullPaper.md`. Available on Desktop.
3. **`reports/submitted_pdfs/WPR_10_Anubhav_Anand.pdf`:**
   - Generated on 30 Sep 2026. Contains no fabricated Turnitin score. Frames Week 10 as Originality & Integrity audit. Available on Desktop.
4. **`reports/submitted_pdfs/WPR_11_Anubhav_Anand_Final.pdf`:**
   - Pre-generated for Week 11 completion. Summarizes final validated outcomes. Available on Desktop.
