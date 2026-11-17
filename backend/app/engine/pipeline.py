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


def score_sample(session: Session, sample_id: int) -> dict | None:
    """Compute the risk score for one sample without persisting it.

    Mirrors the aggregation and scoring used by compute_scores so that a
    per-sample result always matches what the batch job stored. Returns None
    when the sample does not exist, and a zero-score payload when it has no
    scorable readings.
    """
    specs = load_bis_specs(session)
    sample = session.query(WaterSample).filter_by(id=sample_id).one_or_none()
    if sample is None:
        return None

    readings_raw = (
        session.query(Reading)
        .filter_by(sample_id=sample.id)
        .filter(Reading.parameter_key.in_(specs.keys()))
        .all()
    )

    readings: dict[str, tuple[float, dict, float]] = {}
    for r in readings_raw:
        spec = specs[r.parameter_key]
        severity = _severity_for_value(r.value, spec)
        if r.parameter_key not in readings or severity > readings[r.parameter_key][2]:
            readings[r.parameter_key] = (r.value, spec, severity)

    breakdown = [
        {
            "parameter_key": key,
            "label": spec["label"],
            "value": value,
            "unit": spec["unit"],
            "acceptable": spec["acceptable"],
            "permissible": spec["permissible"],
            "weight": spec["weight"],
            "severity": round(severity, 4),
            "exceeded": severity > 0.0,
        }
        for key, (value, spec, severity) in sorted(readings.items())
    ]

    if not readings:
        return {
            "sample_id": sample.id,
            "score": 0.0,
            "band": "Low",
            "worst_parameter": None,
            "n_scored_params": 0,
            "breakdown": [],
            "note": "sample has no readings for scored parameters",
        }

    scored = {k: (v, s) for k, (v, s, _) in readings.items()}
    score, band, worst = composite_score(scored)

    return {
        "sample_id": sample.id,
        "score": score,
        "band": band,
        "worst_parameter": worst,
        "n_scored_params": len(scored),
        "breakdown": breakdown,
    }


def compute_scores(session: Session) -> int:
    specs = load_bis_specs(session)
    samples = session.query(WaterSample).all()
    count = 0

    for sample in samples:
        readings_raw = (
            session.query(Reading)
            .filter_by(sample_id=sample.id)
            .filter(Reading.parameter_key.in_(specs.keys()))
            .all()
        )
        # Aggregate duplicate parameter readings by max severity (defensible for risk)
        readings = {}
        for r in readings_raw:
            spec = specs[r.parameter_key]
            severity = _severity_for_value(r.value, spec)
            if r.parameter_key not in readings or severity > readings[r.parameter_key][2]:
                readings[r.parameter_key] = (r.value, spec, severity)

        # Convert to expected format: (value, spec)
        readings_for_scoring = {k: (v, s) for k, (v, s, _) in readings.items()}

        if not readings_for_scoring:
            continue
        score, band, worst = composite_score(readings_for_scoring)
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


def _severity_for_value(value: float, spec: dict) -> float:
    """Compute severity for a single reading value using BIS spec."""
    from .scoring import parameter_severity

    result = parameter_severity(
        value,
        spec["acceptable"],
        spec.get("permissible"),
        spec.get("strategy", "threshold"),
    )
    return result.severity
