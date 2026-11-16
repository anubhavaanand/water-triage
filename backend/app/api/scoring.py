from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_session
from ..engine.pipeline import score_sample
from ..models import BisParameter

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.get("/{sample_id}")
def get_sample_score(sample_id: int, db: Session = Depends(get_session)):
    """Return the risk score and per-parameter severity breakdown for one sample.

    Recomputed on request rather than read from risk_scores, so the result is
    always consistent with the current BIS limits even before a recompute.
    Returns a zero-score payload (not an error) when the sample has no
    readings for scored parameters.
    """
    result = score_sample(db, sample_id)
    if result is None:
        raise HTTPException(404, "sample not found")
    return result


@router.get("/parameters")
def list_scoring_parameters(db: Session = Depends(get_session)):
    """Expose the BIS IS 10500 parameter table used by the scoring engine.

    The frontend draws its severity bars against these limits rather than
    restating them, so a limit change in the engine propagates to the UI
    instead of silently diverging from it.
    """
    rows = db.query(BisParameter).order_by(BisParameter.key).all()
    return [
        {
            "key": r.key,
            "label": r.label,
            "unit": r.unit,
            "acceptable": float(r.acceptable_limit) if r.acceptable_limit is not None else None,
            "permissible": float(r.permissible_limit) if r.permissible_limit is not None else None,
            "weight": float(r.weight) if r.weight is not None else None,
            "strategy": r.strategy,
            # A parameter with no permissible uplift is binary: any exceedance is
            # full severity. The engine calls this the "acute hazards are binary"
            # case, and the UI must not render a proportional bar for it.
            "binary_exceedance": bool(
                r.permissible_limit is None or r.permissible_limit <= r.acceptable_limit
            ),
        }
        for r in rows
    ]
