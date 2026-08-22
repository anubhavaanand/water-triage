def test_priority_ranked_descending(client):
    res = client.get("/api/priority")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0
    band_rank = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}
    keys = [(band_rank[i["band"]], i["score"]) for i in items]
    assert keys == sorted(keys, reverse=True)
    assert items[0]["rank"] == 1
    assert items[0]["band"] == "Critical"


def test_top_n_endpoint(client):
    res = client.get("/api/priority/top/5")
    assert res.status_code == 200
    assert len(res.json()) == 5


def test_state_filter(client):
    up = client.get("/api/priority", params={"state": "Uttar Pradesh"}).json()
    bihar = client.get("/api/priority", params={"state": "Bihar"}).json()
    assert len(up) > 0 and len(bihar) > 0
    assert all(i["state"] == "Uttar Pradesh" for i in up)
    assert all(i["state"] == "Bihar" for i in bihar)


def test_compare_returns_both_states(client):
    res = client.get("/api/compare")
    assert res.status_code == 200
    states = {s["state"] for s in res.json()["states"]}
    assert {"Uttar Pradesh", "Bihar"} <= states


def test_districts_summary(client):
    res = client.get("/api/districts")
    assert res.status_code == 200
    rows = res.json()
    names = {r["name"] for r in rows}
    assert {"Unnao", "Ferozabad", "Hardoi", "Katihar", "Araria", "Saharsa"} <= names
    for r in rows:
        assert set(r["band_counts"].keys()) == {"Critical", "High", "Medium", "Low"}


def test_sample_detail(client):
    top = client.get("/api/priority/top/1").json()[0]
    res = client.get(f"/api/samples/{top['sample_id']}")
    assert res.status_code == 200
    body = res.json()
    assert len(body["readings"]) >= 2
    assert body["risk_score"]["band"] in {"Critical", "High"}


def test_sample_404(client):
    res = client.get("/api/samples/999999")
    assert res.status_code == 404


def test_recompute_idempotent(db, client):
    before = client.get("/api/priority").json()[0]
    from app.engine import compute_scores

    compute_scores(db)
    after = client.get("/api/priority").json()[0]
    assert before["score"] == after["score"]
