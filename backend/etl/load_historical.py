"""Load the Quality-Affected Habitations registry (UP+Bihar) into PostgreSQL.

Source: data/raw/kaggle/affected_areas_2009_2012/IndiaAffectedWaterQualityAreas.csv
Run:    cd backend && uv run python -m etl.load_historical
"""

import re
from pathlib import Path

import pandas as pd

from app.database import Base, SessionLocal, engine
from app.models import District, HistoricalContamination, State, Village

CSV = Path(__file__).resolve().parents[2] / "data" / "raw" / "kaggle" / \
    "affected_areas_2009_2012" / "IndiaAffectedWaterQualityAreas.csv"

TARGET_STATES = {"UTTAR PRADESH", "BIHAR"}


def clean_name(value: str) -> str:
    value = str(value).strip()
    return re.sub(r"\s*\(\d+\)\s*", "", value).strip().upper()


def clean_village(value: str) -> str:
    value = clean_name(value)
    return re.sub(r"\s+", " ", value)


def main():
    Base.metadata.create_all(bind=engine)

    df = pd.read_csv(CSV, encoding="latin-1")
    df["State Name"] = df["State Name"].str.upper().str.strip()
    ub = df[df["State Name"].isin(TARGET_STATES)].copy()
    print(f"registry rows total={len(df):,} up+bihar={len(ub):,}")

    inserted_events = 0
    with SessionLocal() as db:
        states: dict[str, State] = {s.name: s for s in db.query(State).all()}
        districts: dict[tuple[int, str], District] = {
            (d.state_id, d.name): d for d in db.query(District).all()}
        villages: dict[tuple[int, str], Village] = {
            (v.district_id, v.name): v for v in db.query(Village).all()}

        pending: list[HistoricalContamination] = []
        seen_events: set[tuple[int, str, int, str]] = set()

        for row in ub.itertuples(index=False):
            state_name = row[0]
            district_name = clean_name(row[1])
            block_name = clean_name(row[2])
            village_name = clean_village(row[4])
            habitation = clean_village(row[5]) if pd.notna(row[5]) else None
            parameter = str(row[6]).strip()
            year = int(str(row[7])[-4:])

            state = states.get(state_name)
            if state is None:
                state = State(name=state_name)
                db.add(state)
                db.flush()
                states[state_name] = state

            dkey = (state.id, district_name)
            district = districts.get(dkey)
            if district is None:
                district = District(state_id=state.id, name=district_name)
                db.add(district)
                db.flush()
                districts[dkey] = district

            vkey = (district.id, village_name)
            village = villages.get(vkey)
            if village is None:
                village = Village(
                    district_id=district.id, name=village_name,
                    block=block_name or None,
                )
                db.add(village)
                db.flush()
                villages[vkey] = village

            ekey = (village.id, parameter.upper(), year, (habitation or "").upper())
            if ekey in seen_events:
                continue
            seen_events.add(ekey)
            pending.append(HistoricalContamination(
                village_id=village.id,
                parameter=parameter.upper(),
                year=year,
                habitation=habitation,
            ))
            inserted_events += 1

            if len(pending) >= 5000:
                db.bulk_save_objects(pending)
                db.commit()
                print(f"  flushed {inserted_events:,}", flush=True)
                pending.clear()

        if pending:
            db.bulk_save_objects(pending)
            db.commit()

        counts = db.query(HistoricalContamination).count()
        by_state = (
            db.query(State.name, func_count())
            .join(District, District.state_id == State.id)
            .join(Village, Village.district_id == District.id)
            .join(HistoricalContamination, HistoricalContamination.village_id == Village.id)
            .group_by(State.name)
            .all()
        )
        print(f"DONE events_inserted={inserted_events:,} table_total={counts:,}")
        for name, n in by_state:
            print(f"  {name}: {n:,}")


def func_count():
    from sqlalchemy import func
    return func.count(HistoricalContamination.id)


if __name__ == "__main__":
    main()
