from app.engine.scoring import (
    BIS_10500,
    band_for,
    composite_score,
    parameter_severity,
)


def test_clean_water_scores_low():
    readings = {
        "ph": (7.2, BIS_10500["ph"]),
        "tds": (350.0, BIS_10500["tds"]),
        "fluoride": (0.6, BIS_10500["fluoride"]),
        "arsenic": (0.005, BIS_10500["arsenic"]),
        "nitrate": (20.0, BIS_10500["nitrate"]),
        "iron": (0.1, BIS_10500["iron"]),
        "turbidity": (0.8, BIS_10500["turbidity"]),
        "e_coli": (0.0, BIS_10500["e_coli"]),
    }
    score, band, worst = composite_score(readings)
    assert score == 0.0
    assert band == "Low"
    assert worst is None


def test_fluoride_exceedance_interpolates():
    r = parameter_severity(1.25, 1.0, 1.5, "threshold")
    assert abs(r.severity - 0.5) < 1e-9
    assert r.exceeded


def test_no_relaxation_parameter_full_on_any_exceedance():
    nitrate = parameter_severity(50.0, 45.0, None, "threshold")
    assert nitrate.severity == 1.0

    e_coli = parameter_severity(4.0, 0.0, 0.0, "microbial")
    assert e_coli.severity == 1.0


def test_ph_range_two_sided():
    acid = parameter_severity(5.5, 6.5, 8.5, "range")
    basic = parameter_severity(9.5, 6.5, 8.5, "range")
    inside = parameter_severity(7.0, 6.5, 8.5, "range")
    assert acid.severity == 1.0
    assert basic.severity == 1.0
    assert inside.severity == 0.0


def test_composite_ranks_e_coli_above_tds():
    bad_microbial = {
        "e_coli": (10.0, BIS_10500["e_coli"]),
        "ph": (7.0, BIS_10500["ph"]),
        "turbidity": (1.2, BIS_10500["turbidity"]),
    }
    mild_tds = {
        "tds": (900.0, BIS_10500["tds"]),
        "ph": (7.0, BIS_10500["ph"]),
        "turbidity": (1.2, BIS_10500["turbidity"]),
    }
    s1, b1, w1 = composite_score(bad_microbial)
    s2, b2, _ = composite_score(mild_tds)
    assert s1 > s2
    assert w1 == "e_coli"
    assert b1 == "Critical"
    assert b2 in {"Low", "Medium"}


def test_escalation_rules():
    fluoride_full = {"fluoride": (2.0, BIS_10500["fluoride"]), "ph": (7.0, BIS_10500["ph"])}
    _, band, worst = composite_score(fluoride_full)
    assert band in {"High", "Critical"}
    assert worst == "fluoride"

    arsenic_partial = {
        "arsenic": (0.03, BIS_10500["arsenic"]),
        "ph": (7.0, BIS_10500["ph"]),
        "tds": (300.0, BIS_10500["tds"]),
    }
    score, band_a, worst_a = composite_score(arsenic_partial)
    assert 0 < score < 50
    assert worst_a == "arsenic"

    e_coli_present = {"e_coli": (12.0, BIS_10500["e_coli"]), "ph": (7.0, BIS_10500["ph"])}
    _, band_e, _ = composite_score(e_coli_present)
    assert band_e == "Critical"


def test_bands():
    assert band_for(90) == "Critical"
    assert band_for(75) == "Critical"
    assert band_for(60) == "High"
    assert band_for(30) == "Medium"
    assert band_for(24.99) == "Low"
