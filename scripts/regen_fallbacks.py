#!/usr/bin/env python3
"""Refresh dashboard/public static JSON fallbacks from the live backend API.

The GitHub Pages deploy has no backend, so the React app has nothing to fetch
when the API is unreachable. These baked files keep the deployed site usable and
must be regenerated whenever the corpus changes, or the live site starts
advertising numbers the live database contradicts. The copy shipped on 2026-10-04
still carried a 1,741-sample corpus with 89/392/28/1,232 bands against a live
database holding 1,853 samples and 77/56/131/1,589.

Endpoints pulled:
  /api/health           -> health.json
  /api/meta             -> meta.json
  /api/dashboard-data   -> dashboard-data.json
  /api/samples          -> samples.json
  /api/scoring/parameters -> scoring-parameters.json
  /api/validation/cgwb  -> validation-cgwb.json
"""
import json
import os
import sys
import urllib.request

BASE = os.environ.get("BACKEND_URL", "http://127.0.0.1:8088")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "public"))

# (path, filename, required). Everything here is required: a stale or missing
# fallback is worse than an honest failure on the deployed site.
ENDPOINTS = [
    ("/api/health", "health.json", True),
    ("/api/meta", "meta.json", True),
    ("/api/dashboard-data", "dashboard-data.json", True),
    ("/api/samples", "samples.json", True),
    ("/api/scoring/parameters", "scoring-parameters.json", True),
    ("/api/validation/cgwb", "validation-cgwb.json", True),
]


def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=120) as r:
        return json.load(r)


def summarise(fname, data):
    if fname == "meta.json":
        return (
            f"samples={data['corpus']['samples']} "
            f"bands={data['bands']} "
            f"village_coverage={data['corpus']['village_name_coverage_pct']}%"
        )
    if fname == "health.json":
        return str(data)
    if fname == "scoring-parameters.json":
        return f"{len(data)} BIS parameters"
    if fname == "validation-cgwb.json":
        return f"{len(data.get('ph', []))} CGWB pH rows"
    return ""


def main():
    os.makedirs(OUT, exist_ok=True)
    failed = 0
    for path, fname, required in ENDPOINTS:
        try:
            data = fetch(path)
        except Exception as exc:  # pragma: no cover - network path
            print(f"FAIL {fname}: {exc}", file=sys.stderr)
            failed += 1
            continue
        dest = os.path.join(OUT, fname)
        with open(dest, "w") as f:
            json.dump(data, f, indent=2)
        extra = summarise(fname, data)
        print(f"OK {fname} ({os.path.getsize(dest)}B){' ' + extra if extra else ''}")
    if failed:
        print(f"{failed} endpoint(s) failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
