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


def test_dashboard_data_endpoint(client):
    res = client.get("/api/dashboard-data")
    assert res.status_code == 200
    data = res.json()
    assert "kpi" in data
    assert "priority" in data
    assert "details" in data
    assert "state_bands" in data
    assert "compare" in data
    assert data["kpi"]["samples"] >= len(data["priority"])
    if data["priority"]:
        first_pid = str(data["priority"][0]["sample_id"])
        assert first_pid in data["details"]
        assert "readings" in data["details"][first_pid]



def test_compare_top_exceedance_parameter(client):
    res = client.get("/api/compare")
    assert res.status_code == 200
    states = res.json()["states"]
    assert len(states) > 0
    for s in states:
        assert "top_exceedance_parameter" in s
        assert s["top_exceedance_parameter"] is None or isinstance(
            s["top_exceedance_parameter"], str
        )


def _make_unscored_sample(db):
    from datetime import datetime, timezone

    from app.models import District, Village, WaterSample

    district = db.query(District).filter(District.name == "Unnao").one()
    village = Village(district_id=district.id, name="Unscored Test Habitation")
    db.add(village)
    db.flush()
    ws = WaterSample(
        village_id=village.id,
        source_type="handpump",
        collected_on=datetime(2022, 6, 1, tzinfo=timezone.utc),
        wqmis_ref="TEST-UNSCORED-1",
    )
    db.add(ws)
    db.commit()
    return ws.id


def _drop_sample(db, sample_id):
    from app.models import Village, WaterSample

    village_id = db.query(WaterSample.village_id).filter(
        WaterSample.id == sample_id
    ).scalar()
    db.query(WaterSample).filter(WaterSample.id == sample_id).delete(
        synchronize_session=False
    )
    if village_id is not None:
        db.query(Village).filter(Village.id == village_id).delete(
            synchronize_session=False
        )
    db.commit()


def test_band_filter_excludes_unscored(db, client):
    sample_id = _make_unscored_sample(db)
    try:
        total = client.get("/api/samples", params={"limit": 500}).json()
        filtered = client.get(
            "/api/samples", params={"band": "critical", "limit": 500}
        ).json()
        assert len(filtered) < len(total)
        assert all(s["id"] != sample_id for s in filtered)
    finally:
        _drop_sample(db, sample_id)


def test_unscored_band_returns_only_unscored(db, client):
    sample_id = _make_unscored_sample(db)
    try:
        rows = client.get(
            "/api/samples", params={"band": "unscored", "limit": 500}
        ).json()
        assert [s["id"] for s in rows] == [sample_id]
    finally:
        _drop_sample(db, sample_id)


def test_band_filter_is_case_insensitive(client):
    lower = client.get("/api/samples", params={"band": "critical", "limit": 500}).json()
    upper = client.get("/api/samples", params={"band": "CRITICAL", "limit": 500}).json()
    assert [s["id"] for s in lower] == [s["id"] for s in upper]
    assert len(lower) > 0


def test_unknown_band_returns_400(client):
    res = client.get("/api/samples", params={"band": "bogus"})
    assert res.status_code == 400
    assert "bogus" in res.json()["detail"]


def test_band_filter_none_returns_all(client):
    all_rows = client.get("/api/samples", params={"limit": 500}).json()
    assert len(all_rows) > 0
def test_scoring_sample_returns_breakdown(client):
    sample_id = client.get("/api/samples", params={"limit": 1}).json()[0]["id"]
    res = client.get(f"/api/scoring/{sample_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["sample_id"] == sample_id
    assert 0.0 <= body["score"] <= 100.0
    assert body["band"] in {"Critical", "High", "Medium", "Low"}
    assert body["n_scored_params"] >= 0
    assert isinstance(body["breakdown"], list)
    for row in body["breakdown"]:
        assert {"parameter_key", "value", "weight", "severity", "exceeded"} <= set(row)
        assert 0.0 <= row["severity"] <= 1.0


def test_scoring_sample_agrees_with_priority_queue(client):
    sample_id = client.get("/api/priority/top/1").json()[0]["sample_id"]
    scored = client.get(f"/api/scoring/{sample_id}").json()
    queued = client.get("/api/priority/top/1").json()[0]
    assert round(scored["score"], 2) == round(queued["score"], 2)
    assert scored["band"] == queued["band"]


def test_scoring_sample_missing_returns_404(client):
    res = client.get("/api/scoring/999999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_scoring_sample_zero_readings_does_not_500(db, client):
    from datetime import datetime, timezone

    from app.models import District, Village, WaterSample

    district = db.query(District).filter(District.name == "Unnao").one()
    village = Village(district_id=district.id, name="Zero Reading Habitation")
    db.add(village)
    db.flush()
    ws = WaterSample(
        village_id=village.id,
        source_type="handpump",
        collected_on=datetime(2022, 6, 1, tzinfo=timezone.utc),
        wqmis_ref="TEST-ZERO-READINGS-1",
    )
    db.add(ws)
    db.commit()
    try:
        res = client.get(f"/api/scoring/{ws.id}")
        assert res.status_code == 200
        body = res.json()
        assert body["score"] == 0.0
        assert body["n_scored_params"] == 0
        assert body["breakdown"] == []
    finally:
        _drop_sample(db, ws.id)
