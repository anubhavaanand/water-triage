# WQMIS National Baseline — FY 2026-27 (as on 22/08/2026)

> Captured from public WQMIS dashboard by user, Aug 2026.
> Purpose: validate our ETL pulls + scoring output against official aggregates.

## Lab Testing

| Metric | UP | Bihar | India |
|--------|----|----|-------|
| Labs | 145 | 123 | 2,850 |
| Samples received | 2,06,111 | 55,103 | 26,89,813 |
| Samples tested | 2,06,016 | 55,095 | 26,88,797 |
| **Contaminated** | **1,575** | **11** | **57,223** |
| Remedial action taken | 1,215 | 7 | 14,954 |
| NABL labs | 120 | 39 | 1,748 |

## FTK Testing

| Metric | UP | Bihar | India |
|--------|----|----|-------|
| Villages FTK-tested | 63,419 | 3,885 | 2,28,400 |
| FTK tests done | 11,41,466 | 31,360 | 44,87,082 |

## Validation checks for our pipeline

1. Contamination rate FY26-27: UP ≈ 0.76% (1575/206016), Bihar ≈ 0.02% (11/55095)
   - Our scoring on pulled data should reproduce roughly this ratio per district sums
   - Bihar being ultra-clean matches earlier WQ6 PDF findings
2. Expected scale: if FY26-27 alone is 2.6L UP samples, multi-year pull could be
   several million rows nationally; UP+Bihar subset likely 15-30L rows → fine for Postgres
3. FTK vs lab gap: UP does 5.5× more FTK than lab tests — ETL must tag `source_type`
   (lab vs FTK) because FTK readings are less reliable; weight or flag accordingly
4. Remedial-action coverage: UP acted on 77% of contaminated (1215/1575), Bihar 64%
   - Our `/api/priority` queue should show similar top-of-funnel counts pre-intervention
