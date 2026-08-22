from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..database import get_session
from ..models import District, Reading, RiskScore, State, Village, WaterSample
from ..schemas import SampleDetailOut, SampleOut
from .helpers import reading_units

router = APIRouter(prefix="/samples", tags=["samples"])


@router.get("", response_model=list[SampleOut])
def list_samples(
    district: str | None = None,
    band: str | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_session),
):
    q = (
        db.query(WaterSample)
        .join(Village)
        .join(District)
        .join(State)
        .outerjoin(RiskScore)
        .options(joinedload(WaterSample.village))
    )
    if district:
        q = q.filter(District.name.ilike(district))
    if band:
        q = q.filter(RiskScore.band == band.capitalize())
    rows = (
        q.order_by(WaterSample.collected_on.desc()).limit(limit).offset(offset).all()
    )
    return [
        SampleOut(
            id=s.id,
            village=s.village.name,
            district=s.village.district.name,
            state=s.village.district.state.name,
            source_type=s.source_type,
            collected_on=s.collected_on,
            wqmis_ref=s.wqmis_ref,
        )
        for s in rows
    ]


@router.get("/{sample_id}", response_model=SampleDetailOut)
def get_sample(sample_id: int, db: Session = Depends(get_session)):
    sample = (
        db.query(WaterSample)
        .options(
            joinedload(WaterSample.village),
            joinedload(WaterSample.readings),
            joinedload(WaterSample.risk_score),
        )
        .filter(WaterSample.id == sample_id)
        .first()
    )
    if sample is None:
        raise HTTPException(404, "sample not found")

    units = reading_units(db)
    return SampleDetailOut(
        id=sample.id,
        village=sample.village.name,
        district=sample.village.district.name,
        state=sample.village.district.state.name,
        source_type=sample.source_type,
        collected_on=sample.collected_on,
        wqmis_ref=sample.wqmis_ref,
        readings=[
            {
                "parameter_key": r.parameter_key,
                "value": r.value,
                "unit": units.get(r.parameter_key),
                "label": None,
            }
            for r in sample.readings
        ],
        risk_score=sample.risk_score,
    )
