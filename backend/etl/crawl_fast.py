"""Fast parallel WQMIS crawler — fetches UP+Bihar lab reports in bulk.

Usage:
    python crawl_fast.py --start 1000000 --end 2000000 --workers 8 --max-hits 2000
"""

import argparse
import json
import subprocess
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "wqmis"
BASE = "https://ejalshakti.gov.in"
FINAL_REPORT = f"{BASE}/WQMIS/Common/final_report_print"
KEY_HEX = b"38303830383038303830383038303830"
STATES = {"Uttar Pradesh", "Bihar"}
STATE_ALIASES = {"uttar pradesh": "Uttar Pradesh", "bihar": "Bihar"}
USER_AGENT = "WaterTriage-ETL/0.1 (academic project)"
JSONL_PATH = RAW_DIR / "records.jsonl"
PROGRESS_PATH = RAW_DIR / "crawl_progress.txt"


def aes_encrypt(value: str) -> str:
    out = subprocess.run(
        ["openssl", "enc", "-aes-128-cbc", "-K", KEY_HEX.decode(), "-iv", KEY_HEX.decode(),
         "-nosalt", "-base64"],
        input=value.encode(), capture_output=True, check=True)
    return out.stdout.decode().strip()


def parse_dt(text: str):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text or "")
    if m:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def state_of(html: str) -> str | None:
    m = re.search(r"District-\s*[^,]+,\s*State-\s*([A-Za-z &]+)", html)
    if not m:
        return None
    return STATE_ALIASES.get(m.group(1).strip().lower())


def parse_report(html: str) -> dict | None:
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    soup = BeautifulSoup(text, "html.parser")
    flat = re.sub(r"\s+", " ", soup.get_text(" "))

    sid_m = re.search(r"Sample Id:\s*([A-Z0-9]{4,})", flat)
    if not sid_m:
        return None

    def after(label, until):
        m = re.search(label + r"(.*?)" + until, flat)
        return m.group(1).strip() if m else None

    addr = after(r"Full Address:", r"Sample description")
    loc = {}
    if addr:
        for key in ("Village", "Gram Panchayat", "Block", "District", "State"):
            lm = re.search(key + r"-\s*([^,]+)", addr)
            loc[key.lower()] = lm.group(1).strip() if lm else None

    results = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not any("Parameter" in h for h in headers):
            continue
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) < 6 or not re.match(r"^\d+$", cells[0]):
                continue
            vm = re.match(r"([\d.]+)", cells[5].replace(",", ""))
            if not vm:
                continue
            val_clean = re.sub(r"\.{2,}", ".", vm.group(1)).strip(".")
            try:
                value = float(val_clean)
            except ValueError:
                continue

            def num(s: str):
                m2 = re.search(r"\d+(?:\.\d+)?", s or "")
                return float(m2.group()) if m2 else None
            results.append({
                "parameter": cells[1], "unit": cells[2],
                "acceptable": num(cells[3]), "permissible": num(cells[4]),
                "value": value,
            })
        if results:
            break

    if not loc.get("state") or not loc.get("district"):
        return None

    return {
        "wqmis_sample_id": sid_m.group(1),
        "village": loc.get("village"), "gram_panchayat": loc.get("gram panchayat"),
        "block": loc.get("block"), "district": loc.get("district"),
        "state": loc.get("state"),
        "source": after(r"Source of Sample:", r"Village"),
        "collected_on": parse_dt(after(r"sample collection", r"Date & time of sample received")),
        "lab": after(r"Water Testing Laboratory,", ","),
        "results": results,
    }


def _load_progress() -> set[int]:
    if PROGRESS_PATH.exists():
        return {int(x) for x in PROGRESS_PATH.read_text().split() if x.strip()}
    return set()


def _mark_done(internal_id: int):
    with PROGRESS_PATH.open("a") as fh:
        fh.write(f"{internal_id}\n")


def _append_record(record: dict):
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("a") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def fetch_one(internal_id: int) -> tuple[int, str | None]:
    """Fetch one WQMIS report. Returns (id, html_or_None)."""
    enc = aes_encrypt(str(internal_id))
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        r = s.get(FINAL_REPORT, params={"s_id": enc}, timeout=30)
        return internal_id, r.text
    except Exception:
        return internal_id, None


def crawl_fast(start: int, end: int, workers: int = 8, max_hits: int | None = None):
    done = _load_progress()
    hits = 0
    parsed = 0
    total_ids = end - start + 1
    batch_size = 50

    ids_to_fetch = [i for i in range(start, end + 1) if i not in done]
    print(f"Total IDs: {total_ids}, already done: {len(done)}, to fetch: {len(ids_to_fetch)}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for batch_start in range(0, len(ids_to_fetch), batch_size):
            if max_hits and hits >= max_hits:
                print(f"\nHit cap reached: {hits} hits", flush=True)
                break

            batch = ids_to_fetch[batch_start:batch_start + batch_size]
            futures = {executor.submit(fetch_one, iid): iid for iid in batch}

            for future in as_completed(futures):
                iid, html = future.result()
                _mark_done(iid)

                if not html:
                    continue

                st = state_of(html)
                if st is None:
                    continue

                parsed += 1
                record = parse_report(html)
                if record is None:
                    continue

                record["state"] = st
                record["internal_id"] = iid
                hits += 1
                _append_record(record)
                print(f"  [{iid}] HIT {st}/{record['district']}/{record.get('village','?')} "
                      f"params={len(record['results'])}", flush=True)

                if max_hits and hits >= max_hits:
                    break

            # Progress
            pct = (batch_start + len(batch)) / len(ids_to_fetch) * 100
            print(f"  Progress: {pct:.1f}% ({hits} hits, {parsed} parsed)", flush=True)

    print(f"\nDone: parsed={parsed} hits={hits}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1000000)
    ap.add_argument("--end", type=int, default=2000000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-hits", type=int, default=2000)
    args = ap.parse_args()

    crawl_fast(args.start, args.end, args.workers, args.max_hits)


if __name__ == "__main__":
    main()
