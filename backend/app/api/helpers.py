from sqlalchemy.orm import Session

from ..models import BisParameter


def reading_units(db: Session) -> dict[str, str]:
    return {p.key: p.unit for p in db.query(BisParameter).all()}


def band_counts(scores) -> dict[str, int]:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for (_, band) in scores:
        if band in counts:
            counts[band] += 1
    return counts
