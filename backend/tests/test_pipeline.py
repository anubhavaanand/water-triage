from datetime import datetime, timezone

from app.database import SessionLocal
from app.engine import compute_scores
from app.models import District, Village, WaterSample, Reading


def test_compute_scores_duplicate_readings_no_typeerror(db):
    """Duplicate parameter readings for one sample must not crash scoring.

    Previously pipeline.py compared severity (float) to the spec dict
    (index [1] instead of [2]), raising TypeError when a sample had
    duplicate readings for the same parameter.
    """
    district = db.query(District).filter(District.name == "Unnao").one()
    village = Village(district_id=district.id, name="Dup Readings Test")
    db.add(village)
    db.flush()
    ws = WaterSample(
        village_id=village.id,
        source_type="handpump",
        collected_on=datetime(2022, 6, 1, tzinfo=timezone.utc),
        wqmis_ref="TEST-DUP-READINGS-1",
    )
    db.add(ws)
    db.flush()
    # Two readings for the same parameter with different values
    db.add(Reading(sample_id=ws.id, parameter_key="iron", value=0.2))
    db.add(Reading(sample_id=ws.id, parameter_key="iron", value=0.5))
    db.commit()
    try:
        count = compute_scores(db)
        assert count >= 1
        from app.models import RiskScore
        rs = (
            db.query(RiskScore)
            .filter(RiskScore.sample_id == ws.id)
            .one_or_none()
        )
        assert rs is not None
    finally:
        db.query(Reading).filter(Reading.sample_id == ws.id).delete()
        db.query(WaterSample).filter(WaterSample.id == ws.id).delete()
        if village.id:
            db.query(Village).filter(Village.id == village.id).delete()
        db.commit()
