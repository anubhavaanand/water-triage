from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import District, RiskScore, State, Village, WaterSample
from ..schemas import DistrictSummary
from .helpers import band_counts

router = APIRouter(prefix="/districts", tags=["districts"])


def district_summaries(db: Session, name: str | None = None) -> list[DistrictSummary]:
    q = (
        db.query(
            District,
            State.name.label("state_name"),
            func.count(RiskScore.id),
            func.avg(RiskScore.score),
        )
        .join(State)
        .join(Village)
        .join(WaterSample)
        .outerjoin(RiskScore, RiskScore.sample_id == WaterSample.id)
        .group_by(District.id, State.name)
        .order_by(func.avg(RiskScore.score).desc().nullslast())
    )
    if name:
        q = q.filter(District.name.ilike(name))
    rows = q.all()

    bands_raw = (
        db.query(District.id, RiskScore.band)
        .join(Village)
        .join(WaterSample)
        .join(RiskScore)
        .all()
    )
    per_district: dict[int, dict[str, int]] = {}
    for district_id, band in bands_raw:
        per_district.setdefault(district_id, {"Critical": 0, "High": 0, "Medium": 0, "Low": 0})
        if band in per_district[district_id]:
            per_district[district_id][band] += 1

    return [
        DistrictSummary(
            id=d.id,
            name=d.name,
            state=state_name,
            sample_count=count,
            avg_score=round(float(avg), 2) if avg is not None else None,
            band_counts=per_district.get(d.id, {}),
        )
        for (d, state_name, count, avg) in rows
    ]


@router.get("", response_model=list[DistrictSummary])
def list_districts(db: Session = Depends(get_session)):
    return district_summaries(db)


@router.get("/{district_id}", response_model=DistrictSummary)
def get_district(district_id: int, db: Session = Depends(get_session)):
    d = db.query(District).filter(District.id == district_id).first()
    if d is None:
        raise HTTPException(404, "district not found")
    matches = [s for s in district_summaries(db, d.name) if s.id == district_id]
    if not matches:
        raise HTTPException(404, "no samples for district")
    return matches[0]
