from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_meta_invariants():
    resp = client.get("/api/meta")
    assert resp.status_code == 200
    data = resp.json()
    
    # 1. sum(bands) == samples
    total_samples = data["corpus"]["samples"]
    band_sum = sum(data["bands"].values())
    assert band_sum == total_samples, f"Bands sum {band_sum} != {total_samples}"
    
    # 2. sum(state samples) == samples
    state_sum = sum(s["samples"] for s in data["state_comparison"])
    assert state_sum == total_samples, f"State sum {state_sum} != {total_samples}"
    
    # 3. sum(n_params buckets) == samples per state
    for s in data["state_comparison"]:
        n_params_sum = sum(s["samples_by_n_params"].values())
        assert n_params_sum == s["samples"], f"{s['state']}: {n_params_sum} != {s['samples']}"
        
    # 4. sum(n_params * count) == readings
    total_readings = data["corpus"]["readings"]
    calc_readings = 0
    for s in data["state_comparison"]:
        for n_str, count in s["samples_by_n_params"].items():
            calc_readings += int(n_str) * count
    assert calc_readings == total_readings, f"Readings sum {calc_readings} != {total_readings}"

