"""Re-derive readings for existing samples from records.jsonl with the corrected
parameter mapping, then re-score. Raw labels are authoritative, so sulphate rows
mis-tagged as pH are repaired exactly rather than guessed from value ranges."""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from app.database import Base, SessionLocal, engine
from app.engine import compute_scores, seed_bis_parameters
from app.models import Reading, RiskScore, WaterSample
from etl.load_wqmis import JSONL, map_param

APPLY = "--apply" in sys.argv


def bands(db):
    return Counter(b for (b,) in db.query(RiskScore.band).all())


def main():
    expected = {}
    for line in JSONL.open():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        ref = rec.get("wqmis_sample_id")
        if not ref:
            continue
        pairs = []
        for r in rec.get("results", []):
            key = map_param(r.get("parameter"))
            if key and r.get("value") is not None:
                pairs.append((key, float(r["value"])))
        expected[ref] = pairs

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_bis_parameters(db)
        before = bands(db)
        before_readings = db.query(Reading).count()

        samples = db.query(WaterSample).filter(WaterSample.wqmis_ref.isnot(None)).all()
        matched = repaired = untouched = 0

        for s in samples:
            pairs = expected.get(s.wqmis_ref)
            if pairs is None:
                untouched += 1
                continue
            matched += 1
            current = {r.parameter_key for r in db.query(Reading).filter_by(sample_id=s.id).all()}
            wanted = {k for k, _ in pairs}
            if current == wanted and len(current) == len(pairs):
                continue
            repaired += 1
            if APPLY:
                db.query(Reading).filter_by(sample_id=s.id).delete()
                for key, value in pairs:
                    db.add(Reading(sample_id=s.id, parameter_key=key, value=value))

        print(f"samples in DB with wqmis_ref : {matched}  (no JSONL match: {untouched})")
        print(f"samples needing re-tagging   : {repaired}")
        print(f"readings before              : {before_readings}")

        if not APPLY:
            print("\nDRY RUN — nothing written. Re-run with --apply.")
            return

        db.commit()
        scored = compute_scores(db)
        db.commit()

        after = bands(db)
        print(f"readings after               : {db.query(Reading).count()}")
        print(f"risk_scores recomputed       : {scored}\n")
        print("band          before   after    delta")
        for b in ["Critical", "High", "Medium", "Low"]:
            print(f"{b:11}  {before[b]:7}  {after[b]:6}   {after[b]-before[b]:+d}")
        print(f"\ntotal scored   {sum(before.values()):7}  {sum(after.values()):6}")


if __name__ == "__main__":
    main()
