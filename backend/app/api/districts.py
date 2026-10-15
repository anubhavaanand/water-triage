import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import District, Reading, RiskScore, State, Village, WaterSample
from ..schemas import DistrictDetail, DistrictSummary, VillageSummary
from .helpers import get_district_or_404

router = APIRouter(tags=["geography"])

ROOT = Path(__file__).resolve().parents[3]


@router.get("/districts/full-triage")
def get_full_113_district_triage(
    state: str | None = None,
    band: str | None = None,
):
    """Returns the complete 113-district (75 UP + 38 Bihar) multi-tier BIS IS 10500 risk triage payload."""
    triage_path = ROOT / "dashboard" / "public" / "full-113-triage.json"
    if not triage_path.exists():
        from scripts.build_full_113_district_triage import build_full_113_triage
        payload = build_full_113_triage()
    else:
        payload = json.loads(triage_path.read_text(encoding="utf-8"))

    if state or band:
        filtered = payload.get("districts", [])
        if state:
            filtered = [d for d in filtered if d.get("state", "").lower() == state.lower()]
        if band:
            filtered = [d for d in filtered if d.get("band", "").lower() == band.lower()]
        return {**payload, "districts": filtered}
    return payload


@router.get("/states", response_model=list[str])
def list_states(db: Session = Depends(get_session)):
    rows = db.query(State.name).order_by(State.name).all()
    return [r[0] for r in rows]


@router.get("/districts", response_model=list[DistrictSummary])
def list_districts(state: str | None = None, db: Session = Depends(get_session)):
    q = (
        db.query(
            District.id,
            District.name,
            State.name.label("state"),
            func.count(WaterSample.id).label("samples"),
            func.avg(RiskScore.score).label("avg_score"),
        )
        .join(State, District.state_id == State.id)
        .outerjoin(Village, Village.district_id == District.id)
        .outerjoin(WaterSample, WaterSample.village_id == Village.id)
        .outerjoin(RiskScore, RiskScore.sample_id == WaterSample.id)
        .group_by(District.id, District.name, State.name)
        .order_by(State.name, District.name)
    )
    if state:
        q = q.filter(func.lower(State.name) == state.lower())

    out = []
    for d_id, d_name, s_name, samples, avg in q.all():
        crit = (
            db.query(func.count(RiskScore.id))
            .join(WaterSample, RiskScore.sample_id == WaterSample.id)
            .join(Village, WaterSample.village_id == Village.id)
            .filter(Village.district_id == d_id, RiskScore.band == "Critical")
            .scalar()
            or 0
        )
        out.append(
            DistrictSummary(
                id=d_id,
                name=d_name,
                state=s_name,
                sample_count=samples or 0,
                critical_count=crit,
                avg_score=round(float(avg), 2) if avg is not None else 0.0,
            )
        )
    return out


@router.get("/districts/{district_id}", response_model=DistrictDetail)
def get_district(district_id: int, db: Session = Depends(get_session)):
    district = get_district_or_404(db, district_id)
    villages_out = []
    scores_all: list[float] = []
    crit_total = 0

    for village in district.villages:
        latest_sample = (
            db.query(WaterSample)
            .filter_by(village_id=village.id)
            .order_by(WaterSample.collected_on.desc())
            .first()
        )
        score_val = None
        band_val = None
        worst_val = None
        collected = None
        if latest_sample and latest_sample.risk_score:
            rs = latest_sample.risk_score
            score_val = rs.score
            band_val = rs.band
            worst_val = rs.worst_parameter
            collected = latest_sample.collected_on
            scores_all.append(rs.score)
            if rs.band == "Critical":
                crit_total += 1

        villages_out.append(
            VillageSummary(
                id=village.id,
                name=village.name,
                block=village.block,
                latest_score=score_val,
                latest_band=band_val,
                worst_parameter=worst_val,
                last_sampled_on=collected,
            )
        )

    villages_out.sort(key=lambda v: (v.latest_score is None, -(v.latest_score or 0)))
    avg_score = round(sum(scores_all) / len(scores_all), 2) if scores_all else 0.0

    return DistrictDetail(
        id=district.id,
        name=district.name,
        state=district.state.name,
        sample_count=len(scores_all),
        critical_count=crit_total,
        avg_score=avg_score,
        villages=villages_out,
    )
