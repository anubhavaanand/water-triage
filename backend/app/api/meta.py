from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_session as get_db

router = APIRouter(prefix="/meta", tags=["Metadata"])

def get_git_commit():
    try:
        import subprocess
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], 
            cwd="/home/anubhavanand/Documents/NTCC minor project/codebase"
        ).decode("utf-8").strip()
    except Exception:
        return "unknown"


@router.get("")
def get_metadata(db: Session = Depends(get_db)):
    """Return the global metadata, corpus constraints, limitations, and aggregated statistics."""
    
    # Corpus queries
    samples = db.execute(text("SELECT COUNT(*) FROM water_samples")).scalar()
    readings = db.execute(text("SELECT COUNT(*) FROM readings")).scalar()
    historical = db.execute(text("SELECT COUNT(*) FROM historical_contamination")).scalar()
    districts_with_samples = db.execute(text(
        "SELECT COUNT(DISTINCT d.id) FROM water_samples ws "
        "JOIN villages v ON ws.village_id = v.id "
        "JOIN districts d ON v.district_id = d.id"
    )).scalar()
    
    # Missing district distribution
    # In this dataset, "Not available" is the string used for missing districts
    unassigned = db.execute(text("""
        SELECT s.name as state, COUNT(ws.id)
        FROM water_samples ws
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        WHERE d.name = 'Not available'
        GROUP BY s.name
    """)).fetchall()
    unassigned_dict = {row[0]: row[1] for row in unassigned}

    # Band counts
    bands = db.execute(text("SELECT band, COUNT(*) FROM risk_scores GROUP BY band")).fetchall()
    bands_dict = {b[0]: b[1] for b in bands}
    
    # State Comparison
    state_comparison = []
    states = db.execute(text("SELECT id, name FROM states")).fetchall()
    
    for state_id, state_name in states:
        state_samples = db.execute(text("""
            SELECT ws.id, rs.score, rs.band,
                   (SELECT COUNT(*) FROM readings r JOIN bis_parameters bp ON r.parameter_key = bp.key WHERE r.sample_id = ws.id AND bp.weight > 0) as n_scored_params
            FROM water_samples ws
            JOIN risk_scores rs ON rs.sample_id = ws.id
            JOIN villages v ON ws.village_id = v.id
            JOIN districts d ON v.district_id = d.id
            WHERE d.state_id = :state_id
        """), {"state_id": state_id}).fetchall()
        
        if not state_samples:
            continue
            
        n_total = len(state_samples)
        scores = [row[1] for row in state_samples]
        mean_crs = round(sum(scores) / n_total, 2)
        sorted_scores = sorted(scores)
        
        if n_total % 2 == 1:
            median_crs = sorted_scores[n_total // 2]
        else:
            median_crs = (sorted_scores[n_total // 2 - 1] + sorted_scores[n_total // 2]) / 2.0
            
        median_crs = round(median_crs, 2)
        
        zeros = sum(1 for s in scores if s == 0)
        share_zero = round(zeros / n_total, 4)
        
        sbands = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for row in state_samples:
            sbands[row[2]] += 1
            
        n_params_dist = {}
        for row in state_samples:
            n = str(row[3])
            n_params_dist[n] = n_params_dist.get(n, 0) + 1
            
        single_param_samples = n_params_dist.get("1", 0)
        
        # Parameter rates
        param_rates = db.execute(text("""
            SELECT r.parameter_key,
                   COUNT(r.id) as tested,
                   SUM(CASE WHEN 
                       (bp.strategy = 'range' AND (r.value < bp.acceptable_limit OR r.value > COALESCE(bp.permissible_limit, 8.5)))
                       OR (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
                   THEN 1 ELSE 0 END) as exceeding_acceptable,
                   SUM(CASE WHEN 
                       bp.permissible_limit IS NOT NULL AND 
                       ((bp.strategy = 'range' AND (r.value < bp.acceptable_limit OR r.value > bp.permissible_limit))
                        OR (bp.strategy != 'range' AND r.value > bp.permissible_limit))
                   THEN 1 ELSE 0 END) as exceeding_permissible,
                   MAX(CASE WHEN bp.permissible_limit IS NULL THEN 1 ELSE 0 END) as no_permissible
            FROM readings r
            JOIN water_samples ws ON r.sample_id = ws.id
            JOIN villages v ON ws.village_id = v.id
            JOIN districts d ON v.district_id = d.id
            JOIN bis_parameters bp ON r.parameter_key = bp.key
            WHERE d.state_id = :state_id
            GROUP BY r.parameter_key
        """), {"state_id": state_id}).fetchall()
        
        prates = []
        for pr in param_rates:
            prates.append({
                "parameter_key": pr[0],
                "tested": pr[1],
                "exceeding_acceptable": pr[2],
                "exceeding_permissible": "n/a" if pr[4] else pr[3]
            })
        
        state_comparison.append({
            "state": state_name,
            "samples": n_total,
            "mean_crs": mean_crs,
            "median_crs": float(median_crs),
            "bands": sbands,
            "critical_count": sbands["Critical"],
            "critical_share_of_all_critical": round(sbands["Critical"] / (bands_dict.get("Critical", 1) or 1), 4),
            "share_zero_score": share_zero,
            "samples_by_n_params": n_params_dist,
            "single_param_samples": single_param_samples,
            "parameter_rates": prates
        })

    # Overall top parameters
    top_params = db.execute(text("""
        SELECT s.name as state, r.parameter_key, COUNT(r.id) as tested,
               SUM(CASE WHEN 
                   (bp.strategy = 'range' AND (r.value < bp.acceptable_limit OR r.value > COALESCE(bp.permissible_limit, 8.5)))
                   OR (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
               THEN 1 ELSE 0 END) as exceeding
        FROM readings r
        JOIN water_samples ws ON r.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        JOIN bis_parameters bp ON r.parameter_key = bp.key
        GROUP BY s.name, r.parameter_key
        ORDER BY exceeding DESC
        LIMIT 15
    """)).fetchall()
    
    top_parameters = []
    for tp in top_params:
        top_parameters.append({
            "state": tp[0],
            "parameter_key": tp[1],
            "tested": tp[2],
            "exceeding": int(tp[3] or 0)
        })

    # Village coverage approximation
    v_named = db.execute(text(
        "SELECT COUNT(*) FROM water_samples ws "
        "JOIN villages v ON ws.village_id = v.id "
        "WHERE lower(v.name) NOT IN ('not available', 'unknown')"
    )).scalar()
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "corpus": {
            "samples": samples,
            "readings": readings,
            "historical_events_distinct": historical,
            "sample_years": [2022, 2022],
            "registry_years": [2009, 2012],
            "districts_with_samples": districts_with_samples,
            "village_name_coverage_pct": round((v_named / max(samples, 1)) * 100, 2),
            "unassigned_district_samples": unassigned_dict
        },
        "bands": bands_dict,
        "band_thresholds": {"Critical": 75, "High": 50, "Medium": 25, "Low": 0},
        "state_comparison": state_comparison,
        "top_parameters": top_parameters,
        "scoring": {
            "model": "BIS IS 10500 weighted severity model",
            "standard": "BIS IS 10500",
            "weights": {
                "arsenic": 1.0,
                "e_coli": 0.9,
                "fluoride": 0.8,
                "nitrate": 0.7,
                "iron": 0.4,
                "turbidity": 0.3,
                "tds": 0.3,
                "ph": 0.2
            },
            "escalation_rules": [
                {"rule": "Any parameter severity 1.0 (exceeds permissible / acute risk)", "bands_floor": "High"}
            ]
        },
        "limitations": [
            {
                "id": "panel-size-bias",
                "title": "Panel size drives score",
                "detail": "Composite score depends on how many parameters were tested; the artifact is concentrated in single-parameter iron samples rather than a monotone trend. one-parameter samples can reach 100 if that one parameter exceeds limits.",
                "status": "accepted"
            },
            {
                "id": "missing-district",
                "title": "Unassigned samples",
                "detail": f"{unassigned_dict.get('Uttar Pradesh', 0)} samples in UP are missing district identifiers (marked 'Not available').",
                "status": "open"
            },
            {
                "id": "village-identifiability",
                "title": "Village names unavailable",
                "detail": "Over 98% of WQMIS samples lack a traceable village or gram panchayat name.",
                "status": "accepted"
            }
        ],
        "caveats": {
            "sampling": "non-random crawl; comparisons describe the corpus",
            "min_samples_for_mean": 5
        }
    }
