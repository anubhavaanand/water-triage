from sqlalchemy.orm import Session

from ..models import (
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
        score_row = (
            db.query(RiskScore).filter_by(sample_id=latest.id).one_or_none()
        )
        readings = db.query(Reading).filter(Reading.sample_id == latest.id).all()
        for r in readings:
            spec = specs.get(r.parameter_key)
            if spec is None:
                continue
            acceptable = spec["acceptable"]
            permissible = spec.get("permissible")
            if spec.get("strategy") == "range":
                exceeds = not (acceptable <= r.value <= (permissible or 8.5))
            elif spec.get("strategy") == "microbial":
                exceeds = r.value > acceptable
            elif permissible is None or permissible <= acceptable:
                exceeds = r.value > acceptable
            else:
                exceeds = r.value > acceptable
            if exceeds:
                severity = min(
                    1.0,
                    max(
                        0.0,
                        (r.value - acceptable)
                        / ((permissible or acceptable * 2) - acceptable or 1),
                    ),
                ) or 1.0
                current_exceedances[r.parameter_key] = round(severity, 3)

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
    results: list[VillageRecurrence] = []
    candidate_ids = [
        v_id for (v_id,) in db.query(HistoricalContamination.village_id).distinct().limit(5000)
    ]
    for v_id in candidate_ids:
        rec = village_recurrence(db, v_id)
        if rec and rec.recurrence_score > 0:
            results.append(rec)
    results.sort(key=lambda r: r.recurrence_score, reverse=True)
    return results[:limit]
