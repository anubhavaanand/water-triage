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
            num = lambda s: float(re.sub(r"[^0-9.]", "", s)) if re.search(r"\d", s) else None
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


def cached_html(s_id_enc: str) -> tuple[str, bool]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    safe = s_id_enc.replace("/", "_").replace("+", "-").replace("=", "")
    path = RAW_DIR / f"{safe}.html"
    if path.exists():
        return path.read_text(errors="ignore"), True
    r = session.get(FINAL_REPORT, params={"s_id": s_id_enc}, timeout=40)
    time.sleep(RATE_SECONDS)
    path.write_text(r.text, errors="ignore")
    return r.text, False


STATE_ALIASES = {"uttar pradesh": "Uttar Pradesh", "bihar": "Bihar"}


def crawl(start: int, end: int, store_fn=None):
    hits, parsed_total = 0, 0
    for internal_id in range(start, end + 1):
        enc = aes_encrypt(str(internal_id))
        try:
            html, was_cached = cached_html(enc)
        except requests.RequestException as exc:
            print(f"  [{internal_id}] fetch failed: {exc}", flush=True)
            continue
        record = parse_report(html)
        if not record:
            continue
        parsed_total += 1
        state_key = STATE_ALIASES.get((record["state"] or "").lower())
        if state_key is None:
            continue
        record["state"] = state_key
        record["internal_id"] = internal_id
        hits += 1
        print(f"  [{internal_id}] HIT {state_key}/{record['district']}/{record['village']} "
              f"params={len(record['results'])}", flush=True)
        if store_fn:
            store_fn(record)
    return parsed_total, hits


def pull_parameter_wise(cookie_file: Path, fy="2026-2027"):
    raise NotImplementedError(
        "awaiting authenticated session cookies; public crawler covers interim needs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["probe", "districts", "crawl", "pull"])
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=50)
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
        total, hits = crawl(args.start, args.end)
        print(f"parsed={total} target-state hits={hits}")
    elif args.command == "pull":
        pull_parameter_wise(None)


if __name__ == "__main__":
    main()
