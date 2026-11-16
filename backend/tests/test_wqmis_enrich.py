"""upsert_geo must honour the enriched fields regardless of the branch.

The original expression
    record.get("inferred_district") or record.get("district") if use_enriched else ...
parses as
    (record.get("inferred_district") or record.get("district")) if use_enriched else ...
so use_enriched=False silently dropped inferred_district. These tests pin the
intended reading: prefer the enriched value, fall back to the raw one.
"""

from app.database import SessionLocal
from app.models import District, State, Village
from etl.load_wqmis import upsert_geo


def _record(**over):
    rec = {
        "state": "Uttar Pradesh",
        "district": "Unnao",
        "village": "Bangarmau",
        "source": "Hand Pump",
        "collected_on": "2022-08-17",
    }
    rec.update(over)
    return rec


def test_inferred_district_used_when_enriched():
    db = SessionLocal()
    try:
        v = upsert_geo(db, _record(inferred_district="Rae Bareli"), use_enriched=True)
        assert v.district.name == "Rae Bareli"
    finally:
        db.close()


def test_raw_district_used_when_not_enriched():
    """use_enriched=False means "ignore the enriched fields".

    The old expression dropped inferred_district in this branch too, which
    was harmless by accident rather than by design. This pins the intended
    semantic explicitly.
    """
    db = SessionLocal()
    try:
        v = upsert_geo(db, _record(inferred_district="Rae Bareli"), use_enriched=False)
        assert v.district.name == "Unnao"
    finally:
        db.close()


def test_falls_back_to_district_when_no_inferred():
    db = SessionLocal()
    try:
        v = upsert_geo(db, _record(district="Hardoi"), use_enriched=True)
        assert v.district.name == "Hardoi"
    finally:
        db.close()


def test_extracted_location_preferred():
    db = SessionLocal()
    try:
        v = upsert_geo(
            db, _record(extracted_location="Rampur Bujurg"), use_enriched=True
        )
        assert v.name == "Rampur Bujurg"
    finally:
        db.close()
