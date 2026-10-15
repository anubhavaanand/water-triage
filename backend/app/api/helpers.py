from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import BisParameter, District


def reading_units(db: Session) -> dict[str, str]:
    return {p.key: p.unit for p in db.query(BisParameter).all()}


def band_counts(scores) -> dict[str, int]:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for (_, band) in scores:
        if band in counts:
            counts[band] += 1
    return counts


def get_district_or_404(db: Session, district_id: int) -> District:
    district = db.get(District, district_id)
    if district is None:
        raise HTTPException(status_code=404, detail=f"District {district_id} not found")
    return district
