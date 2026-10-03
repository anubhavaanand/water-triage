# AMITY SCHOOL OF ENGINEERING & TECHNOLOGY
**Amity University Uttar Pradesh, Greater Noida**
**Minor Project (ETMN100)**
**WEEKLY PROGRESS REPORT (WPR) – 4**

**For the week commencing:** 10/08/2026 – 16/08/2026
**Enrollment Number:** A41105223039
**Student Name:** Anubhav Anand
**Program:** B.Tech CSE
**Faculty Guide's Name:** Dr. Girish Paliwal, Professor
**Project Title:** WaterTriage: A Data-Driven Water Quality Risk Scoring and Intervention Prioritization System for Uttar Pradesh and Bihar

---

# Related Work / Literature Review

Prioritizing water safety interventions in developing rural contexts requires combining environmental science, public health guidelines, and data engineering. This section reviews the literature across three key areas: national water monitoring frameworks, water quality index (WQI) scoring methodologies, and the application of decision-support systems for resource allocation.

## 1. National Water Quality Frameworks and WQMIS
The Government of India's Jal Jeevan Mission (JJM), launched in 2019, aims to provide functional household tap connections to all rural households by delivering safe drinking water. Under this mission, the Water Quality Management Information System (WQMIS) was established by the Department of Drinking Water and Sanitation (DDWS) in partnership with the Indian Council of Medical Research (ICMR). WQMIS serves as a national repository for water quality test results conducted at state/district laboratories and on-field using Field Test Kits (FTKs).

While WQMIS provides extensive datasets, studies by Ray et al. (2022) indicate that the utility of this data remains bottle-necked at the district and block levels. Currently, WQMIS operates primarily as a reporting and compliance portal, aggregating counts of tests conducted. Local administrative bodies (Panchayati Raj Institutions and Public Health Engineering Departments) lack tools that synthesize raw readings (such as arsenic in mg/L or E. coli counts) into prioritized action lists. This research gap is what WaterTriage aims to address.

## 2. Water Quality Index (WQI) and Severity Modeling
Evaluating water quality for human consumption has historically relied on the Water Quality Index (WQI), first proposed by Horton (1965) and refined by Brown et al. (1970). Standard WQI models aggregate multiple chemical parameters into a single score using arithmetic weighting:

$$WQI = \frac{\sum W_i q_i}{\sum W_i}$$

Where $W_i$ represents the unit weight of a parameter and $q_i$ represents its sub-index value. However, traditional WQI models exhibit "eclipse" and "ambiguity" effects. Eclipsing occurs when a single highly toxic parameter (e.g., Arsenic) exceeds permissible limits, making the water unsafe, but the composite index remains "Good" due to other clean parameters. 

To mitigate eclipsing, recent environmental research (e.g., Tyagi et al., 2020) suggests using non-linear or max-operator aggregation techniques, especially when assessing drinking water against health standards like the Bureau of Indian Standards (BIS) 10500. WaterTriage adapts these findings by utilizing a weighted severity model that calculates the exceedance ratio of individual parameters relative to their permissible limit, ensuring highly toxic elements like Arsenic (weight = 1.0) and E. coli (weight = 0.9) dominate the composite risk score.

## 3. Toxicity and Health Risks of Focus Contaminants
The geographical focus of this project, Uttar Pradesh and Bihar, is motivated by the distinct geological distribution of groundwater contamination along the Indo-Gangetic plain.
- **Arsenic (As):** As documented by Chakraborti et al. (2018), arsenic contamination is geogenic and highly prevalent along the Gangetic aquifers of Bihar. Chronic ingestion of arsenic leads to arsenicosis, skin lesions, and various cancers. The BIS 10500 standard defines the acceptable limit as 0.01 mg/L, with no relaxation allowed.
- **Fluoride (F):** Widespread in districts of Uttar Pradesh like Unnao and Firozabad. Fluoride concentrations above 1.5 mg/L cause dental and skeletal fluorosis, characterized by teeth discoloration and bone deformities.
- **Bacteriological Contamination (E. coli):** Reflects fecal contamination, leading to acute diarrheal diseases, cholera, and typhoid. The standard mandates zero E. coli presence per 100 mL sample.

## 4. Decision Support Systems for Local Interventions
Intervention prioritization is an optimization problem under resource constraints. While several decision support systems (DSS) exist for urban water networks, rural applications are limited. Previous works (e.g., Al-Mulla, 2019) utilized Geographic Information Systems (GIS) to map water quality but did not incorporate temporal recurrence or risk scoring for automated action recommendations. WaterTriage bridges this gap by integrating FastAPI-based REST APIs with a Streamlit-rendered spatial dashboard, providing local officials with actionable ranks and specific technical recommendations (e.g., Nalgonda defluoridation or chlorination) directly mapped to the severity and recurrence of the contamination.
