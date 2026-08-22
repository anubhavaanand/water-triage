"""Load generated data into the database:  python -m etl.load_data"""

from app.database import Base, SessionLocal, engine
from app.engine import compute_scores, seed_bis_parameters
from app.models import District, Reading, State, Village, WaterSample

from .synthetic import generate_samples


def upsert_geo(session, samples):
    state_cache: dict[str, State] = {}
    district_cache: dict[tuple[str, str], District] = {}
    village_cache: dict[tuple[str, str], Village] = {}

    for s in session.query(State).all():
        state_cache[s.name] = s
    for d in session.query(District).all():
        district_cache[(d.state_id, d.name)] = d

    for sample in samples:
        state = state_cache.get(sample.state)
        if state is None:
            state = State(name=sample.state)
            session.add(state)
            session.flush()
            state_cache[sample.state] = state

        key = (state.id, sample.district)
        district = district_cache.get(key)
        if district is None:
            district = District(state_id=state.id, name=sample.district)
            session.add(district)
            session.flush()
            district_cache[key] = district

        vkey = (district.id, sample.village)
        village = village_cache.get(vkey)
        if village is None:
            village = (
                session.query(Village).filter_by(district_id=district.id, name=sample.village).first()
            )
            if village is None:
                village = Village(
                    district_id=district.id, name=sample.village, block=sample.block
                )
                session.add(village)
                session.flush()
            village_cache[vkey] = village


def load(session) -> dict:
    samples = generate_samples()

    upsert_geo(session, samples)

    existing_refs = {r for (r,) in session.query(WaterSample.wqmis_ref).all()}
    inserted = 0
    for s in samples:
        if s.wqmis_ref in existing_refs:
            continue
        village = (
            session.query(Village)
            .join(District)
            .filter(Village.name == s.village, District.name == s.district)
            .one()
        )
        ws = WaterSample(
            village_id=village.id,
            source_type=s.source_type,
            collected_on=s.collected_on,
            lab_name=s.lab_name,
            wqmis_ref=s.wqmis_ref,
        )
        session.add(ws)
        session.flush()
        for r in s.readings:
            session.add(Reading(sample_id=ws.id, parameter_key=r.parameter_key, value=r.value))
        inserted += 1

    session.commit()
    scored = compute_scores(session)

    return {"generated": len(samples), "inserted": inserted, "scored": scored}


def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seeded = seed_bis_parameters(db)
        stats = load(db)
        stats["bis_params_seeded"] = seeded

    print(stats)


if __name__ == "__main__":
    main()
