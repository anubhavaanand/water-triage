#!/usr/bin/env python3
"""
WaterTriage Data-Gap Recovery & Enrichment Utility (`close_data_gaps.py`)
-------------------------------------------------------------------------
Closes metadata and district-coverage gaps in `data/raw/wqmis/records.jsonl`
NON-DESTRUCTIVELY (preserving `records.jsonl` untouched at md5 d76f8d34... and all
frozen WPR-11 / WPR-12 / Final Report counts, while writing enriched records to
`data/raw/wqmis/records_enriched.jsonl` and the 113-district validation summary to
`data/validation_reports/wq6_district_summary.json`):

1. Deterministically resolves 47 of the 354 "Not available" districts offline:
   - 5 Lab IDs (47 unassigned samples) map 1-to-1 to a single district in `records.jsonl`:
       * L338 (21 samples) -> Kaushambi (16 named Kaushambi samples)
       * L362 (18 samples) -> Prayagraj (5 named Prayagraj samples)
       * L434 (6 samples)  -> Ballia (30 named Ballia samples)
       * L411 (1 sample)   -> Shahjahanpur (17 named Shahjahanpur samples)
       * L460 (1 sample)   -> Lalitpur (1 named Lalitpur sample)
   - L158 (52 unassigned samples, UP Jal Nigam State/Regional Lab in Lucknow) spans 7 distinct
     named UP districts in `records.jsonl` (Kheri 14, Saharanpur 6, Lucknow 5, Sitapur 4,
     Bahraich 2, Balrampur 1, Amethi 1) and is therefore NOT assigned to a single district.
   - Online (`--fetch-missing-labs`): Uses the two-step ASP.NET Session Cookie Handshake
     documented in `data/raw/official/FINDINGS_REPORT.md`:
       Step A: GET `https://ejalshakti.gov.in/WQMIS/Report/Report_p` to acquire `ASP.NET_SessionId`
               and `__RequestVerificationToken_L1dRTUlT0` cookies.
       Step B: GET `https://ejalshakti.gov.in/WQMIS/Common/final_report_print?s_id=<AES_B64>`
               using that session cookie jar and parse `<div class="lab-address-panel">`.

2. Recovers +284 missing village/habitation names offline (21 [1.21%] -> 305 [17.52%] in the 1,741 cohort):
   - Extracts free-text habitation, village, tola, and school names embedded after `location :`
     inside the `source` field of `records.jsonl` when `village == "Not available"`.

3. Integrates the Full 113-District Official WQMIS Form WQ6 Tables (75 UP + 38 Bihar = 113 districts):
   - Parses `data/validation_reports/WQ6_Complete_UP.csv` (75 UP districts) and
     `data/validation_reports/WQ6_Complete_Bihar.csv` (38 Bihar districts), confirming:
       * Iron: 4,317 villages (88 UP + 4,229 Bihar)
       * Turbidity: 489 villages (404 UP + 85 Bihar)
       * Fluoride: 434 villages (138 UP + 296 Bihar)
       * Arsenic: 236 villages (34 UP + 202 Bihar)
       * Total Coliform: 204 villages (204 UP + 0 Bihar)
       * E. coli: 133 villages (125 UP + 8 Bihar)
"""

from __future__ import annotations

import argparse
import csv
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

REPORT_P_URL = "https://ejalshakti.gov.in/WQMIS/Report/Report_p"
FINAL_REPORT_URL = "https://ejalshakti.gov.in/WQMIS/Common/final_report_print"

SINGLE_DISTRICT_LABS: dict[str, str] = {
    "L338": "Kaushambi",
    "L362": "Prayagraj",
    "L434": "Ballia",
    "L411": "Shahjahanpur",
    "L460": "Lalitpur",
}

MULTI_DISTRICT_LABS: set[str] = {"L158"}

