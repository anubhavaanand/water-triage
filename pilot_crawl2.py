import requests
import random
import time
import subprocess
import urllib3
urllib3.disable_warnings()

KEY_HEX = b"38303830383038303830383038303830"
headers = {'User-Agent': 'WaterTriage-ETL/0.1 (academic project; student pilot sampling)'}
s = requests.Session()
s.headers.update(headers)

def aes_encrypt(value: str) -> str:
    out = subprocess.run(
        ["openssl", "enc", "-aes-128-cbc", "-K", KEY_HEX.decode(), "-iv", KEY_HEX.decode(),
         "-nosalt", "-base64"],
        input=value.encode(), capture_output=True, check=True)
    return out.stdout.decode().strip()

# 100 requests to get a fast sample
ids = random.sample(range(1010000, 1050000), 50)

valid_count = 0
up_count = 0
bihar_count = 0
blocks = 0
attempted = 0

print("Pilot Crawl: starting...", flush=True)
for i in ids:
    enc_id = aes_encrypt(str(i))
    try:
        attempted += 1
        r = s.get(f"https://ejalshakti.gov.in/WQMIS/Common/final_report_print?s_id={enc_id}", verify=False, timeout=5)
        if r.status_code != 200:
            if r.status_code == 500:
                pass # empty report
            else:
                print(f"Blocked or error on ID {i}: {r.status_code}")
                blocks += 1
                break
        else:
            text = r.text
            if "District-" in text and "State-" in text:
                valid_count += 1
                if "Uttar Pradesh" in text or "UTTAR PRADESH" in text:
                    up_count += 1
                elif "Bihar" in text or "BIHAR" in text:
                    bihar_count += 1
    except Exception as e:
        print(f"Exception on ID {i}: {e}")
        blocks += 1
        break

print(f"Results: {attempted} attempted, {valid_count} valid reports, {up_count} UP, {bihar_count} Bihar, {blocks} blocks.")
