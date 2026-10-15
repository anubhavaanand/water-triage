#!/usr/bin/env python
"""Fix phantom 'Not available' districts and villages.

Issue: Two phantom districts named 'Not available' were created (one in UP, one in Bihar).
1,493 samples have village='Not available' but correctly belong to REAL districts.
The phantom districts have NO samples - they are empty shells.

Fix:
1. Delete the two phantom 'Not available' districts (and their 'Not available' villages)
2. Keep the 1,493 samples with village='Not available' in their REAL districts
   (this preserves correct district assignment for analysis)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.database import SessionLocal
from backend.app.models.entities import District, Village, State, WaterSample
from sqlalchemy import func


def main():
    db = SessionLocal()
    try:
        print("FIXING PHANTOM 'Not available' DISTRICTS")
        print("=" * 60)

        # Find the phantom districts
        phantom_districts = db.query(District).filter(District.name == "Not available").all()
        print(f"Found {len(phantom_districts)} phantom districts:")
        for d in phantom_districts:
            state = db.query(State).filter(State.id == d.state_id).one()
            print(f"  District ID {d.id}: {d.name} ({state.name}) - param_count={d.parameter_count}, data_quality={d.data_quality}")

        # Check villages in phantom districts
        for d in phantom_districts:
            villages = db.query(Village).filter(Village.district_id == d.id).all()
            print(f"  Villages in phantom district {d.id}: {[(v.id, v.name) for v in villages]}")

            # Check if any samples point to these villages
            for v in villages:
                sample_count = db.query(func.count(WaterSample.id)).filter(WaterSample.village_id == v.id).scalar()
                print(f"    Village {v.id} ({v.name}) has {sample_count} samples")

        # Verify: samples with village='Not available' in REAL districts
        real_not_avail_samples = db.query(func.count(WaterSample.id)).join(Village).join(District).filter(
            Village.name == "Not available",
            District.name != "Not available"
        ).scalar()
        print(f"\nSamples with village='Not available' in REAL districts: {real_not_avail_samples}")

        # Samples with village='Not available' in PHANTOM districts
        phantom_not_avail_samples = db.query(func.count(WaterSample.id)).join(Village).join(District).filter(
            Village.name == "Not available",
            District.name == "Not available"
        ).scalar()
        print(f"Samples with village='Not available' in PHANTOM districts: {phantom_not_avail_samples}")

        # Delete phantom districts' villages first, then districts
        print("\nDeleting phantom districts and their villages...")
        for d in phantom_districts:
            # Delete villages in this phantom district first
            villages = db.query(Village).filter(Village.district_id == d.id).all()
            for v in villages:
                print(f"    Deleting village {v.id} ({v.name})")
                db.delete(v)
            print(f"  Deleting district {d.id} ({d.name}) in state {d.state_id}")
            db.delete(d)

        db.commit()

        # Verify deletion
        remaining = db.query(District).filter(District.name == "Not available").all()
        print(f"\nRemaining 'Not available' districts: {len(remaining)}")

        # Verify samples still exist
        total_samples = db.query(func.count(WaterSample.id)).scalar()
        print(f"Total samples after fix: {total_samples}")

        # Verify real 'Not available' villages still exist
        real_villages = db.query(Village).join(District).filter(
            Village.name == "Not available",
            District.name != "Not available"
        ).all()
        print(f"'Not available' villages in real districts: {len(real_villages)}")
        for v in real_villages[:5]:
            district = db.query(District).filter(District.id == v.district_id).one()
            state = db.query(State).filter(State.id == district.state_id).one()
            sample_count = db.query(func.count(WaterSample.id)).filter(WaterSample.village_id == v.id).scalar()
            print(f"  Village {v.id}: {v.name} in {district.name} ({state.name}) - {sample_count} samples")

        print("\n" + "=" * 60)
        print("PHANTOM DISTRICTS FIX COMPLETE")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()