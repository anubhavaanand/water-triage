from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import BisParameter

router = APIRouter(prefix="/scoring", tags=["scoring"])


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
