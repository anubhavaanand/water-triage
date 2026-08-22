from app.engine.recurrence import (
    classify_param,
    compute_recurrence,
    verdict_for,
)


def test_persistent_when_history_and_current_overlap():
    cls, score = compute_recurrence(
        {"arsenic": [2009, 2010, 2011]}, {"arsenic": 0.8}
    )
    assert cls["arsenic"] == "persistent"
    assert 0 < score <= 100


def test_historical_only_means_resolved():
    cls, _ = compute_recurrence({"fluoride": [2009]}, {})
    assert cls["fluoride"] == "historical-only"


def test_new_contamination_no_history():
    cls, _ = compute_recurrence({}, {"e_coli": 1.0})
    assert cls["e_coli"] == "new"


def test_score_orders_persistent_above_new():
    _, s_persistent = compute_recurrence(
        {"iron": [2009, 2010, 2011, 2012]}, {"iron": 0.9}
    )
    _, s_new = compute_recurrence({}, {"iron": 0.9})
    assert s_persistent > s_new


def test_verdicts():
    assert verdict_for(85, 2) == "chronic-hotspot"
    assert verdict_for(40, 1) == "recurring"
    assert verdict_for(20, 0) == "watchlist"
    assert verdict_for(0, 0) == "no-history"
