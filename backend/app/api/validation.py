from collections import defaultdict
import csv
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_session

router = APIRouter(prefix="/validation", tags=["validation"])

IN_SCOPE = ("Uttar Pradesh", "Bihar")

STATE_ALIAS = {
    "uttarpradesh": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "bihar": "Bihar",
}

PH_RANGE = (6.5, 8.5)
REPO_ROOT = Path(__file__).resolve().parents[3]
VAL_DIR = REPO_ROOT / "data" / "validation_reports"


def _load_cgwb_fallback_from_files() -> tuple[list[dict], dict[str, list[str]]]:
    """Reads CGWB 2012-2021 pH compliance from raw CSVs or CGWB_State_Validation.csv when DB table is empty."""
    gw_dir = REPO_ROOT / "data" / "raw" / "kaggle" / "gw_quality_2012_2021"
    ph_rows: list[dict] = []
    present = {st: ["conductivity", "ph", "temperature"] for st in IN_SCOPE}

    if gw_dir.exists():
        bucket: dict[tuple[str, int], list[int]] = defaultdict(lambda: [0, 0])
        for year in range(2012, 2022):
            if year == 2020:
                continue
            fpath = gw_dir / f"Ground Water {year}.csv"
            if not fpath.exists():
                continue
            with fpath.open("r", encoding="latin1", errors="ignore") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    raw_st = (r.get("STATE") or "").strip().lower()
                    st = STATE_ALIAS.get(raw_st)
                    if st not in IN_SCOPE:
                        continue
                    try:
                        pmin = float(r.get("pH Min") or 0)
                        pmax = float(r.get("pH Max") or 0)
                        pmean = (pmin + pmax) / 2.0
                    except ValueError:
                        continue
                    b = bucket[(st, year)]
                    b[0] += 1
                    if not (PH_RANGE[0] <= pmean <= PH_RANGE[1]):
                        b[1] += 1
        for st in IN_SCOPE:
            for (s_key, yr), (n, exc) in sorted(bucket.items()):
                if s_key != st:
                    continue
                ph_rows.append(
                    {
                        "state": st,
                        "year": yr,
                        "readings": n,
                        "exceeded": exc,
                        "exceed_pct": round(100.0 * exc / n, 1) if n else None,
                    }
                )
        if ph_rows:
            return ph_rows, present

    csv_fallback = VAL_DIR / "CGWB_State_Validation.csv"
    if csv_fallback.exists():
        with csv_fallback.open("r", encoding="utf-8", errors="ignore") as f:
            for r in csv.DictReader(f):
                st = r.get("state")
                if st not in IN_SCOPE:
                    continue
                yr = int(r.get("year") or 0)
                n = int(r.get("stations") or 0)
                pct = float(r.get("ph_exceed_pct") or 0.0)
                exc = round(n * pct / 100.0)
                ph_rows.append(
                    {
                        "state": st,
                        "year": yr,
                        "readings": n,
                        "exceeded": exc,
                        "exceed_pct": pct,
                    }
                )
    return ph_rows, present


def _load_master_and_wq6() -> tuple[dict, list[dict]]:
    wq6_summary = {}
    wq6_path = VAL_DIR / "wq6_district_summary.json"
    if wq6_path.exists():
        try:
            wq6_summary = json.loads(wq6_path.read_text(encoding="utf-8"))
        except Exception:
            wq6_summary = {}

    master_rows: list[dict] = []
    for st in ("Uttar Pradesh", "Bihar"):
        mpath = VAL_DIR / f"Master_Validation_{st}.csv"
        if not mpath.exists():
            continue
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
    return wq6_summary, master_rows


@router.get("/cgwb")
def list_cgwb_ph(db: Session = Depends(get_session)):
    """CGWB groundwater pH compliance + 113-district WQ6 & Master Validation ground truth."""
    ph_rows: list[dict] = []
    present: dict[str, set[str]] = defaultdict(set)

    try:
        rows = db.execute(
            text("SELECT state, year, parameter, value FROM cgwb_readings")
        ).fetchall()
    except Exception:
        rows = []

    if rows:
        ph = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        for state, year, parameter, value in rows:
            state = STATE_ALIAS.get((state or "").lower())
            if state not in IN_SCOPE:
                continue
            present[state].add(parameter)
            if parameter != "ph" or year is None:
                continue
            bucket = ph[state][year]
            bucket[0] += 1
            if value is not None and not (PH_RANGE[0] <= value <= PH_RANGE[1]):
                bucket[1] += 1

        for state in IN_SCOPE:
            years = ph.get(state) or {}
            for year in sorted(years):
                n, exceeded = years[year]
                ph_rows.append(
                    {
                        "state": state,
                        "year": year,
                        "readings": n,
                        "exceeded": exceeded,
                        "exceed_pct": round(100.0 * exceeded / n, 1) if n else None,
                    }
                )
        avail_out = {state: sorted(present.get(state, [])) for state in IN_SCOPE}
    else:
        ph_rows, avail_out = _load_cgwb_fallback_from_files()

    wq6_summary, master_rows = _load_master_and_wq6()

    return {
        "ph": ph_rows,
        "available_parameters": avail_out,
        "years": sorted({r["year"] for r in ph_rows}),
        "wq6_summary": wq6_summary,
        "master_districts": master_rows,
    }


@router.get("/districts")
def list_master_validation_districts():
    """Returns all 113 canonical districts (75 UP + 38 Bihar) with WQMIS, IMIS, and WQ6 counts."""
    wq6_summary, master_rows = _load_master_and_wq6()
    return {
        "total_districts": len(master_rows),
        "wq6_summary": wq6_summary,
        "districts": master_rows,
    }
