from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_session
from ..engine import compute_scores
from ..models import District, RiskScore, State, Village, WaterSample
from ..schemas import CompareOut, PriorityItem, StateCompare

router = APIRouter(tags=["scoring"])


def priority_items(db: Session) -> list[PriorityItem]:
    rows = (
        db.query(RiskScore, WaterSample, Village, District, State)
        .join(WaterSample, RiskScore.sample_id == WaterSample.id)
        .join(Village, WaterSample.village_id == Village.id)
        .join(District, Village.district_id == District.id)
        .join(State, District.state_id == State.id)
        .order_by(desc(RiskScore.score))
        .all()
    )
    items = [
        PriorityItem(
            rank=0,
            sample_id=rs.sample_id,
            village=village.name,
            block=village.block,
            district=district.name,
            state=state.name,
            score=rs.score,
            band=rs.band,
            worst_parameter=rs.worst_parameter,
            collected_on=sample.collected_on,
        )
        for (rs, sample, village, district, state) in rows
    ]
    band_rank = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}
    items.sort(key=lambda i: (band_rank[i.band], i.score), reverse=True)
    for rank, item in enumerate(items, start=1):
        item.rank = rank
    return items


@router.get("/priority", response_model=list[PriorityItem])
def get_priority(
    state: str | None = None,
    band: str | None = None,
    db: Session = Depends(get_session),
):
    items = priority_items(db)
    if state:
        items = [i for i in items if i.state.lower() == state.lower()]
    if band:
        items = [i for i in items if i.band.lower() == band.lower()]
    return items


@router.get("/priority/top/{n}", response_model=list[PriorityItem])
def get_priority_top(n: int, db: Session = Depends(get_session)):
    return priority_items(db)[:n]


@router.post("/scoring/recompute")
def recompute(db: Session = Depends(get_session)):
    count = compute_scores(db)
    return {"recomputed": count}


@router.get("/compare", response_model=CompareOut)
def compare_states(db: Session = Depends(get_session)):
    states = db.query(State).order_by(State.name).all()
    out = []

    for state in states:
        rows = (
            db.query(RiskScore.band, RiskScore.score)
            .join(WaterSample, RiskScore.sample_id == WaterSample.id)
            .join(Village, WaterSample.village_id == Village.id)
            .join(District, Village.district_id == District.id)
            .filter(District.state_id == state.id)
            .all()
        )
        if not rows:
            continue
        bands = [b for b, _ in rows]
        worst_params = (
            db.query(RiskScore.worst_parameter, func_cnt())
            .join(WaterSample, RiskScore.sample_id == WaterSample.id)
            .join(Village, WaterSample.village_id == Village.id)
            .join(District, Village.district_id == District.id)
            .filter(District.state_id == state.id, RiskScore.worst_parameter.isnot(None))
            .group_by(RiskScore.worst_parameter)
            .order_by(desc(func_cnt()))
            .first()
        )
        out.append(
            StateCompare(
                state=state.name,
                sample_count=len(rows),
                avg_score=round(sum(s for _, s in rows) / len(rows), 2),
                critical_count=bands.count("Critical"),
                high_count=bands.count("High"),
                top_exceedance_parameter=worst_params[0] if worst_params else None,
            )
        )

    return CompareOut(states=out)


def func_cnt():
    from sqlalchemy import func

    return func.count(RiskScore.id)
