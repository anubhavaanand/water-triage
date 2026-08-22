# WQMIS Data Access — Reverse Engineering Findings

> Verified live on 17 Aug 2026 · All findings reproducible with plain curl + openssl

## TL;DR

**Individual lab test reports are fully public and enumerable** (`final_report_print?s_id=<AES(id)>`), 20M+ records, complete structure. Aggregate/drill-down report endpoints require a (free) login session whose registration is CAPTCHA-gated → manual step for the user, then automation takes over.

## Confirmed facts

### 1. Client-side crypto (extracted from `/WQMIS/Scripts/frmValidate.js`)

```js
key = '8080808080808080'; iv = same; AES-128-CBC / PKCS7
enCriptedAES(value) -> base64 ciphertext   // identical to URL s_id encoding
```

Replication (openssl):
```bash
printf '%s' "$ID" | openssl enc -aes-128-cbc \
  -K 38303830383038303830383038303830 \
  -iv 38303830383038303830383038303830 -nosalt -base64
```

### 2. Public endpoints (no login)

| Endpoint | Method | Notes |
|----------|--------|-------|
| `GET /WQMIS/Report/Report_p` | GET | Issues `__RequestVerificationToken` + cookie |
| `POST /WQMIS/Common/District_Bind_without_session` | POST | body: `state_id=<AES>` + token → JSON districts ✅ verified (UP→76 districts, Unnao=482, Bihar state_id=5) |
| `POST /WQMIS/Common/GetVillage_Bind_without_session` | POST | same pattern |
| `GET /WQMIS/Common/final_report_print?s_id=<AES>` | GET | **Full lab report** ✅ verified at ids 1 … 20,000,000 |

State IDs (from page): UP=31, Bihar=5. Parameter IDs: Fluoride=11, Iron=19, Nitrate=13, TDS=8, Arsenic=26, E.coli=34.

### 3. Session-gated endpoints (302 → Error without login)

- `POST /WQMIS/Report/get_Report_Parameter_wise` (fy, stid, dtid, blid, gpid, ParameterId — all AES)
- `POST /WQMIS/Report/get_report_parameter_wise_list_detail` (+ p_type, villid)
- These return DataTables JSON — the efficient targeted path **if** a session cookie is provided.

### 4. Report page structure (per sample)

Contains: Sample Id (`U<user>L<lab>S<seq>`), Village/GP/Block/District/State, lat/long fields,
collection/receipt/analysis dates, lab name+address, and the results table with
**parameter | unit | BIS acceptable | BIS permissible | measured value** — exactly our
`readings` schema. Parseable with regex/BeautifulSoup.

## Acquisition plan (chosen)

| Path | Effort | Verdict |
|------|--------|---------|
| A. User registers free WQMIS account → share session cookie → we automate detail endpoints per district×parameter×FY | ~10 min user, then fully automated | ⭐ preferred |
| B. User logs in, uses UI Export-to-Excel per district (state-wide: ~114 districts × FY) → drop files in `data/raw/wqmis/` | ~45 min manual | fallback, zero risk |
| C. Sequential crawl of `final_report_print`, filter locally | weeks, ~0.8% hit-rate over 20M+ ids | ❌ rejected (impolite + infeasible) |

Politeness rules for any automated fetching: ≤1 req/sec, single-threaded, off-peak windows,
identify honestly, cache everything under `data/raw/wqmis/`.

## Next actions

1. [USER] Register at `ejalshakti.gov.in/WQMIS/Home/login_register` (public user role), note credentials
2. [USER→AGENT] Share session cookie OR export district-wise Excel files manually (all UP+Bihar preferred; 6-district demo subset minimum)
3. [AGENT] Build `backend/etl/wqmis.py`: cookie/token flow + AES helpers + parser → `water_samples`
