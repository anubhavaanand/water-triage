# WPR-9: Full Research Paper — **REVISED (v2)**

**Revision date:** 23/09/2026 v2.1
**Supersedes:** `reports/submitted_pdfs/WPR_9_Anubhav_Anand.pdf` (compiled 20/09/2026 17:20)
**Reason for revision:** The submitted version reported figures from a pre-correction database snapshot and contained one unsupported claim. Both are corrected below with an additional disclosure about iron scoring model behavior that affects 84% of Critical samples. Changes are itemised in the Revision Note printed in the document itself rather than issued separately.

---

## REVISION NOTE *(include verbatim in the submitted PDF, immediately after the abstract)*

Three corrections were made to this paper after its figures were first drafted, each traced to a
specific defect rather than to a change of interpretation.

1. **Sample count and band distribution.** The database of record was re-verified against
   PostgreSQL and **114 synthetic demonstration rows were removed** from the corpus. Reported
   figures change from 1,245 samples (14 Critical / 462 High / 11 Medium / 758 Low) to **1,741
   samples (89 Critical / 392 High / 28 Medium / 1,232 Low)**.
2. **A parser defect reversed the headline comparison.** The ingest layer resolved laboratory
   parameter labels by substring matching, so the alias `ph` matched `Sul<u>ph</u>ate`. 467
   sulphate readings were filed as pH values; because pH severity saturates at
   `clamp(deviation/1.0)`, sulphate concentrations of 100–900 mg/L each scored maximum severity.
   **394 of those 467 mis-tagged rows were in Uttar Pradesh**, which inflated Uttar Pradesh's mean
   composite score. Corrected, the comparison **reverses: Uttar Pradesh 12.68, Bihar 18.36.** The
   earlier "Uttar Pradesh is riskier" conclusion in this paper and in WPR-6 and WPR-7 was an
   artifact of the defect, not a finding.
3. **One recurrence claim was unsupported and has been withdrawn.** Section 4.5 of the submitted
   version stated that the recurrence module classified Khokha village (Purnia) as a
   *chronic-hotspot*. It does not, and structurally cannot, on this data. The honest statement is
   retained in Section 4.5 below.

Corrections 1 and 2 changed the numbers; correction 3 removed a claim. All three are disclosed here
because a reader comparing this paper against WPR-6, WPR-7 or WPR-8 would otherwise find
unexplained contradictions in those earlier reports, which have not been withdrawn.

---

## Abstract

Access to safe drinking water remains a critical public health concern across rural India, particularly in the states of Uttar Pradesh and Bihar, where chemical and microbiological contamination of groundwater sources affects millions of households. Despite the Jal Jeevan Mission (JJM) generating extensive water quality testing data at the village and habitation level, this information remains largely inaccessible to local district and block-level officials responsible for prioritising remediation efforts. This project proposes WaterTriage, an open, data-driven triage system that ingests publicly available JJM water quality data and processes it through a backend pipeline built on Python, FastAPI, SQLAlchemy, and PostgreSQL. At its core lies a contamination severity scoring engine that evaluates water sources against Bureau of Indian Standards (BIS) 10500 permissible limits, applying differential weights by health risk and an acute-hazard escalation rule that prevents severe contaminants such as arsenic and E. coli from being diluted by compliant aesthetic parameters. A recurrence detection module is designed to distinguish persistent contamination from isolated anomalies using a historical registry spanning 2009–2012. The system was validated against **1,741 live laboratory reports (966 from Uttar Pradesh, 775 from Bihar)** and **100,690 historical contamination records**, producing ranked, filterable intervention priority lists through nine REST API endpoints and an interactive dashboard. Results show a mean composite risk score of **12.68 for Uttar Pradesh versus 18.36 for Bihar**, reflecting materially distinct contamination profiles. Uttar Pradesh holds the corpus's single most extreme chemical result — a **fluoride concentration of 12.60 mg/L**, 8.4 times the BIS permissible limit — while **Bihar accounts for 75 of the 89 Critical-band samples** on a smaller sample base. The recurrence analysis is reported at **district** level, since village-level identifiers are absent from the majority of public lab reports; the resulting limitation is analysed in Section 5. The system demonstrates that independently reproducible analytics built on government open data can support ground-level water safety planning without requiring privileged access to internal government systems, while making explicit which administrative resolution that data can and cannot support.

