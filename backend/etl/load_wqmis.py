"""Load WQMIS crawler output (records.jsonl) into PostgreSQL and score.

Run: cd backend && DATABASE_URL=... uv run python -m etl.load_wqmis
"""

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.engine import compute_scores, seed_bis_parameters
from app.models import District, Reading, State, Village, WaterSample

JSONL = Path(__file__).resolve().parents[2] / "data" / "raw" / "wqmis" / "records.jsonl"

CANONICAL_STATE = {"UTTAR PRADESH": "Uttar Pradesh", "BIHAR": "Bihar"}

PARAM_ALIASES = {
    "ph": "ph",
    "tds": "tds",
    "total dissolved solids": "tds",
    "fluoride": "fluoride",
    "total arsenic": "arsenic",
    "arsenic": "arsenic",
    "nitrate": "nitrate",
    "iron": "iron",
    "turbidity": "turbidity",
    "e. coli": "e_coli",
    "e.coli": "e_coli",
    "e coli": "e_coli",
    "total coliform": "total_coliform",
}


def map_param(label: str | None) -> str | None:
    if not label:
        return None
    norm = label.lower().replace("*", "").strip()
    for alias, key in PARAM_ALIASES.items():
        if alias in norm:
            return key
    return None


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value))


def upsert_geo(db: Session, record: dict):
    state_name = CANONICAL_STATE.get(record["state"], record["state"])
    district_name = clip(record["district"], 100) or "UNKNOWN"
    village_name = clip(record["village"], 150) or "UNKNOWN"

    state = db.query(State).filter_by(name=state_name).one_or_none()
    if state is None:
        state = State(name=state_name)
        db.add(state)
        db.flush()

    district = (
        db.query(District).filter_by(state_id=state.id, name=district_name).one_or_none()
    )
    if district is None:
        district = District(state_id=state.id, name=district_name)
        db.add(district)
        db.flush()

    village = (
        db.query(Village)
        .filter_by(district_id=district.id, name=village_name)
        .one_or_none()
    )
    if village is None:
        village = Village(
            district_id=district.id,
            name=village_name,
            block=(record.get("block") or "").upper() or None,
            panchayat=(record.get("gram_panchayat") or "").upper() or None,
        )
        db.add(village)
        db.flush()

    return village


def clip(value, width):
    if value is None:
        return None
    return str(value)[:width].strip() or None


def load_all(db: Session) -> dict:
    inserted = skipped_no_results = duplicates = 0

    existing_refs = {
        r for (r,) in db.query(WaterSample.wqmis_ref).all() if r
    }

    for line in JSONL.open():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)

        mapped = []
        for r in record.get("results", []):
            key = map_param(r.get("parameter"))
            if key and r.get("value") is not None:
                mapped.append((key, float(r["value"])))
        if not mapped:
            skipped_no_results += 1
            continue

        ref = record.get("wqmis_sample_id")
        if ref and ref in existing_refs:
            duplicates += 1
            continue
        if ref:
            existing_refs.add(ref)

        village = upsert_geo(db, record)
        sample = WaterSample(
            village_id=village.id,
            source_type=clip(record.get("source"), 50) or "unknown",
            collected_on=parse_dt(record.get("collected_on")) or datetime(2022, 1, 1),
            lab_name=clip(record.get("lab"), 200),
            wqmis_ref=ref,
        )
        db.add(sample)
        db.flush()
        for key, value in mapped:
            db.add(Reading(sample_id=sample.id, parameter_key=key, value=value))
        inserted += 1

    db.commit()
    scored = compute_scores(db)
    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "skipped_empty": skipped_no_results,
        "scored_total": scored,
    }


def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_bis_parameters(db)
        print(load_all(db))


if __name__ == "__main__":
    main()
