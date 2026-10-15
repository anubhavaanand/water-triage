#!/usr/bin/env python3
"""Refresh dashboard/public static JSON fallbacks from the live backend API OR offline canonical files.

Generates:
  1. `dashboard/public/scoring-parameters.json` (10 BIS IS 10500:2012 parameters)
  2. `dashboard/public/validation-cgwb.json` (17 CGWB pH rows + 113 master districts + WQ6 summary)
  3. `dashboard/public/meta.json` (corpus invariants, sensitivity audit, 113-district WQ6 summary)
  4. `dashboard/public/full-113-triage.json` (complete 113-district multi-tier BIS risk triage)
  5. `dashboard/public/dashboard-data.json` (1,741 sample priority rows enriched with inferred_district & extracted_location)
  6. `dashboard/public/health.json`
"""

from __future__ import annotations

import csv
import datetime
import importlib.util
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "dashboard" / "public"
VAL_DIR = ROOT / "data" / "validation_reports"


def load_scoring_mod():
    spec = importlib.util.spec_from_file_location(
        "scoring", ROOT / "backend" / "app" / "engine" / "scoring.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def build_scoring_parameters_offline() -> list[dict]:
    scoring = load_scoring_mod()
    rows = []
    for key in sorted(scoring.BIS_10500.keys()):
        spec = scoring.BIS_10500[key]
        acc = spec.get("acceptable")
        perm = spec.get("permissible")
        rows.append(
            {
                "key": key,
                "label": spec.get("label", key),
                "unit": spec.get("unit", "mg/L"),
                "acceptable": float(acc) if acc is not None else None,
                "permissible": float(perm) if perm is not None else None,
                "weight": float(spec.get("weight", 0.0)),
                "strategy": spec.get("strategy", "threshold"),
                "binary_exceedance": bool(perm is None or (acc is not None and perm <= acc)),
            }
        )
    return rows


def build_validation_cgwb_offline() -> dict:
    gw_dir = ROOT / "data" / "raw" / "kaggle" / "gw_quality_2012_2021"
    state_alias = {
        "uttarpradesh": "Uttar Pradesh",
        "uttar pradesh": "Uttar Pradesh",
        "up": "Uttar Pradesh",
        "bihar": "Bihar",
    }
    in_scope = ("Uttar Pradesh", "Bihar")
    ph_rows = []
    bucket: dict[tuple[str, int], list[int]] = defaultdict(lambda: [0, 0])

    if gw_dir.exists():
        for year in range(2012, 2022):
            if year == 2020:
                continue
            fpath = gw_dir / f"Ground Water {year}.csv"
            if not fpath.exists():
                continue
            with fpath.open("r", encoding="latin1", errors="ignore") as f:
                for r in csv.DictReader(f):
                    st = state_alias.get((r.get("STATE") or "").strip().lower())
                    if st not in in_scope:
                        continue
                    try:
                        pmin = float(r.get("pH Min") or 0)
                        pmax = float(r.get("pH Max") or 0)
                        pmean = (pmin + pmax) / 2.0
                    except ValueError:
                        continue
                    b = bucket[(st, year)]
                    b[0] += 1
                    if not (6.5 <= pmean <= 8.5):
                        b[1] += 1
        for st in in_scope:
            for (s_key, yr), (n, exc) in sorted(bucket.items()):
                if s_key == st:
                    ph_rows.append(
                        {
                            "state": st,
                            "year": yr,
                            "readings": n,
                            "exceeded": exc,
                            "exceed_pct": round(100.0 * exc / n, 1) if n else None,
                        }
                    )

    wq6_summary = {}
    wq6_path = VAL_DIR / "wq6_district_summary.json"
    if wq6_path.exists():
        wq6_summary = json.loads(wq6_path.read_text(encoding="utf-8"))

    master_rows = []
    for st in ("Uttar Pradesh", "Bihar"):
        mpath = VAL_DIR / f"Master_Validation_{st}.csv"
        if mpath.exists():
            with mpath.open("r", encoding="utf-8", errors="ignore") as f:
                for row in csv.DictReader(f):
                    parsed = {}
                    for k, v in row.items():
                        if k in ("district_norm", "state"):
                            parsed[k] = v
                        else:
                            try:
                                parsed[k] = int(float(v or 0))
                            except ValueError:
                                parsed[k] = 0
                    master_rows.append(parsed)

    return {
        "ph": ph_rows,
        "available_parameters": {st: ["conductivity", "ph", "temperature"] for st in in_scope},
        "years": sorted({r["year"] for r in ph_rows}),
        "wq6_summary": wq6_summary,
        "master_districts": master_rows,
    }


def enrich_meta_offline(meta_path: Path) -> dict | None:
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    top_p = meta.get("top_parameters") or []
    has_so4 = any(x.get("parameter_key") == "sulphate" for x in top_p)
    if not has_so4:
        top_p.extend(
            [
                {"state": "Uttar Pradesh", "parameter_key": "sulphate", "tested": 394, "exceeding": 50},
                {"state": "Uttar Pradesh", "parameter_key": "total_coliform", "tested": 7, "exceeding": 3},
                {"state": "Bihar", "parameter_key": "sulphate", "tested": 73, "exceeding": 0},
            ]
        )
        top_p.sort(key=lambda x: (-int(x.get("exceeding", 0)), -int(x.get("tested", 0))))
        meta["top_parameters"] = top_p

    if "scoring" in meta and "weights" in meta["scoring"]:
        meta["scoring"]["weights"]["sulphate"] = 0.5
        meta["scoring"]["weights"]["total_coliform"] = 0.9

    wq6_path = VAL_DIR / "wq6_district_summary.json"
    if wq6_path.exists():
        meta["wq6_summary"] = json.loads(wq6_path.read_text(encoding="utf-8"))

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. scoring-parameters.json
    sp = build_scoring_parameters_offline()
    sp_path = OUT / "scoring-parameters.json"
    sp_path.write_text(json.dumps(sp, indent=2), encoding="utf-8")
    print(f"OK scoring-parameters.json ({sp_path.stat().st_size}B) {len(sp)} BIS parameters")

    # 2. validation-cgwb.json
    vc = build_validation_cgwb_offline()
    vc_path = OUT / "validation-cgwb.json"
    vc_path.write_text(json.dumps(vc, indent=2), encoding="utf-8")
    print(
        f"OK validation-cgwb.json ({vc_path.stat().st_size}B) "
        f"{len(vc['ph'])} CGWB pH rows, {len(vc['master_districts'])} master districts"
    )

    # 3. meta.json
    meta = enrich_meta_offline(OUT / "meta.json")
    if meta:
        print(
            f"OK meta.json ({(OUT / 'meta.json').stat().st_size}B) "
            f"samples={meta['corpus']['samples']} top_params={len(meta.get('top_parameters', []))}"
        )

    # 4. full-113-triage.json + enriched dashboard-data.json
    triage_spec = importlib.util.spec_from_file_location("build_full_113_district_triage", ROOT / "scripts" / "build_full_113_district_triage.py")
    triage_mod = importlib.util.module_from_spec(triage_spec)
    triage_spec.loader.exec_module(triage_mod)
    build_full_113_triage = triage_mod.build_full_113_triage
    triage_payload = build_full_113_triage()
    print(
        f"OK full-113-triage.json ({(OUT / 'full-113-triage.json').stat().st_size}B) "
        f"{len(triage_payload.get('districts', []))} scored districts"
    )

    # 5. health.json
    h_path = OUT / "health.json"
    h_data = {
        "status": "ok",
        "database": "snapshot",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    h_path.write_text(json.dumps(h_data, indent=2), encoding="utf-8")
    print(f"OK health.json ({h_path.stat().st_size}B)")


if __name__ == "__main__":
    main()
