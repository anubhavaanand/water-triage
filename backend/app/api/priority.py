from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_session
from ..engine import compute_scores
from ..models import District, RiskScore, State, Village, WaterSample
from ..schemas import CompareOut, PriorityItem, StateCompare

router = APIRouter(tags=["scoring"])


def priority_items(db: Session) -> list[PriorityItem]:
    from sqlalchemy import text
    query = text("""
        SELECT ws.id as sample_id, v.name as village, v.block, d.name as district, s.name as state,
               rs.score, rs.band, rs.worst_parameter, ws.collected_on,
               (SELECT COUNT(*) FROM readings r JOIN bis_parameters bp ON r.parameter_key = bp.key WHERE r.sample_id = ws.id AND bp.weight > 0) as n_scored_params
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        ORDER BY rs.score DESC
    """)
    rows = db.execute(query).fetchall()
    
    items = [
        PriorityItem(
            rank=0,
            sample_id=row[0],
            village=row[1] or "Unknown",
            block=row[2],
            district=row[3],
            state=row[4],
            score=row[5],
            band=row[6],
            worst_parameter=row[7],
            collected_on=row[8],
            n_scored_params=row[9]
        )
        for row in rows
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