**Keywords:** Water Quality; Jal Jeevan Mission; Contamination Severity Scoring; BIS 10500; FastAPI; Intervention Prioritization; Recurrence Detection

---

## 1. Introduction

*(Unchanged from the submitted version except for the final sentence, which is re-scoped.)*

Access to safe and adequate drinking water is a fundamental determinant of public health, yet a substantial proportion of India's rural population continues to rely on groundwater sources vulnerable to both geogenic and anthropogenic contamination. Uttar Pradesh and Bihar, situated along the Indo-Gangetic plain, are particularly affected by naturally occurring arsenic and fluoride contamination, compounded by nitrate and microbiological contamination from inadequate sanitation infrastructure. The Jal Jeevan Mission (JJM) has generated one of the largest water quality testing datasets in the country, yet this data remains consolidated within the Water Quality Management Information System (WQMIS), a reporting layer designed for national and state-level monitoring rather than direct, actionable use by district and block-level officials.

This project is motivated by the observation that publicly accessible JJM data can be independently processed to close this accessibility gap without requiring modification to, or privileged access within, existing government systems. The primary objective is to design and implement WaterTriage: a reproducible system that ingests JJM water quality data for Uttar Pradesh and Bihar, scores each recorded source against BIS 10500 limits, and produces a ranked, filterable list of intervention priorities. The two states were selected both for practical feasibility and because they exhibit genuinely distinct contamination profiles — Bihar's arsenic- and iron-affected districts along the Gangetic floodplain, contrasted against Uttar Pradesh's fluoride and nitrate concerns — offering a meaningful basis for comparative analysis. **The delivered system resolves priorities to the district and block level rather than the village level; Section 5.1 establishes that this is a property of the published source data, not of the scoring design.**

---

## 2. Related Work

*(Unchanged. Sections 2.1 Government Water Quality Monitoring Infrastructure, 2.2 Groundwater Contamination in the Middle Gangetic Plain, 2.3 Water Quality Index and Contamination Scoring Approaches, and 2.4 Positioning of This Project are reproduced verbatim from the submitted version.)*

---

## 3. Methodology

### 3.1 System Architecture
Unchanged: four-stage pipeline — acquisition, storage, enrichment, serving.

### 3.2 Database Schema
Unchanged: eight tables — `states`, `districts`, `villages`, `bis_parameters`, `water_samples`, `readings`, `risk_scores`, `historical_contamination`, `interventions`.

**Addition for accuracy.** The two ingest paths wrote geographic names under different conventions — the WQMIS loader Title Case (`Saharanpur`), the historical registry loader UPPER (`SAHARANPUR`) — so the `districts` table holds **142 rows for 109 distinct districts**. This is disclosed because it is the proximate reason the sample and historical tables cannot be joined by identifier (Section 5.1), and because it is a schema-level defect that a normalisation migration must resolve.

### 3.3 Contamination Severity Scoring
Unchanged in substance. Per-parameter severity 0–1 by linear interpolation between BIS acceptable and permissible limits; microbial and no-relaxation parameters saturate at 1.0 on any exceedance; composite risk score (CRS) is the weighted mean scaled to 0–100 with health-risk weights (arsenic 1.0, E. coli 0.9, fluoride 0.8, nitrate 0.7, iron 0.4, turbidity 0.3, TDS 0.3, pH 0.2). Bands: Critical ≥75, High 50–74, Medium 25–49, Low <25. The band-escalation rule that corrects the WQI eclipsing flaw is: any parameter at full severity (≥1.0) floors the band at High; a full breach of an *acute* hazard (E. coli, total coliform, arsenic) floors it at Critical irrespective of the arithmetic score.

**Addition for completeness.** `total_coliform` (7 readings) and `sulphate` (467 readings) are persisted but **deliberately excluded from scoring**: sulphate carries no entry in the IS 10500 weight set used by this model. The exclusion is explicit rather than incidental, since 467 unexplained readings would otherwise invite the question.