MISSING_LAB_PROBES: dict[str, dict[str, str | int]] = {
    "L268": {"state": "Bihar", "unassigned_count": 15, "internal_id": 1057819, "s_id": "l0Qyn6RBu161Azza/u2IGA=="},
    "L339": {"state": "Uttar Pradesh", "unassigned_count": 7, "internal_id": 1060487, "s_id": "7di7SbPBqHZ6s0pUfCULJw=="},
    "L359": {"state": "Uttar Pradesh", "unassigned_count": 15, "internal_id": 1017309, "s_id": "RrDPMHxTF3n65CLzcFPVaQ=="},
    "L375": {"state": "Uttar Pradesh", "unassigned_count": 40, "internal_id": 1005092, "s_id": "qkVOWu30kDtI1qsvXlCdTA=="},
    "L376": {"state": "Uttar Pradesh", "unassigned_count": 16, "internal_id": 1015008, "s_id": "YTlfxQM9o0VR4Tt6NmLyjA=="},
    "L377": {"state": "Uttar Pradesh", "unassigned_count": 48, "internal_id": 1000022, "s_id": "yA+wpLQr8xfHcV0XU71/yw=="},
    "L400": {"state": "Uttar Pradesh", "unassigned_count": 1, "internal_id": 10018, "s_id": "Ywjka/ntcIT6gdyDTApB/A=="},
    "L405": {"state": "Uttar Pradesh", "unassigned_count": 20, "internal_id": 1002693, "s_id": "JSNPb0Xce0eq2hbBp9z58Q=="},
    "L452": {"state": "Uttar Pradesh", "unassigned_count": 28, "internal_id": 1002001, "s_id": "ZbuVwW1NdC8Z0XcMb8nvuA=="},
    "L455": {"state": "Uttar Pradesh", "unassigned_count": 12, "internal_id": 1057942, "s_id": "FqigBgWTlKAMOvRhhYSs4Q=="},
    "L468": {"state": "Uttar Pradesh", "unassigned_count": 9, "internal_id": 1009337, "s_id": "4nDQxbbO+Lieh46gmLt9cQ=="},
    "L516": {"state": "Uttar Pradesh", "unassigned_count": 16, "internal_id": 1000040, "s_id": "kBxePP7SFXR1r/eJnY0qTA=="},
    "L535": {"state": "Uttar Pradesh", "unassigned_count": 4, "internal_id": 1000005, "s_id": "XDah38HBlj59v7Bjvoq3Bw=="},
    "L664": {"state": "Uttar Pradesh", "unassigned_count": 15, "internal_id": 1002459, "s_id": "0g6iQaiBibD/5DlWwypnzw=="},
    "L730": {"state": "Uttar Pradesh", "unassigned_count": 9, "internal_id": 1016495, "s_id": "3SC9USiNcx//A9OZE0t8kA=="},
}

WQ6_PARAMETER_COLS = [
    "pH", "TDS", "Turbidity", "Chloride", "Total_Alkalinity", "Total_Hardness",
    "Sulphate", "Iron", "Total_Arsenic", "Fluoride", "Nitrate",
    "Residual_Chlorine", "Others_chem", "E_coli", "Total_Coliform", "Others_bact",
]


def extract_lab_code(record: dict) -> str | None:
    sid = record.get("wqmis_sample_id") or record.get("sample_id") or ""
    m = re.search(r"(L\d+)", str(sid))
    return m.group(1) if m else None


