"""load_all must not leave committed rows behind when scoring fails."""

import pytest
from sqlalchemy import text

from app.database import SessionLocal
from etl import load_wqmis


def _count(db, table):
    return db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def test_load_all_rolls_back_when_scoring_fails(monkeypatch):
    db = SessionLocal()
    try:
        before_samples = _count(db, "water_samples")
        before_readings = _count(db, "readings")

        def boom(_session):
            raise RuntimeError("simulated scoring failure")

        monkeypatch.setattr(load_wqmis, "compute_scores", boom)

        with pytest.raises(RuntimeError, match="simulated scoring failure"):
            load_wqmis.load_all(db)

        assert _count(db, "water_samples") == before_samples
        assert _count(db, "readings") == before_readings
    finally:
        db.close()
