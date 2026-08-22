from sqlalchemy.orm import Session

from ..models import BisParameter, Reading, RiskScore, WaterSample
from .scoring import BIS_10500, composite_score


def seed_bis_parameters(session: Session) -> int:
    existing = {p.key for p in session.query(BisParameter).all()}
    created = 0
    for key, spec in BIS_10500.items():
        if key in existing:
            continue
        session.add(
            BisParameter(
                key=key,
                label=spec["label"],
                unit=spec["unit"],
                acceptable_limit=spec["acceptable"],
                permissible_limit=spec["permissible"],
                weight=spec["weight"],
                strategy=spec.get("strategy", "threshold"),
            )
        )
        created += 1
    session.commit()
    return created


def load_bis_specs(session: Session) -> dict[str, dict]:
    specs = {}
    for p in session.query(BisParameter).all():
        specs[p.key] = {
            "label": p.label,
            "unit": p.unit,
            "acceptable": p.acceptable_limit,
            "permissible": p.permissible_limit,
            "weight": p.weight,
            "strategy": p.strategy,
        }
    return specs


def compute_scores(session: Session) -> int:
    specs = load_bis_specs(session)
    samples = session.query(WaterSample).all()
    count = 0

    for sample in samples:
        readings = {
            r.parameter_key: (r.value, specs[r.parameter_key])
            for r in session.query(Reading).filter_by(sample_id=sample.id).all()
            if r.parameter_key in specs
        }
        if not readings:
            continue
        score, band, worst = composite_score(readings)
        existing = session.query(RiskScore).filter_by(sample_id=sample.id).one_or_none()
        if existing is None:
            existing = RiskScore(sample_id=sample.id)
            session.add(existing)
        existing.score = score
        existing.band = band
        existing.worst_parameter = worst
        count += 1

    session.commit()
    return count