### 3.4 Recurrence Detection
As implemented, each village–parameter combination is evaluated against the historical registry alongside current sample data, and a recurrence score blends the number of registry years with current exceedance status into one of four verdicts: `chronic-hotspot`, `recurring`, `watchlist`, `no-history`.

**Correction of an overstatement.** The submitted version presented this module as producing confirmed hotspot verdicts. On the delivered corpus it produces none: a `persistent` classification — the necessary condition for `chronic-hotspot` — requires a current exceedance recorded against the same village identifier that appears in the registry, and the two tables' village identifier sets are disjoint. The module is therefore reported honestly as **implemented, unit-tested, and not yet exercised on connected data**, with the district-level rework that would make it functional described in Section 5.1.

### 3.5 Data Acquisition Strategy
Unchanged: crawler against the WQMIS public report-printing endpoint with politeness controls, plus the 2009–2012 historical Quality-Affected Habitations registry as a supplementary source.

**Addition on limits.** The parameter-wise endpoint is session-gated and denies an anonymous role, which caps further acquisition at the present access level. The corpus reflects which sample-identifier ranges were scanned and is **not a random or spatially uniform sample** of either state.

### 3.6 Implementation
Unchanged: FastAPI and SQLAlchemy against PostgreSQL 16, containerised via Docker Compose; nine REST endpoints; interactive dashboard with priority queue, state comparison and district-level map.

### 3.7 Testing
**Corrected count.** The implementation was validated using **twenty-seven** automated test cases (the submitted version said twenty-six) covering scoring correctness, API contract behaviour, WQMIS parser edge cases and recurrence logic, including a PostgreSQL integration suite. All twenty-seven pass in 1.41 s against the production database. The recurrence-ranking performance issue (an N+1 query pattern at approximately 37 s) was resolved by rewriting the operation as set-based queries to approximately 0.58 s, with output verified identical by regression tests.

**Addition on test adequacy.** The parser defect in Section 4.3 was not caught by the suite: `test_wqmis_parse.py` exercises `etl.wqmis.parse_report`, a different function from the faulty `etl.load_wqmis.map_param`, and nothing pinned "sulphate must not map to pH." The defect class is now covered by an exact-match aliasing rule plus a re-derivation utility (`backend/etl/repair_readings.py`); a physical-plausibility assertion at ingest (rejecting, for example, any value labelled pH above 14) remains open scope and is named as such.

---

## 4. Results

### 4.1 Data Volume

The production PostgreSQL database contains **1,741 scored live laboratory reports (Uttar Pradesh: 966; Bihar: 775)** and **6,792 individual parameter readings**, supplemented by **100,690 historical contamination registry events** (Bihar 90,794; Uttar Pradesh 9,896) spanning 2009–2012.

Sample counts reported in earlier weekly progress documents (755, then 1,359, then 1,245, then 1,855) reflect intermediate snapshots taken during active crawling, an initial SQLite prototype, and the subsequent removal of synthetic demonstration rows. The figures in this section are drawn directly from the production database and are treated as authoritative; each is reproducible by the queries listed in Appendix B of `docs/frontend-plan.md`.

### 4.2 Severity Band Distribution

**Table 1 — distribution of 1,741 scored samples**

| Severity Band | Count | Share |
|:---|---:|---:|
| Critical (CRS ≥ 75) | **89** | 5.1% |
| High (50 ≤ CRS < 75) | **392** | 22.5% |
| Medium (25 ≤ CRS < 50) | **28** | 1.6% |
| Low / Safe (CRS < 25) | **1,232** | 70.8% |
| **Total** | **1,741** | 100% |

| Band | Uttar Pradesh | Bihar |
|:---|---:|---:|
| Critical | 14 | **75** |
| High | 234 | 158 |
| Medium | 27 | 1 |
| Low / Safe | 691 | 541 |
| **All samples** | **966** | **775** |

### 4.3 Comparative State Analysis

**Table 2 — contamination metrics by state (corrected)**

