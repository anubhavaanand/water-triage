#!/usr/bin/env python3
"""WaterTriage data-gap recovery and enrichment (non-destructive).

Recovered 2026-10-14. The version circulated earlier (Downloads/close_data_gaps.py)
had four defects that made it resolve nothing, all verified against records.jsonl:

1. It read `r.get("sample_id")`; the field is `wqmis_sample_id`. Every lab-code
   lookup returned None, so `lab_to_district` was only ever the six hardcoded entries.
2. `summarize_wq6_csv` read a `District Name` column and only counted columns whose
   name contains "Villages". The WQ6 CSVs use a `district` column and plain
   parameter names (`Iron`, `Fluoride`, ...), so it produced 0 districts and no counts.
3. It iterated all 1,822 lines of records.jsonl. 81 of those have no `results`
   payload; the analysable corpus is the 1,741 that do. Both totals are reported.
4. `KNOWN_LAB_DISTRICTS` maps L158 -> Lucknow. L158 is a State/Regional lab whose 38
   named-district records span 11 districts (Kheri 14, Saharanpur 6, Lucknow 5, ...),
   so it is not a district proxy. It is applied only where a lab has exactly one named
   district, and the count of such labs is reported instead of assumed.

Non-destructive by construction: writes records_enriched.jsonl and
wq6_district_summary.json, never overwrites records.jsonl.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

KNOWN_LAB_DISTRICTS: dict[str, str] = {
    "L338": "Kaushambi",
    "L362": "Prayagraj",
    "L434": "Ballia",
    "L411": "Shahjahanpur",
    "L460": "Lalitpur",
}
LABS_NOT_A_DISTRICT_PROXY = {"L158"}
WQ6_COLUMNS = [
    "pH", "TDS", "Turbidity", "Chloride", "Total_Alkalinity", "Total_Hardness",
    "Sulphate", "Iron", "Total_Arsenic", "Fluoride", "Nitrate", "Residual_Chlorine",
    "Others_chem", "E_coli", "Total_Coliform", "Others_bact",
]


def extract_lab_code(sample_id: str | None) -> str | None:
    if not sample_id:
        return None
    m = re.search(r"(L\d+)", sample_id)
    return m.group(1) if m else None


def extract_location_from_source(source: str | None) -> str | None:
    """Habitation/village/tola name after `location :` in the WQMIS source field."""
    if not source:
        return None
    m = re.search(r"location\s*:\s*(.+)$", source, re.IGNORECASE)
    if not m:
        return None
    loc = m.group(1).strip(" -.,;:")
    if not loc or loc.lower() in ("not available", "na", "n/a", "nil", "none", "-", "0"):
        return None
    return loc


def summarize_wq6_csv(csv_path: Path, state_name: str) -> dict:
    """Sum per-parameter contaminated-village counts across districts.

    The WQ6 CSVs carry one row per district with a `district` column and bare
    parameter names.
    """
    if not csv_path.exists():
        return {"state": state_name, "districts": 0, "error": f"{csv_path} not found"}
    districts = 0
    totals: Counter = Counter()
    affected: defaultdict = defaultdict(int)
    with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dist = (row.get("district") or "").strip()
            if not dist or dist.lower().startswith("total"):
                continue
            districts += 1
            for col in WQ6_COLUMNS:
                raw = (row.get(col) or "0").replace(",", "").strip()
                try:
                    val = int(float(raw or 0))
                except ValueError:
                    val = 0
                totals[col] += val
                if val > 0:
                    affected[col] += 1
    return {
        "state": state_name,
        "districts": districts,
        "contaminated_villages_by_parameter": dict(totals),
        "affected_districts_by_parameter": dict(affected),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Close WaterTriage metadata and coverage gaps.")
    ap.add_argument("--records", type=Path, default=Path("data/raw/wqmis/records.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("data/raw/wqmis/records_enriched.jsonl"))
    ap.add_argument("--wq6-dir", type=Path, default=Path("data/validation_reports"))
    ap.add_argument("--summary", type=Path,
                   default=Path("data/validation_reports/wq6_district_summary.json"))
    args = ap.parse_args()

    if not args.records.exists():
        raise SystemExit(f"Records file not found: {args.records}")

    records = [json.loads(l) for l in
               args.records.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = [r for r in records if r.get("results")]
    print(f"Loaded {len(records)} lines from {args.records} ({len(scored)} carry a results payload)")

    # --- Step 1: derive lab -> district from records that already carry a district ---
    named_by_lab: defaultdict = defaultdict(Counter)
    for r in records:
        lc = extract_lab_code(r.get("wqmis_sample_id"))
        dist = (r.get("district") or "").strip()
        if lc and dist and dist != "Not available":
            named_by_lab[lc][dist] += 1

    lab_to_district: dict[str, str] = {}
    ambiguous: dict[str, list[tuple[str, int]]] = {}
    for lc, counts in named_by_lab.items():
        if len(counts) == 1:
            lab_to_district[lc] = next(iter(counts))
        else:
            ambiguous[lc] = counts.most_common()
    # Hardcoded entries only where the lab is not contradicted by the data.
    for lc, dist in KNOWN_LAB_DISTRICTS.items():
        if lc not in ambiguous and lc not in lab_to_district:
            lab_to_district[lc] = dist

    print("\n=== Lab -> district resolution ===")
    print(f"  labs with exactly one named district (safe to inherit): {len(lab_to_district)}")
    print(f"  labs spanning >1 district (NOT resolvable): {len(ambiguous)}")
    for lc in LABS_NOT_A_DISTRICT_PROXY:
        if lc in ambiguous:
            print(f"  {lc}: {len(ambiguous[lc])} districts "
                  f"({', '.join(f'{d} {n}' for d, n in ambiguous[lc][:4])}, ...)")

    unassigned = [r for r in scored
                 if (r.get("district") or "Not available").strip() == "Not available"]
    resolved = sum(1 for r in unassigned
                   if lab_to_district.get(extract_lab_code(r.get("wqmis_sample_id")) or ""))
    print(f"  unassigned districts: {len(unassigned)} of {len(scored)} "
          f"({len(unassigned) / len(scored) * 100:.1f}%)")
    print(f"  resolvable offline from a lab's own named records: {resolved} "
          f"({resolved / len(unassigned) * 100:.1f}% of unassigned)")
    print(f"  still need a portal probe: {len(unassigned) - resolved}")

    # --- Step 2: village/location recovery ---
    orig_named = sum(1 for r in scored
                     if (r.get("village") or "Not available").strip() != "Not available")
    recovered = [r for r in scored
                 if (r.get("village") or "Not available").strip() == "Not available"
                 and extract_location_from_source(r.get("source"))]

    print("\n=== Village / location recovery ===")
    print(f"  named in the structured village field : {orig_named} "
          f"({orig_named / len(scored) * 100:.2f}%)")
    print(f"  recovered from `source` after 'location :' : +{len(recovered)}")
    print(f"  combined coverage: {orig_named + len(recovered)} / {len(scored)} "
          f"({(orig_named + len(recovered)) / len(scored) * 100:.2f}%)")

    # --- Step 3: write enriched records (raw fields preserved alongside) ---
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for r in records:
            enriched = dict(r)
            lc = extract_lab_code(r.get("wqmis_sample_id"))
            enriched["lab_code"] = lc

            dist = (r.get("district") or "Not available").strip()
            inferred = lab_to_district.get(lc or "")
            if dist == "Not available":
                enriched["inferred_district"] = inferred or "Not available"
                enriched["district_resolution_source"] = f"lab_id:{lc}" if inferred else "unresolved"
            else:
                enriched["inferred_district"] = dist
                enriched["district_resolution_source"] = "submitter_address"

            village = (r.get("village") or "Not available").strip()
            if village != "Not available":
                enriched["extracted_location"] = village
                enriched["location_resolution_source"] = "structured_village_field"
            else:
                loc = extract_location_from_source(r.get("source"))
                enriched["extracted_location"] = loc or "Not available"
                enriched["location_resolution_source"] = (
                    "source_location_field" if loc else "missing")
            out.write(json.dumps(enriched, ensure_ascii=False) + "\n")
    print(f"\nEnriched dataset written to {args.output} "
          f"(records.jsonl untouched)")

    # --- Step 4: WQ6 district summary ---
    up = summarize_wq6_csv(args.wq6_dir / "WQ6_Complete_UP.csv", "Uttar Pradesh")
    br = summarize_wq6_csv(args.wq6_dir / "WQ6_Complete_Bihar.csv", "Bihar")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps({"Uttar Pradesh": up, "Bihar": br}, indent=2), encoding="utf-8")

    print("\n=== Official WQ6 / Format L1 district tables ===")
    for label, s in (("UP", up), ("Bihar", br)):
        if "error" in s:
            print(f"  {label}: {s['error']}")
            continue
        print(f"  {label}: {s['districts']} districts")
        for param, n in sorted(s["contaminated_villages_by_parameter"].items(),
                              key=lambda kv: -kv[1]):
            if n:
                print(f"      {param:22s} {n:5d} contaminated villages "
                      f"in {s['affected_districts_by_parameter'].get(param, 0)} districts")
    print(f"  combined districts: {up.get('districts', 0) + br.get('districts', 0)}")
    print(f"WQ6 summary written to {args.summary}")


if __name__ == "__main__":
    main()
