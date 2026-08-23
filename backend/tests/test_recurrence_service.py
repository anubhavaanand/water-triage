"""Integration tests for recurrence_service against the real PostgreSQL database.

Runs against postgresql://jjm_user:jjm_password@localhost:5432/jjm_triage.
Skips the whole module if the server is unreachable. Rows created by the
hotspot test are discarded via transaction rollback.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, distinct, func, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

POSTGRES_URL = "postgresql://jjm_user:jjm_password@localhost:5432/jjm_triage"
os.environ["DATABASE_URL"] = POSTGRES_URL

try:
    _engine = create_engine(POSTGRES_URL)
    with _engine.connect() as _conn:
        _conn.execute(text("SELECT 1"))
except Exception as exc:  # pragma: no cover - depends on local services
    pytest.skip(f"PostgreSQL unavailable at {POSTGRES_URL}: {exc}", allow_module_level=True)

from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.engine.recurrence_service import (  # noqa: E402
    list_recurrent_villages,
    village_recurrence,
)
from app.models import (  # noqa: E402
    District,
    HistoricalContamination,
    Reading,
    Village,
    WaterSample,
)

TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    yield


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _seed_persistent_hotspot(db):
    """Create (uncommitted) a village whose history overlaps current exceedances."""
    district_id = db.query(District.id).first()[0]
    village = Village(district_id=district_id, name="zz-recurrence-hotspot")
    db.add(village)
    db.flush()
    db.add_all(
        [
            HistoricalContamination(village_id=village.id, parameter="ARSENIC", year=year)
            for year in (2009, 2010, 2011, 2012)
        ]
        + [
            HistoricalContamination(village_id=village.id, parameter="FLUORIDE", year=year)
            for year in (2010, 2011, 2012, 2013)
        ]
    )
    sample = WaterSample(
        village_id=village.id,
        source_type="handpump",
        collected_on=datetime.now(timezone.utc),
        lab_name="pytest",
    )
    db.add(sample)
    db.flush()
    db.add_all(
        [
            Reading(sample_id=sample.id, parameter_key="arsenic", value=0.12),
            Reading(sample_id=sample.id, parameter_key="fluoride", value=2.4),
        ]
    )
    db.flush()
    return village.id


def test_village_recurrence_known_hotspot(db):
    vid = (
        db.query(HistoricalContamination.village_id)
        .group_by(HistoricalContamination.village_id)
        .having(func.count() >= 6)
        .order_by(func.count().desc())
        .limit(1)
        .one()
    )[0]

    real_rec = village_recurrence(db, vid)
    assert real_rec is not None
    assert real_rec.historical
    assert real_rec.recurrence_score > 0

    rec = village_recurrence(db, _seed_persistent_hotspot(db))
    assert rec is not None
    assert rec.verdict in {"chronic-hotspot", "recurring"}
    assert rec.historical
    assert rec.recurrence_score > 0


def test_village_recurrence_no_history(db):
    row = (
        db.query(WaterSample.village_id)
        .filter(
            WaterSample.village_id.notin_(
                db.query(distinct(HistoricalContamination.village_id))
            )
        )
        .first()
    )
    if row is None:
        pytest.skip("no sampled village without history in dataset")
    rec = village_recurrence(db, row[0])
    assert rec is not None
    assert set(rec.classifications) <= set(rec.current_exceedances)
    assert rec.verdict in {"watchlist", "no-history"}


def test_village_recurrence_missing_returns_none(db):
    assert village_recurrence(db, 99999999) is None


def test_list_recurrent_sorted_desc(db):
    results = list_recurrent_villages(db, limit=10)
    assert len(results) <= 10
    scores = [r.recurrence_score for r in results]
    assert scores == sorted(scores, reverse=True)