| Metric | Uttar Pradesh | Bihar |
|:---|---:|---:|
| Scored samples | 966 | 775 |
| **Mean composite risk score (CRS)** | **12.68** | **18.36** |
| Average fluoride (mg/L) | 0.616 | 0.508 |
| Maximum fluoride (mg/L) | **12.60** | 1.410 |
| Average nitrate (mg/L) | 7.439 | 5.817 |
| Maximum nitrate (mg/L) | 61.24 | 25.00 |
| Average iron (mg/L) | 0.361 | 0.353 |
| Maximum iron (mg/L) | 2.380 | 0.980 |
| Average arsenic (mg/L) | 0.003 | 0.001 |
| Maximum arsenic (mg/L) | 0.009 | 0.004 |

**The mean composite risk score is materially higher in Bihar (18.36) than in Uttar Pradesh
(12.68)** — the opposite direction to the submitted version of this paper, for the parser reason
given in the Revision Note. Bihar concentrates **75 of the 89 Critical-band samples (84%)** while
holding 45% of the corpus, so its Critical rate is roughly seven times Uttar Pradesh's.

Uttar Pradesh's distinguishing feature is not its average severity but its **chemical ceiling**:
the maximum recorded fluoride concentration of **12.60 mg/L** is 8.4 times the BIS permissible
limit of 1.5 mg/L and 12.6 times the acceptable limit, against a Bihar maximum of 1.410 mg/L,
which does not breach the acceptable limit at all. Uttar Pradesh also carries the higher nitrate
extreme (61.24 mg/L against 25.00). The two states therefore differ in the *shape* of risk —
Uttar Pradesh a lower mean with sharp geogenic and anthropogenic extremes, Bihar a uniformly
elevated mean — which is a more defensible framing than a single "riskier state" claim.

**Arsenic must be read against coverage.** The maximum arsenic observed anywhere in the corpus is
0.009 mg/L, below even the 0.01 mg/L acceptable limit, from 259 readings. This is a statement
about which samples the crawler reached, not evidence that the study area's groundwater is
arsenic-safe; the published district counts in `references/` and the historical registry both
record arsenic-affected habitations in these states. Section 5.2 treats this as the corpus's most
important negative result.

### 4.4 Escalation Rule Validation

Sample **`U691097L158S1903`**, from Lucknow, Uttar Pradesh, returned a composite arithmetic score of
**20.01** — which classifies as Low/Safe under conventional averaging — but was escalated to
**Critical**, with `worst_parameter = e_coli` recorded as the driver. (The submitted version
reported this score as 24.35; the value changed with the parser correction, the classification did
not.) The case demonstrates the practical necessity of the escalation rule described in Section
3.3: a purely averaged index would have reported an E. coli-positive source as safe.

### 4.5 Recurrence and Chronic Hotspot Findings — **corrected**

The submitted version of this paper stated that the recurrence module flagged Khokha village
(Purnia, Bihar) as a *chronic iron-contamination hotspot* with 166 recorded exceedance events.
**That classification is withdrawn.** Re-running the module over the production database returns
14,006 villages and classifies **every one of them `watchlist`**, with zero `chronic-hotspot` and
zero `recurring` verdicts.

What the data does support is narrower and still useful:

- **Khokha (Purnia, Bihar) holds the deepest historical iron record in the registry: 166 IRON
  events across 2009–2012, the highest count of any of the 14,006 registered villages.** Purnia
  dominates the registry's top ranks (Khokha 166, Khunti Dhanaili 165, Satkodaria 156, Singhia
  153).
- This is a **historical-registry finding, not a recurrence finding.** It describes a documented
  long-term hydrogeological susceptibility. It cannot be described as persistent or current,
  because **no scored WQMIS sample exists for Khokha** — or for any village in Bihar, whose
  sample records carry no village identifier at all (Section 5.1).

The distinction matters for the intervention question this project asks. A chronic classification
would license a specific engineering response (deeper bore placement, a treatment train sized for
recurring iron). A historical-only classification licenses, at most, **prioritising Purnia for
confirmatory sampling** — which is a genuinely different recommendation, and the one the data
actually supports.

### 4.6 System Validation

All **twenty-seven** automated tests pass against the production database. The nine REST endpoints
and the dashboard were verified functional against that database, and the recurrence-ranking
optimisation (37 s → 0.58 s) was confirmed by regression testing. `dashboard/data.json`, which the
static console consumes, was regenerated from the production database on 20/09/2026 rather than
hand-edited, so the console's figures and Section 4.1 agree.