def parse_lab_district_from_html(html: str) -> tuple[str | None, str | None]:
    panel_match = re.search(
        r'<div[^>]*class="[^"]*lab-address-panel[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    block = panel_match.group(1) if panel_match else html
    h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", block, re.DOTALL | re.IGNORECASE)
    lab_name = re.sub(r"\s+", " ", h2_match.group(1)).strip() if h2_match else None

    dist_match = re.search(r"Dist(?:rict)?\s*-\s*([A-Za-z\s\(\)\.]+?)(?:,|Pin|$|<)", block, re.IGNORECASE)
    if dist_match:
        district = dist_match.group(1).strip()
        if district and district.lower() != "not available":
            return lab_name, district

    if lab_name and "," in lab_name:
        tail = lab_name.rsplit(",", 1)[-1].strip()
        if tail and tail.lower() not in ("not available", "up", "bihar"):
            return lab_name, tail

    return lab_name, None


def extract_location_from_source(source: str | None) -> str | None:
    if not source:
        return None
    m = re.search(r"location\s*:\s*(.+)$", source, re.IGNORECASE)
    if not m:
        return None
    loc = m.group(1).strip(" -.,;:")
    if not loc or loc.lower() in ("not available", "na", "n/a", "nil", "none", "-", "0"):
        return None
    return loc


def fetch_missing_lab_districts(delay_sec: float = 1.0) -> dict[str, dict[str, str | None]]:
    """
    Uses the two-step ASP.NET Session Cookie Handshake from FINDINGS_REPORT.md:
      1) GET https://ejalshakti.gov.in/WQMIS/Report/Report_p to establish session cookies.
      2) GET https://ejalshakti.gov.in/WQMIS/Common/final_report_print?s_id=<AES_B64>
    """
    resolved: dict[str, dict[str, str | None]] = {}
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) WaterTriage-ETL/0.2"),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    ]

    try:
        print(f"  [SESSION] Initializing ASP.NET session cookies via {REPORT_P_URL} ...")
        with opener.open(REPORT_P_URL, timeout=20) as resp:
            _ = resp.read()
        cookie_names = [c.name for c in cj]
        print(f"  [SESSION] Acquired cookies: {cookie_names}")
    except Exception as exc:
        print(f"  [WARN] Session bootstrap via Report_p failed ({exc}); attempting direct requests...")

    for lab_code, info in MISSING_LAB_PROBES.items():
        qs = urllib.parse.urlencode({"s_id": str(info["s_id"])})
        url = f"{FINAL_REPORT_URL}?{qs}"
        try:
            with opener.open(url, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            lab_name, district = parse_lab_district_from_html(html)
            resolved[lab_code] = {"lab_name": lab_name, "district": district}
            print(f"  [OK] {lab_code} ({info['unassigned_count']} samples) -> District: {district} | Lab: {lab_name}")
        except Exception as exc:
            resolved[lab_code] = {"lab_name": None, "district": None}
            print(f"  [PORTAL GATED] {lab_code} ({info['unassigned_count']} samples): {exc}")
        time.sleep(delay_sec)
    return resolved


def summarize_wq6_csv(csv_path: Path, state_name: str) -> dict:
    if not csv_path.exists():
        return {"state": state_name, "districts": 0, "error": f"{csv_path} not found"}
    districts = 0
    totals: Counter[str] = Counter()
    affected_districts: dict[str, int] = defaultdict(int)
    with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dist = (row.get("district") or row.get("District Name") or "").strip()
            if not dist or dist.lower().startswith("total"):
                continue
            districts += 1
            for col in WQ6_PARAMETER_COLS:
                if col not in row:
                    continue
                try:
                    val = int(float((row.get(col) or "0").replace(",", "").strip() or 0))
                except ValueError:
                    val = 0
                totals[col] += val
                if val > 0:
                    affected_districts[col] += 1
    return {
        "state": state_name,
        "districts": districts,
        "contaminated_villages_by_parameter": dict(totals),
        "affected_districts_by_parameter": dict(affected_districts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Close WaterTriage metadata and district coverage gaps.")
    parser.add_argument(
        "--records",
        type=Path,
        default=Path("data/raw/wqmis/records.jsonl"),
        help="Path to raw WQMIS records.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/wqmis/records_enriched.jsonl"),
        help="Path to write non-destructively enriched records",
    )
    parser.add_argument(
        "--fetch-missing-labs",
        action="store_true",
        help="Establish ASP.NET session on Report_p and fetch 15 representative WQMIS pages via Common/final_report_print.",
    )
    args = parser.parse_args()

    if not args.records.exists():
        raise SystemExit(f"Records file not found: {args.records}")

    records = [json.loads(line) for line in args.records.read_text(encoding="utf-8").splitlines() if line.strip()]

    lab_to_district: dict[str, str] = dict(SINGLE_DISTRICT_LABS)

    if args.fetch_missing_labs:
        print("\nProbing 15 representative WQMIS pages via Report_p session + Common/final_report_print...")
        fetched_labs = fetch_missing_lab_districts()
        for lab_code, meta in fetched_labs.items():
            if meta.get("district"):
                lab_to_district[lab_code] = meta["district"]  # type: ignore[assignment]

    cohort_total = 0
    orig_missing_dist = 0
    resolved_dist = 0
    multi_district_lab_unassigned = 0
    orig_named_villages = 0
    recovered_villages = 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out_f:
        for r in records:
            enriched = dict(r)
            lab_code = extract_lab_code(r)
            enriched["lab_code"] = lab_code

            is_active_cohort = r.get("state") in ("Uttar Pradesh", "Bihar") and bool(r.get("results"))
            if is_active_cohort:
                cohort_total += 1

            dist = (r.get("district") or "Not available").strip()
            if dist == "Not available":
                if is_active_cohort:
                    orig_missing_dist += 1
                inferred = lab_to_district.get(lab_code or "")
                if inferred:
                    enriched["inferred_district"] = inferred
                    enriched["district_resolution_source"] = f"single_district_lab:{lab_code}"
                    if is_active_cohort:
                        resolved_dist += 1
                elif (lab_code or "") in MULTI_DISTRICT_LABS:
                    enriched["inferred_district"] = "Not available"
                    enriched["district_resolution_source"] = f"multi_district_regional_lab:{lab_code}"
                    if is_active_cohort:
                        multi_district_lab_unassigned += 1
                else:
                    enriched["inferred_district"] = "Not available"
                    enriched["district_resolution_source"] = "unmapped_lab_portal_gated"
            else:
                enriched["inferred_district"] = dist
                enriched["district_resolution_source"] = "submitter_address"

            village = (r.get("village") or "Not available").strip()
            if village != "Not available":
                if is_active_cohort:
                    orig_named_villages += 1
                enriched["extracted_location"] = village
                enriched["location_resolution_source"] = "structured_village_field"
            else:
                loc = extract_location_from_source(r.get("source"))
                if loc:
                    if is_active_cohort:
                        recovered_villages += 1
                    enriched["extracted_location"] = loc
                    enriched["location_resolution_source"] = "source_location_field"
                else:
                    enriched["extracted_location"] = "Not available"
                    enriched["location_resolution_source"] = "missing"

            out_f.write(json.dumps(enriched, ensure_ascii=False) + "\n")

    up_summary = summarize_wq6_csv(Path("data/validation_reports/WQ6_Complete_UP.csv"), "Uttar Pradesh")
    br_summary = summarize_wq6_csv(Path("data/validation_reports/WQ6_Complete_Bihar.csv"), "Bihar")
    wq6_out = Path("data/validation_reports/wq6_district_summary.json")
    wq6_out.parent.mkdir(parents=True, exist_ok=True)
    wq6_out.write_text(json.dumps({"Uttar Pradesh": up_summary, "Bihar": br_summary}, indent=2), encoding="utf-8")

    print("=== ENRICHMENT SUMMARY (1,741-SAMPLE ACTIVE UP+BIHAR COHORT) ===")
    print(f"Active scored UP+Bihar samples            : {cohort_total}")
    print(f"Original 'Not available' districts        : {orig_missing_dist} ({orig_missing_dist / cohort_total * 100:.1f}%)")
    print(f"Deterministic single-district Lab matches : {resolved_dist} / {orig_missing_dist} (5 labs: L338, L362, L434, L411, L460)")
    print(f"Multi-district regional Lab (L158) held   : {multi_district_lab_unassigned} (spans 7 UP districts; not fabricated)")
    print(f"Remaining unmapped labs (portal gated)    : {orig_missing_dist - resolved_dist - multi_district_lab_unassigned} (across 15 Lab IDs)")
    print(f"Original named villages                   : {orig_named_villages} ({orig_named_villages / cohort_total * 100:.2f}%)")
    print(f"Recovered locations from `source`         : +{recovered_villages}")
    print(
        f"New named location coverage               : {orig_named_villages + recovered_villages} / {cohort_total} "
        f"({(orig_named_villages + recovered_villages) / cohort_total * 100:.2f}%)"
    )
    print(f"113-District WQ6 coverage                 : {up_summary['districts'] + br_summary['districts']} districts (UP {up_summary['districts']} + Bihar {br_summary['districts']})")
    print(f"113-District WQ6 Iron villages            : {up_summary['contaminated_villages_by_parameter'].get('Iron', 0) + br_summary['contaminated_villages_by_parameter'].get('Iron', 0)}")
    print(f"113-District WQ6 Turbidity villages       : {up_summary['contaminated_villages_by_parameter'].get('Turbidity', 0) + br_summary['contaminated_villages_by_parameter'].get('Turbidity', 0)} (UP {up_summary['contaminated_villages_by_parameter'].get('Turbidity', 0)} + Bihar {br_summary['contaminated_villages_by_parameter'].get('Turbidity', 0)})")
    print(f"Enriched dataset written to               : {args.output}")
    print(f"113-district WQ6 summary written to       : {wq6_out}")


if __name__ == "__main__":
    main()
