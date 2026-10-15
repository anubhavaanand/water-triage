"""Fast parallel WQMIS crawler (v2) — fetches UP+Bihar lab reports in bulk with:
1. Two-step ASP.NET Session Cookie Handshake (`GET /WQMIS/Report/Report_p` -> `ASP.NET_SessionId` +
   `__RequestVerificationToken_L1dRTUlT0` before `GET /WQMIS/Common/final_report_print?s_id=...`).
2. Automatic `<div class="lab-address-panel">` fallback district extraction whenever the submitter's
   `Full Address:` records `District- Not available`.
3. Automatic `location : <Village/Habitation>` extraction from `Source of Sample:` whenever `Village-`
   is `Not available`.

Usage:
    python crawl_fast.py --start 1000000 --end 2000000 --workers 8 --max-hits 2000
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "wqmis"
BASE = "https://ejalshakti.gov.in"
REPORT_P_URL = f"{BASE}/WQMIS/Report/Report_p"
FINAL_REPORT = f"{BASE}/WQMIS/Common/final_report_print"
KEY_HEX = b"38303830383038303830383038303830"
STATES = {"Uttar Pradesh", "Bihar"}
STATE_ALIASES = {"uttar pradesh": "Uttar Pradesh", "bihar": "Bihar"}
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) WaterTriage-ETL/0.3 (academic project)"
JSONL_PATH = RAW_DIR / "records.jsonl"
PROGRESS_PATH = RAW_DIR / "crawl_progress.txt"

_thread_local = threading.local()


def _get_session() -> requests.Session:
    """Returns a thread-local requests.Session pre-initialized with WQMIS ASP.NET session cookies."""
    sess = getattr(_thread_local, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        try:
            sess.get(REPORT_P_URL, timeout=20)
        except Exception:
            pass
        _thread_local.session = sess
    return sess


def aes_encrypt(value: str) -> str:
    out = subprocess.run(
        [
            "openssl", "enc", "-aes-128-cbc",
            "-K", KEY_HEX.decode(),
            "-iv", KEY_HEX.decode(),
            "-nosalt", "-base64",
        ],
        input=value.encode(),
        capture_output=True,
        check=True,
    )
    return out.stdout.decode().strip()


def parse_dt(text: str | None):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text or "")
    if m:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def state_of(html: str) -> str | None:
    m = re.search(r"District-\s*[^,]+,\s*State-\s*([A-Za-z &]+)", html)
    if not m:
        return None
    return STATE_ALIASES.get(m.group(1).strip().lower())


def parse_lab_panel(html: str) -> tuple[str | None, str | None]:
    """Extracts (lab_name, lab_district) from `<div class="lab-address-panel">`."""
    panel_match = re.search(
        r'<div[^>]*class="[^"]*lab-address-panel[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    block = panel_match.group(1) if panel_match else html
    h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", block, re.DOTALL | re.IGNORECASE)
    lab_name = re.sub(r"\s+", " ", h2_match.group(1)).strip() if h2_match else None

    dist_match = re.search(r"Dist(?:rict)?\s*-\s*([A-Za-z\s\(\)\.]+?)(?:,|Pin|$|<)", block, re.IGNORECASE)
    if dist_match:
        district = dist_match.group(1).strip()
        if district and district.lower() != "not available":
            return lab_name, district

    if lab_name and "," in lab_name:
        tail = lab_name.rsplit(",", 1)[-1].strip()
        if tail and tail.lower() not in ("not available", "up", "bihar"):
            return lab_name, tail
    return lab_name, None


def extract_location_from_source(source: str | None) -> str | None:
    if not source:
        return None
    m = re.search(r"location\s*:\s*(.+)$", source, re.IGNORECASE)
    if not m:
        return None
    loc = m.group(1).strip(" -.,;:")
    if not loc or loc.lower() in ("not available", "na", "n/a", "nil", "none", "-", "0"):
        return None
    return loc


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

            results.append(
                {
                    "parameter": cells[1],
                    "unit": cells[2],
                    "acceptable": num(cells[3]),
                    "permissible": num(cells[4]),
                    "value": value,
                }
            )
        if results:
            break

    if not loc.get("state") or not loc.get("district"):
        return None

    source_str = after(r"Source of Sample:", r"Village")
    lab_panel_name, lab_panel_district = parse_lab_panel(html)
    raw_district = loc.get("district")
    inferred_district = (
        raw_district
        if (raw_district and raw_district.lower() != "not available")
        else (lab_panel_district or "Not available")
    )

    raw_village = loc.get("village")
    extracted_location = (
        raw_village
        if (raw_village and raw_village.lower() != "not available")
        else (extract_location_from_source(source_str) or "Not available")
    )

    sample_id_str = sid_m.group(1)
    lab_code_m = re.search(r"(L\d+)", sample_id_str)

    return {
        "wqmis_sample_id": sample_id_str,
        "lab_code": lab_code_m.group(1) if lab_code_m else None,
        "village": raw_village,
        "extracted_location": extracted_location,
        "gram_panchayat": loc.get("gram panchayat"),
        "block": loc.get("block"),
        "district": raw_district,
        "inferred_district": inferred_district,
        "state": loc.get("state"),
        "source": source_str,
        "collected_on": parse_dt(after(r"sample collection", r"Date & time of sample received")),
        "lab": lab_panel_name or after(r"Water Testing Laboratory,", ","),
        "results": results,
    }


def _load_progress() -> set[int]:
    if PROGRESS_PATH.exists():
        return {int(x) for x in PROGRESS_PATH.read_text().split() if x.strip()}
    return set()


def _mark_done(internal_id: int):
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_PATH.open("a") as fh:
        fh.write(f"{internal_id}\n")


def _append_record(record: dict):
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("a") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def fetch_one(internal_id: int) -> tuple[int, str | None]:
    """Fetch one WQMIS report using thread-local ASP.NET session cookies."""
    enc = aes_encrypt(str(internal_id))
    try:
        s = _get_session()
        r = s.get(FINAL_REPORT, params={"s_id": enc}, timeout=30)
        if r.status_code == 500 or "Object reference not set" in r.text:
            # Refresh ASP.NET session cookie on expiry and retry once
            s.get(REPORT_P_URL, timeout=20)
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

            batch = ids_to_fetch[batch_start : batch_start + batch_size]
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
                print(
                    f"  [{iid}] HIT {st}/{record.get('inferred_district') or record['district']}/"
                    f"{record.get('extracted_location') or record.get('village','?')} "
                    f"params={len(record['results'])}",
                    flush=True,
                )

                if max_hits and hits >= max_hits:
                    break

            pct = (batch_start + len(batch)) / max(1, len(ids_to_fetch)) * 100
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
