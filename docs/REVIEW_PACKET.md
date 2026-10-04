# REVIEW PACKET

## A. WPR-11 PDF
**pdfinfo output:**
```
Title:           WPR-11
Pages:           2
Page size:       595.276 x 841.89 pts (A4)
File size:       15637 bytes
```

**pdfimages -list output:**
```
(No images found in WPR-11, nor in WPR-10 which had 0 images)
```
- PNG renders saved to `docs/figures/WPR_11_Page-1.png` and `docs/figures/WPR_11_Page-2.png`.

## B. Alias & Registry Matching
- Restored original names (`Prayagraj`, `Kushinagar`, `Bara Banki`, `Siddharthnagar`, `Kaimur (Bhabua)`).
- Created `district_alias` table to map corpus names to registry names.
- **Database counts (intact):** 1,741 samples, 6,792 readings, 89 Critical, 392 High, 28 Medium, 1232 Low.

**Fuzzy Matches for Unmatched Districts:**
The following districts were completely missing from the `staging_kaggle_l3_habitations` registry file for 2009-2012, so they could not be matched. Fuzzy match results:
- `SITAPUR` -> `SULTANPUR` (score: 75)
- `SHAHJAHANPUR` -> `SAHARANPUR` (score: 82)
- `PURBI CHAMPARAN` -> `SARAN` (score: 72)
- `PILIBHIT` -> `BASTI` (score: 40)
- `PASHCHIM CHAMPARAN` -> `SARAN` (score: 72)
- `JEHANABAD` -> `NAWADA` (score: 66)
- `BUDAUN` -> `GAUTAM BUDDHA NAGAR` (score: 60)
- `AMETHI` -> `ETAH` (score: 68)
- `ARWAL` -> `BEGUSARAI` (score: 60)
- `SITAMARHI` -> `ARARIA` (score: 60)

**New Spearman Results:**
*Iron 0.3 (Standard):*
- POOLED (n=26): rho=0.548, p=0.004
- POOLED (excl Madhepura) (n=25): rho=0.493, p=0.012
- Uttar Pradesh (n=15): rho=0.528, p=0.043

*Iron 1.0 (Sensitivity Run):*
- POOLED (n=26): rho=0.349, p=0.081
- POOLED (excl Madhepura) (n=25): rho=0.411, p=0.041
- Uttar Pradesh (n=15): rho=0.457, p=0.087

*Fluoride:*
- POOLED (n=29): rho=0.223, p=0.246
- Uttar Pradesh (n=22): rho=0.426, p=0.048

## C. Evidence
- Saved raw `/api/meta` to `docs/meta.json`. **SHA256**: `e92254562db3a45e5a3c15bb30dd0fcb56ad69041a05394a3d8c2d949ed7e96e`.
- **`corpus.readings` Explanation**: The previous `/api/meta` response showed `corpus.readings` as an array of values `[["fluoride", 0.186], ...]` because of a variable shadowing bug (`readings` integer was overwritten by the `readings` list in the sample iteration loop). This has been fixed in `meta.py` and now correctly outputs the integer `6792`.
- `git log -1 -- README.md`: `docs: Rewrite README for React + FastAPI live system`
- Removed all mock files (`frontend/public/priority.json`, `frontend/public/data.json`, `frontend/dist/data.json`). Searching for `Unnao`, `Firozabad`, `Katihar` yields no results in the repo.
- **Playwright Test Results**: 
  - `example.spec.ts:5:7 › loads Engineering Notebook Dashboard cleanly` -> PASSED
  - `example.spec.ts:24:7 › verifies tab navigation and data loading` -> PASSED
  - `meta.spec.ts:3:5 › asserts displayed samples and band counts match live /api/meta` -> PASSED
  - `screenshots.spec.ts:3:5 › take screenshots and verify React tabs` -> PASSED

## D. Report
- A skeleton report has been created at `docs/report.docx`. I am waiting for you to provide the department circular rules in `docs/report_requirements.txt` before generating the full draft and PDF.

## E. Claims Ledger
| Claim | Value | Source | Status |
|-------|-------|--------|--------|
| Samples | 1,741 | `SELECT COUNT(*) FROM water_samples;` | Verified |
| Readings | 6,792 | `SELECT COUNT(*) FROM readings;` | Verified |
| Critical Bands | 89 | `SELECT count(*) FROM risk_scores WHERE band='Critical'` | Verified |
| Unmatched Districts | 10 missing | `staging_kaggle_l3_habitations` fuzzy match | Verified |
| Iron 0.3 Pooled rho | 0.548 (p=0.004) | `registry_query_v3.py` script output | Verified |
| Iron 1.0 Pooled rho | 0.349 (p=0.081) | `sensitivity_iron.py` script output | Verified |

