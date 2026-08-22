"""WQMIS data acquisition for WaterTriage.

Access tiers:
  PUBLIC  final_report_print?s_id=AES(id)  individual lab reports, sequential ids
  SESSION get_Report_Parameter_wise        parameter-wise tables, needs login cookie

AES scheme (extracted from WQMIS JS): AES-128-CBC, key=iv='8080808080808080', PKCS7.
Replicated via openssl CLI to avoid extra python deps.

Commands:
  probe                          check endpoint health
  districts                      list UP+Bihar districts (public endpoints)
  crawl --start N --end M        fetch public reports by id range, store matches
  pull --cookie-file F           session-mode parameter-wise pull (all UP+Bihar)
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "wqmis"
BASE = "https://ejalshakti.gov.in"
REPORT_P = f"{BASE}/WQMIS/Report/Report_p"
FINAL_REPORT = f"{BASE}/WQMIS/Common/final_report_print"
DISTRICT_BIND = f"{BASE}/WQMIS/Common/District_Bind_without_session"
PARAM_WISE = f"{BASE}/WQMIS/Report/get_Report_Parameter_wise"

KEY_HEX = b"38303830383038303830383038303830"
STATES = {"Uttar Pradesh": 31, "Bihar": 5}
TARGET_STATES = set(STATES)
USER_AGENT = "WaterTriage-ETL/0.1 (academic project; contact: anubhavaanand)"
RATE_SECONDS = 1.0

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def aes_encrypt(value: str) -> str:
    out = subprocess.run(
        ["openssl", "enc", "-aes-128-cbc", "-K", KEY_HEX.decode(), "-iv", KEY_HEX.decode(),
         "-nosalt", "-base64"],
        input=value.encode(), capture_output=True, check=True)
    return out.stdout.decode().strip()


def get_verification_token() -> str:
    r = session.get(REPORT_P, timeout=30)
    m = re.search(r'__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("no anti-forgery token on Report_p")
    return m.group(1)


def fetch_districts(state_name: str) -> dict[str, str]:
    state_id = STATES[state_name]
    token = get_verification_token()
    r = session.post(
        DISTRICT_BIND,
        data={"__RequestVerificationToken": token, "state_id": aes_encrypt(str(state_id))},
        headers={"X-Requested-With": "XMLHttpRequest"}, timeout=30)
    rows = r.json()
    return {row["DistrictName"].strip(): row["JJM_DistrictId"]
            for row in rows if row.get("JJM_DistrictId") not in (None, "", " ")}


MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def parse_dt(text: str):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text or "")
    if m:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


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
            acceptable = cells[3] if len(cells) > 3 else ""
            permissible = cells[4] if len(cells) > 4 else ""
            value_raw = cells[5] if len(cells) > 5 else ""
            vm = re.match(r"([\d.]+)", value_raw.replace(",", ""))
            if not vm:
                continue

            def num(s: str):
                m2 = re.search(r"\d+(?:\.\d+)?", s or "")
                return float(m2.group()) if m2 else None
            results.append({
                "parameter": cells[1], "unit": cells[2],
                "acceptable": num(acceptable), "permissible": num(permissible),
                "value": float(vm.group(1)),
            })
        if results:
            break

    sid = sid_m.group(1)
    if not loc.get("state") or not loc.get("district"):
        return None

    return {
        "wqmis_sample_id": sid,
        "village": loc.get("village"), "gram_panchayat": loc.get("gram panchayat"),
        "block": loc.get("block"), "district": loc.get("district"),
        "state": loc.get("state"),
        "source": after(r"Source of Sample:", r"Village"),
        "collected_on": parse_dt(after(r"sample collection", r"Date & time of sample received")),
        "lab": after(r"Water Testing Laboratory,", ",") ,
        "results": results,
    }


def cached_html(internal_id: int, enc: str, keep_html: bool = False) -> tuple[str | None, bool]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    safe = enc.replace("/", "_").replace("+", "-").replace("=", "")
    path = RAW_DIR / f"{safe}.html"
    if path.exists():
        return path.read_text(errors="ignore"), True
    try:
        r = session.get(FINAL_REPORT, params={"s_id": enc}, timeout=40)
    except requests.RequestException:
        return None, False
    time.sleep(RATE_SECONDS)
    if keep_html:
        path.write_text(r.text, errors="ignore")
        return r.text, False
    return r.text, False


JSONL_PATH = RAW_DIR / "records.jsonl"
PROGRESS_PATH = RAW_DIR / "crawl_progress.txt"


def _load_progress() -> set[int]:
    done: set[int] = set()
    if PROGRESS_PATH.exists():
        done = {int(x) for x in PROGRESS_PATH.read_text().split()}
    return done


def _mark_done(internal_id: int):
    with PROGRESS_PATH.open("a") as fh:
        fh.write(f"{internal_id}\n")


def _append_record(record: dict):
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("a") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


STATE_ALIASES = {"uttar pradesh": "Uttar Pradesh", "bihar": "Bihar"}


def state_of(html: str) -> str | None:
    m = re.search(r"District-\s*[^,]+,\s*State-\s*([A-Za-z &]+)", html)
    if not m:
        return None
    return STATE_ALIASES.get(m.group(1).strip().lower())


def crawl(start: int, end: int, max_hits: int | None = None, keep_html: bool = False):
    done = _load_progress()
    hits, parsed_total, skipped = 0, 0, 0
    for internal_id in range(start, end + 1):
        if internal_id in done:
            skipped += 1
            continue
        enc = aes_encrypt(str(internal_id))
        html, was_cached = cached_html(internal_id, enc, keep_html=keep_html)
        if not html:
            print(f"  [{internal_id}] fetch failed", flush=True)
            continue
        record = parse_report(html)
        if record is None:
            _mark_done(internal_id)
            continue
        parsed_total += 1
        state_key = STATE_ALIASES.get((record["state"] or "").lower())
        if state_key is None:
            _mark_done(internal_id)
            continue
        record["state"] = state_key
        record["internal_id"] = internal_id
        hits += 1
        _append_record(record)
        _mark_done(internal_id)
        print(f"  [{internal_id}] HIT {state_key}/{record['district']}/{record['village']} "
              f"params={len(record['results'])}", flush=True)
        if max_hits and hits >= max_hits:
            print("hit cap reached", flush=True)
            break
    return parsed_total, hits


def map_ranges(start: int, end: int, stride: int):
    counts = {"Uttar Pradesh": 0, "Bihar": 0, "other": 0}
    ranges: dict[str, list[int]] = {}
    for internal_id in range(start, end + 1, stride):
        enc = aes_encrypt(str(internal_id))
        try:
            r = session.get(FINAL_REPORT, params={"s_id": enc}, timeout=40)
        except requests.RequestException as exc:
            print(f"  [{internal_id}] fail {exc}", flush=True)
            continue
        time.sleep(RATE_SECONDS)
        st = state_of(r.text)
        key = st or "other"
        counts[key] += 1
        lo, hi = ranges.get(key, [internal_id, internal_id])
        ranges[key] = [min(lo, internal_id), max(hi, internal_id)]
        print(f"  [{internal_id}] {key}", flush=True)
    print(json.dumps({"counts": counts, "ranges": ranges}, indent=1))


def pull_parameter_wise(cookie_file: Path, fy="2026-2027"):
    raise NotImplementedError(
        "awaiting authenticated session cookies; public crawler covers interim needs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["probe", "districts", "crawl", "pull", "map"])
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=50)
    ap.add_argument("--stride", type=int, default=50000)
    ap.add_argument("--max-hits", type=int, default=None)
    args = ap.parse_args()

    if args.command == "probe":
        ok = []
        for name, url in [("portal", f"{BASE}/WQMIS"), ("report_form", REPORT_P)]:
            r = session.get(url, timeout=20)
            ok.append(f"{name}: HTTP {r.status_code}")
        print(" | ".join(ok))
    elif args.command == "districts":
        for state in STATES:
            d = fetch_districts(state)
            print(f"{state}: {len(d)} districts; sample: {dict(list(d.items())[:3])}")
    elif args.command == "crawl":
        total, hits = crawl(args.start, args.end, max_hits=args.max_hits)
        print(f"parsed={total} target-state hits={hits}")
    elif args.command == "map":
        map_ranges(args.start, args.end, args.stride)
    elif args.command == "pull":
        pull_parameter_wise(None)


if __name__ == "__main__":
    main()
