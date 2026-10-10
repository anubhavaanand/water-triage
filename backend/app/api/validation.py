from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_session

router = APIRouter(prefix="/validation", tags=["validation"])

# The corpus covers only these two states.
IN_SCOPE = ("Uttar Pradesh", "Bihar")

# cgwb_readings.state stores raw OCR-ish lowercase names, including the
# echoed duplicates 'up'/'uttarpradesh' and a national 'total' row.
STATE_ALIAS = {
    "uttarpradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "bihar": "Bihar",
}

# BIS IS 10500 acceptable pH range, mirrored so the exceedance count is
# self-describing. The scoring engine owns the authoritative copy.
PH_RANGE = (6.5, 8.5)


@router.get("/cgwb")
def list_cgwb_ph(db: Session = Depends(get_session)):
    """CGWB groundwater pH compliance for the two corpus states.

    This is independent of the WQMIS crawl, so it is a genuine external check.
    Aggregated in Python because cgwb_readings.state carries OCR'd aliases
    ('up' vs 'uttarpradesh', plus a national 'total' row) that must be folded
    before counting, and SQLite has no initcap/upper helpers available.
    """
    try:
        rows = db.execute(
            text("SELECT state, year, parameter, value FROM cgwb_readings")
        ).fetchall()
    except Exception:
        # Optional table: a fresh database may not have it loaded yet.
        return {
            "ph": [],
            "available_parameters": {},
            "years": [],
        }

    # state -> year -> [ph_readings, ph_exceeding]
    ph = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    # state -> set of parameter keys present
    present = defaultdict(set)

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

    ph_rows = []
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

    return {
        "ph": ph_rows,
        "available_parameters": {
            state: sorted(present.get(state, [])) for state in IN_SCOPE
        },
        "years": sorted({r["year"] for r in ph_rows}),
    }
