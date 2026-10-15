"""Load WQMIS crawler output (records_enriched.jsonl or records.jsonl) into PostgreSQL and score.

Automatically promotes `inferred_district` (resolving 302 of 354 "Not available" districts via
20 single-district Lab IDs) and `extracted_location` (+284 villages extracted from `source`)
when `records_enriched.jsonl` is present or when `--use-enriched` is enabled (default).

Run: cd backend && DATABASE_URL=... uv run python -m etl.load_wqmis
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.engine import compute_scores, seed_bis_parameters
from app.models import District, Reading, State, Village, WaterSample

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "wqmis"
ENRICHED_JSONL = RAW_DIR / "records_enriched.jsonl"
RAW_JSONL = RAW_DIR / "records.jsonl"

CANONICAL_STATE = {"UTTAR PRADESH": "Uttar Pradesh", "BIHAR": "Bihar"}

DISTRICT_ALIASES = {
    "kaimur (bhabua)": "Kaimur (Bhabua)",
    "kaimur": "Kaimur (Bhabua)",
    "raebareli": "Rae Bareli",
    "rae bareli": "Rae Bareli",
    "barabanki": "Bara Banki",
    "bara banki": "Bara Banki",
    "lakhimpur kheri": "Kheri",
    "maharajganj": "Mahrajganj",
    "shravasti": "Shrawasti",
    "siddharth nagar": "Siddharthnagar",
    "sant kabeer nagar": "Sant Kabir Nagar",
    "sant ravidas nagar": "Bhadohi",
    "allahabad": "Prayagraj",
    "faizabad": "Ayodhya",
    "jyotiba phule nagar": "Amroha",
    "mahamaya nagar": "Hathras",
    "kanshiram nagar": "Kasganj",
    "panchsheel nagar": "Hapur",
    "prabuddha nagar": "Shamli",
    "bhimnagar": "Sambhal",
}

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
    "sulphate": "sulphate",
    "sulfate": "sulphate",
}

_PARENTHETICAL = re.compile(r"\([^)]*\)")


def normalize_param(label: str) -> str:
    """Lowercase, drop assay markers and the '(as XX)' analyte qualifier."""
    norm = _PARENTHETICAL.sub(" ", label.lower().replace("*", " "))
    return re.sub(r"\s+", " ", norm).strip()


def map_param(label: str | None) -> str | None:
    if not label:
        return None
    return PARAM_ALIASES.get(normalize_param(label))


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value))


def normalize_district_name(raw_dist: str | None) -> str:
    if not raw_dist:
        return "Not available"
    cleaned = re.sub(r"\s+", " ", str(raw_dist)).strip()
    low = cleaned.lower()
    if low in ("not available", "unknown", "na", ""):
        return "Not available"
    if low in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[low]
    return cleaned


def upsert_geo(db: Session, record: dict, use_enriched: bool = True):
    state_name = CANONICAL_STATE.get(record["state"], record["state"])
    raw_dist = (
        record.get("inferred_district") or record.get("district")
        if use_enriched
        else record.get("district")
    )
    district_name = clip(normalize_district_name(raw_dist), 100) or "Not available"

    raw_vil = (
        record.get("extracted_location") or record.get("village")
        if use_enriched
        else record.get("village")
    )
    village_name = clip(raw_vil, 150) or "UNKNOWN"

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


def load_all(db: Session, use_enriched: bool | None = None) -> dict:
    if use_enriched is None:
        use_enriched = os.environ.get("WQMIS_USE_ENRICHED", "1") != "0"

    source_jsonl = ENRICHED_JSONL if (use_enriched and ENRICHED_JSONL.exists()) else RAW_JSONL
    inserted = skipped_no_results = duplicates = duplicate_readings = 0

    existing_refs = {
        r for (r,) in db.query(WaterSample.wqmis_ref).all() if r
    }

    for line in source_jsonl.open(encoding="utf-8"):
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

        seen_params = {}
        for key, value in mapped:
            if key in seen_params:
                duplicate_readings += 1
            else:
                seen_params[key] = value

        ref = record.get("wqmis_sample_id")
        if ref and ref in existing_refs:
            duplicates += 1
            continue
        if ref:
            existing_refs.add(ref)

        village = upsert_geo(db, record, use_enriched=use_enriched)
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
        "source_file": source_jsonl.name,
        "inserted": inserted,
        "duplicates": duplicates,
        "duplicate_readings": duplicate_readings,
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
