from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import (
    BisParameter,
    District,
    HistoricalContamination,
    Reading,
    RiskScore,
    State,
    Village,
    WaterSample,
)
from .pipeline import load_bis_specs as load_specs
from .recurrence import VillageRecurrence, compute_recurrence, verdict_for


def _exceeds(value: float, acceptable: float, permissible: float | None, strategy: str) -> bool:
    if strategy == "range":
        return not (acceptable <= value <= (permissible or 8.5))
    return value > acceptable


def village_recurrence(db: Session, village_id: int) -> VillageRecurrence | None:
    base = (
        db.query(Village, District, State)
        .join(District, Village.district_id == District.id)
        .join(State, District.state_id == State.id)
        .filter(Village.id == village_id)
        .first()
    )
    if base is None:
        return None
    village, district, state = base

    hist_rows = (
        db.query(HistoricalContamination.parameter, HistoricalContamination.year)
        .filter(HistoricalContamination.village_id == village_id)
        .all()
    )
    historical: dict[str, list[int]] = {}
    for param, year in hist_rows:
        historical.setdefault(param.lower(), []).append(year)

    latest = (
        db.query(WaterSample)
        .filter(WaterSample.village_id == village_id)
        .order_by(WaterSample.collected_on.desc())
        .first()
    )
    current_exceedances: dict[str, float] = {}
    if latest is not None:
        specs = load_specs(db)
        readings = db.query(Reading).filter(Reading.sample_id == latest.id).all()
        for r in readings:
            spec = specs.get(r.parameter_key)
            if spec is None:
                continue
            if _exceeds(r.value, spec["acceptable"], spec.get("permissible"), spec.get("strategy", "threshold")):
                current_exceedances[r.parameter_key] = 1.0

    classifications, score = compute_recurrence(historical, current_exceedances)
    persistent_count = sum(1 for c in classifications.values() if c == "persistent")

    return VillageRecurrence(
        village_id=village.id,
        village=village.name.title(),
        district=district.name.title(),
        state=state.name,
        historical=historical,
        current_exceedances=current_exceedances,
        classifications=classifications,
        recurrence_score=score,
        verdict=verdict_for(score, persistent_count),
    )


def list_recurrent_villages(db: Session, limit: int = 50) -> list[VillageRecurrence]:
    hist_rows = (
        db.query(
            HistoricalContamination.village_id,
            HistoricalContamination.parameter,
            func.array_agg(func.distinct(HistoricalContamination.year)),
        )
        .group_by(HistoricalContamination.village_id, HistoricalContamination.parameter)
        .all()
    )
    if not hist_rows:
        return []

    historical_by_village: dict[int, dict[str, list[int]]] = {}
    for v_id, param, years in hist_rows:
        historical_by_village.setdefault(v_id, {})[param.lower()] = sorted(int(y) for y in years)

    village_ids = list(historical_by_village)
    latest_sub = (
        db.query(
            WaterSample.village_id.label("vid"),
            func.max(WaterSample.collected_on).label("latest"),
        )
        .filter(WaterSample.village_id.in_(village_ids))
        .group_by(WaterSample.village_id)
        .subquery()
    )
    latest_samples = (
        db.query(WaterSample)
        .join(
            latest_sub,
            (WaterSample.village_id == latest_sub.c.vid)
            & (WaterSample.collected_on == latest_sub.c.latest),
        )
        .all()
    )

    exceeds_by_village: dict[int, dict[str, float]] = defaultdict(dict)
    if latest_samples:
        sample_to_village = {w.id: w.village_id for w in latest_samples}
        reading_rows = (
            db.query(Reading, BisParameter)
            .join(BisParameter, Reading.parameter_key == BisParameter.key)
            .filter(Reading.sample_id.in_(list(sample_to_village)))
            .all()
        )
        for r, bp in reading_rows:
            v_id = sample_to_village[r.sample_id]
            if _exceeds(r.value, bp.acceptable_limit, bp.permissible_limit, bp.strategy):
                exceeds_by_village[v_id][r.parameter_key] = 1.0

    all_ids = set(historical_by_village) | set(exceeds_by_village)
    villages = {v.id: v for v in db.query(Village).filter(Village.id.in_(all_ids)).all()}
    districts = {
        d.id: d
        for d in db.query(District).filter(
            District.id.in_({v.district_id for v in villages.values() if v})
        ).all()
    }
    states = {s.id: s.name for s in db.query(State).all()}

    results: list[VillageRecurrence] = []
    for v_id, historical in historical_by_village.items():
        current = exceeds_by_village.get(v_id, {})
        classifications, score = compute_recurrence(historical, current)
        if score <= 0:
            continue
        persistent_count = sum(1 for c in classifications.values() if c == "persistent")
        v = villages.get(v_id)
        d = districts.get(v.district_id) if v else None
        results.append(
            VillageRecurrence(
                village_id=v_id,
                village=v.name.title() if v else f"Village {v_id}",
                district=d.name.title() if d else "",
                state=states.get(d.state_id, "") if d else "",
                historical=historical,
                current_exceedances=current,
                classifications=classifications,
                recurrence_score=score,
                verdict=verdict_for(score, persistent_count),
            )
        )

    results.sort(key=lambda r: r.recurrence_score, reverse=True)
    return results[:limit]
