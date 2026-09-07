"""Build dashboard/data.json from the database.

Contract (consumed by dashboard/index.html + /api/dashboard-data fallback):
  kpi: {samples, critical, high, low}
  priority[]: {sample_id, village, district, state, ref, band, score, date, worst}
  registry: {villages, events}
  hotspots[]: {village, district, state, params, events, first, last}
  state_bands: {state: {band: count}}
  compare[]: {state, samples, avg}
  registry_by_state: {state: {villages, events}}
  details[sample_id]: {readings[{parameter_key, value, acceptable, permissible, unit, strategy}],
                       hist_years[], hist_params[], hist_count}

Run: cd backend && ../.venv/bin/python -m etl.build_dashboard_json [--details N]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "watertriage.db"
OUT = ROOT / "dashboard" / "data.json"


def build(details_n: int = 200) -> dict:
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    samples = db.execute("SELECT COUNT(*) FROM water_samples").fetchone()[0]
    bands = dict(db.execute("SELECT band, COUNT(*) FROM risk_scores GROUP BY band").fetchall())
    reg_villages = db.execute("SELECT COUNT(DISTINCT village_id) FROM historical_contamination").fetchone()[0]
    reg_events = db.execute("SELECT COUNT(*) FROM historical_contamination").fetchone()[0]

    priority = db.execute("""
        SELECT ws.id AS sample_id, v.name AS village, d.name AS district, s.name AS state,
               ws.wqmis_ref AS ref, rs.band, rs.score,
               ws.collected_on AS date, rs.worst_parameter AS worst
        FROM water_samples ws
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        JOIN risk_scores rs ON ws.id = rs.sample_id
        ORDER BY CASE rs.band WHEN 'Critical' THEN 0 WHEN 'High' THEN 1
                              WHEN 'Medium' THEN 2 ELSE 3 END, rs.score DESC
    """).fetchall()

    state_bands: dict = {}
    for r in priority:
        state_bands.setdefault(r["state"], {})
        state_bands[r["state"]][r["band"]] = state_bands[r["state"]].get(r["band"], 0) + 1

    compare = []
    for st in state_bands:
        n = sum(state_bands[st].values())
        avg = db.execute("""
            SELECT AVG(rs.score) FROM risk_scores rs
            JOIN water_samples ws ON rs.sample_id = ws.id
            JOIN villages v ON ws.village_id = v.id
            JOIN districts d ON v.district_id = d.id
            JOIN states s ON d.state_id = s.id WHERE s.name = ?
        """, (st,)).fetchone()[0]
        compare.append({"state": st, "samples": n, "avg": round(avg or 0, 2)})

    registry_by_state = {}
    for r in db.execute("""
        SELECT s.name AS state, COUNT(DISTINCT hc.village_id) AS villages, COUNT(*) AS events
        FROM historical_contamination hc
        JOIN villages v ON hc.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id GROUP BY s.name
    """).fetchall():
        registry_by_state[r["state"]] = {"villages": r["villages"], "events": r["events"]}

    details = {}
    for r in priority[:details_n]:
        sid = r["sample_id"]
        readings = db.execute("""
            SELECT r.parameter_key, r.value, bp.acceptable_limit, bp.unit,
                   bp.permissible_limit, bp.strategy
            FROM readings r LEFT JOIN bis_parameters bp ON r.parameter_key = bp.key
            WHERE r.sample_id = ?
        """, (sid,)).fetchall()
        hist = db.execute("""
            SELECT hc.year, hc.parameter FROM historical_contamination hc
            JOIN water_samples ws ON hc.village_id = ws.village_id WHERE ws.id = ?
        """, (sid,)).fetchall()
        details[str(sid)] = {
            "readings": [{"parameter_key": x["parameter_key"], "value": x["value"],
                          "acceptable": x["acceptable_limit"], "permissible": x["permissible_limit"],
                          "unit": x["unit"], "strategy": x["strategy"]} for x in readings],
            "hist_years": sorted({h["year"] for h in hist}),
            "hist_params": sorted({h["parameter"] for h in hist}),
            "hist_count": len(hist),
        }

    hotspots = db.execute("""
        SELECT v.name AS village, d.name AS district, s.name AS state,
               GROUP_CONCAT(DISTINCT hc.parameter) AS params, COUNT(*) AS events,
               MIN(hc.year) AS first, MAX(hc.year) AS last
        FROM historical_contamination hc
        JOIN villages v ON hc.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY v.name, d.name, s.name HAVING COUNT(*) >= 3
        ORDER BY events DESC LIMIT 50
    """).fetchall()

    return {
        "kpi": {"samples": samples, "critical": bands.get("Critical", 0),
                "high": bands.get("High", 0), "low": bands.get("Low", 0)},
        "priority": [{"sample_id": r["sample_id"], "village": r["village"], "district": r["district"],
                      "state": r["state"], "ref": r["ref"], "band": r["band"],
                      "score": r["score"], "date": r["date"], "worst": r["worst"]} for r in priority],
        "registry": {"villages": reg_villages, "events": reg_events},
        "hotspots": [{"village": h["village"], "district": h["district"], "state": h["state"],
                      "params": h["params"], "events": h["events"],
                      "first": h["first"], "last": h["last"]} for h in hotspots],
        "state_bands": state_bands,
        "compare": compare,
        "registry_by_state": registry_by_state,
        "details": details,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--details", type=int, default=200)
    args = ap.parse_args()
    if not DB.exists():
        sys.exit(f"DB not found: {DB}")
    data = build(args.details)
    OUT.write_text(json.dumps(data, indent=2))
    k = data["kpi"]
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes): "
          f"{k['samples']} samples, {k['critical']} critical, {k['high']} high, {k['low']} low; "
          f"{len(data['priority'])} priority, {len(data['details'])} details, "
          f"{len(data['hotspots'])} hotspots")


if __name__ == "__main__":
    main()