---

## 5. Discussion

### 5.1 Resolution limits: what this data can and cannot be asked

Three coverage facts constrain every conclusion above, and they are properties of the published
source data rather than of the scoring design.

1. **Village identifiers are almost entirely absent from the scored corpus.** Only **21 of 1,741
   samples (1.2%)** attach to a real village name; all 21 are in Uttar Pradesh, and they occupy
   eight distinct villages (Abbha 6, Dharauli 4, Bhoor Niranjanpur 4, Bragunnu 2, Nagram 2, and
   three with one sample each). The remaining 1,720 records carry the literal value "Not
   available" in the village field of the WQMIS report. **Bihar's figure is zero.** Any
   village-level prioritisation claim is therefore unsupported by construction, and the system's
   defensible unit of resolution is the **district**: real coverage is **47 districts (Uttar
   Pradesh 28, Bihar 19)** out of the 114 in the two states.
2. **The sample and historical tables are disjoint at village level.** Their `village_id` sets
   intersect in exactly zero rows, which is why the recurrence module returns no hotspots
   (Section 4.5). Part of the cause is the name-convention defect in Section 3.2.
3. **A district-level join is available and is the honest path forward.** After case
   normalisation, **32 districts appear in both tables, containing 774 scored samples and 23,850
   historical events.** That is sufficient to compute real district-level recurrence, and it is
   the highest-value remaining engineering task in this project. It would let the system say
   "district X is both historically quality-affected and currently scoring Critical," which is a
   claim the current village-level join cannot make at all.

### 5.2 Negative results and what they mean

The corpus's thin parameters are as informative as its dense ones. Microbial testing — the
category carrying the heaviest escalation power — accounts for **45 E. coli and 7 total coliform
readings out of 6,792 (0.8%)**, yet E. coli alone determines the Critical band in the Section 4.4
case. Arsenic, the most heavily weighted contaminant in the model, appears in **259 readings
(3.8%)** and never exceeds 0.009 mg/L. Turbidity, TDS, pH and iron are each measured on more than
800 samples. The scoring model is thus *weighted* toward hazards that the underlying data
*under-observes*: a source is far more likely to be ranked on an aesthetic parameter than on the
pathogen or metal that the weights consider decisive. This is a surveillance-coverage finding
about JJM's public reporting, and it is arguably the most useful result this project produced —
but it also means the priority list should be read as *ranked on what was tested*, not as a
complete hazard census of any village.

### 5.3 Iron scoring model limitation

Iron's permissible limit is defined as NULL in the BIS IS 10500 specification used by this model,
causing any exceedance above the acceptable threshold of 0.3 mg/L to trigger maximum severity
interpolation. Consequently, samples with marginal iron exceedances (0.31–0.60 mg/L) receive full-severity
scores that saturate the composite score at Critical band levels. Of the 89 Critical samples, **75
(84%) are iron-driven** at average concentrations well below aesthetic concern thresholds. This
model design artifact means a substantial portion of the Critical ranking reflects scoring behavior
rather than contamination urgency. These cases should be re-evaluated once the scoring model adopts
a scientifically justified permissible limit (e.g., WHO/BIS aesthetic limit of 1.0 mg/L) or switches
to tiered severity bands for sub-critical metals.

### 5.3 Interpretation of the comparative result

The corrected finding — Bihar's higher mean and its concentration of Critical samples, against
Uttar Pradesh's extreme fluoride and nitrate maxima — is consistent with the hydrogeological
literature reviewed in Section 2.2 in a way the reversed original was not: Bihar's Gangetic
floodplain iron and arsenic mobilisation produces broadly elevated low-level contamination across
many sources, whereas Uttar Pradesh's fluoride belts produce locally severe exceedances against a
background of compliant sources. The two states warrant different intervention *strategies*
(widespread source improvement versus targeted treatment in specific belts), which is the
practically actionable form of the comparison. The original UP-higher framing would have pointed
resources the wrong way, which is the concrete cost of the parser defect.

### 5.4 Other limitations

