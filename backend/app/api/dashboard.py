from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_session

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard-data")
def get_dashboard_data(db: Session = Depends(get_session)):
    samples_res = db.execute(text("SELECT COUNT(*) FROM risk_scores")).scalar() or 0
    crit_res = db.execute(text("SELECT COUNT(*) FROM risk_scores WHERE band='Critical'")).scalar() or 0
    high_res = db.execute(text("SELECT COUNT(*) FROM risk_scores WHERE band='High'")).scalar() or 0
    low_res = db.execute(text("SELECT COUNT(*) FROM risk_scores WHERE band='Low'")).scalar() or 0
    
    kpi = {
        "samples": samples_res,
        "critical": crit_res,
        "high": high_res,
        "low": low_res
    }
    
    priority_rows = db.execute(text("""
        SELECT rs.id as risk_id, rs.sample_id as sample_id, rs.score, rs.band, rs.worst_parameter,
               ws.wqmis_ref as ref, ws.collected_on as date,
               v.name as village, d.name as district, s.name as state
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        ORDER BY rs.score DESC
        LIMIT 2000
    """)).fetchall()

    bis_rows = db.execute(text("""
        SELECT key, label, unit, acceptable_limit, permissible_limit, strategy
        FROM bis_parameters
    """)).fetchall()
    bis_map = {
        r.key: {
            "label": r.label,
            "unit": r.unit,
            "acceptable": float(r.acceptable_limit) if r.acceptable_limit is not None else None,
            "permissible": float(r.permissible_limit) if r.permissible_limit is not None else None,
            "strategy": r.strategy
        } for r in bis_rows
    }

    sample_ids = [r.sample_id for r in priority_rows]
    readings_by_sample = defaultdict(list)
    if sample_ids:
        chunk_size = 500
        for i in range(0, len(sample_ids), chunk_size):
            chunk = sample_ids[i:i + chunk_size]
            placeholders = ",".join(f":s_{idx}" for idx in range(len(chunk)))
            params = {f"s_{idx}": sid for idx, sid in enumerate(chunk)}
            rdg_rows = db.execute(text(f"""
                SELECT sample_id, parameter_key, value
                FROM readings
                WHERE sample_id IN ({placeholders})
            """), params).fetchall()

            for rdg in rdg_rows:
                binfo = bis_map.get(rdg.parameter_key, {})
                unit = binfo.get("unit") or ("MPN/100mL" if rdg.parameter_key in ("e_coli", "total_coliform") else "mg/L")
                readings_by_sample[rdg.sample_id].append({
                    "parameter_key": rdg.parameter_key,
                    "value": float(rdg.value) if rdg.value is not None else None,
                    "acceptable": binfo.get("acceptable"),
                    "permissible": binfo.get("permissible"),
                    "unit": unit,
                    "strategy": binfo.get("strategy") or "threshold"
                })

    priority = []
    details = {}
    
    for r in priority_rows:
        pid = str(r.risk_id)
        priority.append({
            "sample_id": r.risk_id,
            "village": r.village,
            "district": r.district,
            "state": r.state,
            "ref": r.ref,
            "band": r.band,
            "score": float(r.score) if r.score else 0.0,
            "date": str(r.date),
            "worst": r.worst_parameter or "Unknown"
        })
        
        details[pid] = {
            "readings": readings_by_sample.get(r.sample_id, []),
            "hist_years": [],
            "hist_params": [],
            "hist_count": 0
        }
    
    state_bands = {}
    sb_rows = db.execute(text("""
        SELECT s.name as state, rs.band as band, COUNT(*) as cnt
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY s.name, rs.band
    """)).fetchall()
    
    for r in sb_rows:
        if r.state not in state_bands:
            state_bands[r.state] = {"Critical": 0, "High": 0, "Low": 0, "Medium": 0}
        band = r.band if r.band in ["Critical", "High", "Low", "Medium"] else "Low"
        state_bands[r.state][band] += r.cnt

    compare_rows = db.execute(text("""
        SELECT s.name as state, COUNT(rs.id) as samples, ROUND(CAST(AVG(rs.score) AS NUMERIC), 2) as avg_score
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY s.name
    """)).fetchall()
    compare = [{"state": r.state, "samples": r.samples, "avg": float(r.avg_score) if r.avg_score else 0.0} for r in compare_rows]

    reg_villages = db.execute(text("SELECT COUNT(DISTINCT village_id) FROM historical_contamination")).scalar() or 0
    reg_events = db.execute(text("SELECT COUNT(*) FROM historical_contamination")).scalar() or 0
    registry = {"villages": reg_villages, "events": reg_events}
        
    return {
        "kpi": kpi,
        "priority": priority,
        "details": details,
        "state_bands": state_bands,
        "registry": registry,
        "hotspots": [],
        "compare": compare,
        "registry_by_state": {}
    }

