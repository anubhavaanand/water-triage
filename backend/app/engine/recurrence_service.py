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


def list_recurrent_districts(db: Session, limit: int = 50) -> list[VillageRecurrence]:
    """
    District-level recurrence engine.
    Returns it inside the VillageRecurrence struct to maintain API backwards compatibility.
    """
    # 1. Get historical contamination aggregated by district_id
    hist_rows = (
        db.query(
            Village.district_id,
            HistoricalContamination.parameter,
            func.array_agg(func.distinct(HistoricalContamination.year)),
        )
        .join(Village, HistoricalContamination.village_id == Village.id)
        .group_by(Village.district_id, HistoricalContamination.parameter)
        .all()
    )
    if not hist_rows:
        return []

    historical_by_district: dict[int, dict[str, list[int]]] = {}
    for d_id, param, years in hist_rows:
        historical_by_district.setdefault(d_id, {})[param.lower()] = sorted(int(y) for y in years)

    # 2. Get the latest samples for all districts
    district_ids = list(historical_by_district)
    
    # We want ALL samples in the district, because any sample in the district failing is a district failure.
    latest_samples = (
        db.query(WaterSample, Village.district_id)
        .join(Village, WaterSample.village_id == Village.id)
        .all()
    )

    exceeds_by_district: dict[int, dict[str, float]] = defaultdict(dict)
    if latest_samples:
        sample_id_to_district = {w.id: d_id for w, d_id in latest_samples}
        reading_rows = (
            db.query(Reading, BisParameter)
            .join(BisParameter, Reading.parameter_key == BisParameter.key)
            .all()
        )
        for r, bp in reading_rows:
            d_id = sample_id_to_district.get(r.sample_id)
            if not d_id:
                continue
            if _exceeds(r.value, bp.acceptable_limit, bp.permissible_limit, bp.strategy):
                exceeds_by_district[d_id][r.parameter_key] = 1.0

    # 3. Compute recurrence scores
    all_ids = set(historical_by_district) | set(exceeds_by_district)
    districts = {d.id: d for d in db.query(District).filter(District.id.in_(all_ids)).all()}
    states = {s.id: s.name for s in db.query(State).all()}

    results: list[VillageRecurrence] = []
    for d_id, historical in historical_by_district.items():
        current = exceeds_by_district.get(d_id, {})
        classifications, score = compute_recurrence(historical, current)
        if score <= 0:
            continue
        persistent_count = sum(1 for c in classifications.values() if c == "persistent")
        d = districts.get(d_id)
        results.append(
            VillageRecurrence(
                village_id=d_id,  # Overload village_id with district_id for API compatibility
                village=f"{d.name.title()} (District-Wide)",
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

# Keep village_recurrence for compatibility, but we just return None since villages don't have matching data
def village_recurrence(db: Session, village_id: int) -> VillageRecurrence | None:
    return None

