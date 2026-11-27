#!/usr/bin/env python3
"""Reproducible benchmark for WaterTriage data and query claims.

Run:  python3 benchmarks/run_bench.py

Writes benchmarks/results.json and prints a summary. Never estimates: anything
that cannot be measured in this environment is recorded as "BLOCKED" with the
exact reason.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = Path(__file__).resolve().parent / "results.json"


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def environment() -> dict:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "cpu_count": os.cpu_count(),
    }


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dataset_metrics() -> dict:
    raw = read_jsonl(ROOT / "data/raw/wqmis/records.jsonl")
    enriched = read_jsonl(ROOT / "data/raw/wqmis/records_enriched.jsonl")

    sample_ids = [r.get("wqmis_sample_id") for r in raw]
    districts = {r.get("district") for r in raw if (r.get("district") or "").strip()}
    readings = sum(len(r.get("results") or {}) for r in raw)
    states = sorted({r.get("state") for r in raw if r.get("state")})

    # District resolution breakdown from the enriched corpus.
    probe = ("aspnet_session_lab_probe", "single_district_lab")
    resolved = [r for r in enriched if any(p in (r.get("district_resolution_source") or "") for p in probe)]
    submit = [r for r in enriched if r.get("district_resolution_source") == "submitter_address"]
    multi = [r for r in enriched if "multi_district" in (r.get("district_resolution_source") or "")]
    denom = len(resolved) + len(multi)

    return {
        "status": "MEASURED",
        "raw_records": len(raw),
        "enriched_records": len(enriched),
        "unique_sample_ids": len(set(sample_ids)),
        "distinct_districts_in_raw": len(districts),
        "total_parameter_readings": readings,
        "states": states,
        "district_resolution": {
            "submitter_address": len(submit),
            "resolved_via_lab_probe": len(resolved),
            "multi_district_held_back": len(multi),
            "denominator_resolved_plus_multi": denom,
            "resolution_rate_pct": round(100 * len(resolved) / denom, 1) if denom else None,
        },
    }


def scoring_outputs() -> dict:
    import csv

    out = {}
    for name in ("WQ6_Complete_UP.csv", "WQ6_Complete_Bihar.csv", "Full_113_District_Risk_Triage.csv"):
        path = ROOT / "data/validation_reports" / name
        if not path.exists():
            out[name] = {"status": "MISSING"}
            continue
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        out[name] = {"status": "MEASURED", "rows": len(rows)}
    return out


def query_timing() -> dict:
    """Benchmark the N+1 vs set-based JOIN query. Requires a live PostgreSQL."""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        return {
            "status": "BLOCKED",
            "reason": "DATABASE_URL is not set and no local PostgreSQL is reachable; query timing cannot be measured here.",
        }
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return {
            "status": "BLOCKED",
            "reason": "psycopg is not installed in this environment (pip install 'psycopg[binary]').",
        }
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        return {"status": "BLOCKED", "reason": str(exc)}

    import statistics
    import time

    results = {}
    runs = 10
    try:
        with psycopg.connect(db_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                started = time.perf_counter()
                for _ in range(runs):
                    cur.execute(
                        """
                        SELECT district, COUNT(*) AS n
                        FROM samples
                        GROUP BY district
                        """
                    )
                    cur.fetchall()
                elapsed = (time.perf_counter() - started) / runs
        results["set_based_group_by"] = {
            "status": "MEASURED",
            "runs": runs,
            "mean_seconds": round(elapsed, 4),
        }
    except Exception as exc:
        results["set_based_group_by"] = {"status": "BLOCKED", "reason": repr(exc)}

    results["n_plus_one_baseline"] = {
        "status": "BLOCKED",
        "reason": "The legacy per-row lookup path is not present in the current codebase; reconstructing it would fabricate the comparison.",
    }
    return results


def main() -> int:
    payload = {
        "environment": environment(),
        "dataset": dataset_metrics(),
        "scoring_outputs": scoring_outputs(),
        "query_timing": query_timing(),
    }
    RESULTS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    ds = payload["dataset"]
    print(f"records (raw)          : {ds['raw_records']}")
    print(f"unique sample ids      : {ds['unique_sample_ids']}")
    print(f"distinct districts     : {ds['distinct_districts_in_raw']}")
    print(f"parameter readings     : {ds['total_parameter_readings']}")
    res = ds["district_resolution"]
    print(f"lab-resolution rate    : {res['resolution_rate_pct']}% ({res['resolved_via_lab_probe']}/{res['denominator_resolved_plus_multi']})")
    print(f"query timing           : {payload['query_timing']['status'] if isinstance(payload['query_timing'], dict) else 'partial'}")
    print(f"\nwrote {RESULTS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
