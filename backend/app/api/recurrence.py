from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_session
from ..engine.recurrence_service import list_recurrent_villages, village_recurrence

router = APIRouter(prefix="/recurrence", tags=["recurrence"])


@router.get("/{village_id}")
def get_village_recurrence(village_id: int, db: Session = Depends(get_session)):
    rec = village_recurrence(db, village_id)
    if rec is None:
        raise HTTPException(404, "village not found")
    return {
        "village_id": rec.village_id,
        "village": rec.village,
        "district": rec.district,
        "state": rec.state,
        "historical": {k: sorted(v) for k, v in rec.historical.items()},
        "current_exceedances": rec.current_exceedances,
        "classifications": rec.classifications,
        "persistent_params": rec.persistent_params,
        "recurrence_score": rec.recurrence_score,
        "verdict": rec.verdict,
    }


@router.get("")
def list_recurrent(
    limit: int = Query(50, le=200), db: Session = Depends(get_session)
):
    rows = list_recurrent_villages(db, limit=limit)
    return [
        {
            "village_id": r.village_id,
            "village": r.village,
            "district": r.district,
            "state": r.state,
            "persistent_params": r.persistent_params,
            "classifications": r.classifications,
            "recurrence_score": r.recurrence_score,
            "verdict": r.verdict,
        }
        for r in rows
    ]