First, the 1,741 reports were drawn from targeted WQMIS identifier ranges rather than a spatially
uniform census; district density reflects crawler coverage, not underlying contamination burden.
Second, every scored sample is dated between **2022-07-01 and 2022-11-19**, against a registry
window of 2009–2012: there is a temporal discontinuity on both sides of the comparison, and the
system cannot support any current-year monitoring claim. Third, the collection-date field is
partly a parse artifact (341 samples share a single date) and `source_type` is polluted with
laboratory names and identifiers, so provenance metadata is unreliable and is labelled as such in
the interface rather than displayed as fact.

---

## 6. Conclusion

This project set out to design and implement WaterTriage, a system that ingests publicly available
JJM water quality data for Uttar Pradesh and Bihar and produces ranked, actionable intervention
priorities that existing government reporting systems do not directly provide to local officials.

**Table 3 — synopsis objectives against delivered outcomes (corrected)**

| Synopsis Objective | Delivered Outcome |
|:---|:---|
| Acquisition and normalization of JJM open water-quality data for UP and Bihar | **Achieved** — politeness-controlled, cached, resumable WQMIS public report crawler delivering **1,741 scored live laboratory reports (UP 966 / Bihar 775)** with 6,792 parameter readings, supplemented by a 100,690-event historical registry (2009–2012). Acquisition is capped by session-gated access to the parameter-wise endpoint. |
| Relational database schema for source-level records | **Achieved with a known defect** — eight-table normalised schema with referential integrity, but geographic names are duplicated across ingest conventions (142 `districts` rows for 109 districts), which blocks the cross-source join in objective 4. |
| Contamination severity scoring model per BIS IS 10500 | **Achieved and re-validated** — weighted per-parameter severity with linear interpolation, plus the acute-hazard escalation rule; verified live on sample `U691097L158S1903` (score 20.01, escalated to Critical via E. coli). |
| Recurrence/trend detection module | **Partially achieved — honest restatement.** Engine implemented and unit-tested, classifying village-parameter pairs by blending registry history with current exceedance. **It returns zero chronic hotspots on the delivered corpus** because sample and registry village identifiers are disjoint. The registry itself confirms Khokha (Purnia) as its most iron-affected village across 2009–2012 (166 events). A district-level join across 32 shared districts is specified as the fix. |
| FastAPI backend exposing ranked intervention lists | **Achieved** — nine REST endpoints including ranked priority queue, recurrence ranking and state comparison. |
| Dashboard for district-wise and state-wise comparison | **Achieved at district resolution** — interactive console with priority queue, drill-down verdicts, state comparison and district-level maps for both states, consuming a snapshot regenerated from the production database. Village-level drill-down is not supportable for 1,720 of 1,741 samples and is not claimed. |
| Containerized deployment | **Achieved** — PostgreSQL and backend services containerised via Docker Compose, with an Alembic initial-schema revision present; bringing the live database under Alembic version control remains future scope. |

The system was implemented, tested against **twenty-seven** automated test cases, and validated
against a production database of **1,741 real laboratory reports and 100,690 historical
contamination records**. Its central contribution is an open, independently reproducible triage
layer that renders JJM water-quality data actionable for district and block-level officials.

Two things are claimed deliberately, and one is not. The scoring engine is claimed: it is
validated, and Section 4.4 shows its escalation rule operating on a real sample. The
district-resolution comparison is claimed, and Section 5.3 argues it is the more useful framing.
Village-level prioritisation — the form the original synopsis envisioned, "which village gets a
repair team first" — is **not** claimed, because the published data does not carry village
identifiers for 98.8% of the corpus. Naming that boundary, and the parser defect that briefly
concealed it, is part of what an 82-day minor project can legitimately contribute: a reproducible
method, an honest resolution limit, and a surveillance-coverage finding (Section 5.2) that follows
from measuring which hazards the public data actually observes.

Future work: (i) the district-level recurrence rework of Section 5.1, which converts the largest
unexercised component of the system into a working one; (ii) an ingest-time physical-plausibility
assertion, the single control that would have caught the Section 4.3 defect at load time;
(iii) expanded acquisition subject to official WQMIS access or the restricted AIKosh
source-quality dataset, the only identified public source with village-level coverage; and
(iv) an interventions-tracking workflow with exportable reporting for field use.

---

## References

*(Unchanged — references [1] through [8] as in the submitted version.)*
