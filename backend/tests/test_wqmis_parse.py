from pathlib import Path

from etl.wqmis import parse_report

FIXTURE = Path(__file__).parent / "fixtures" / "report_himachal.html"


def test_parses_real_report():
    record = parse_report(FIXTURE.read_text(errors="ignore"))
    assert record is not None
    assert record["wqmis_sample_id"] == "U695645L661S1"
    assert record["village"] == "Basal"
    assert record["district"] == "Solan"
    assert record["state"] == "Himachal Pradesh"
    assert record["collected_on"] is not None
    assert isinstance(record["results"], list)
    assert len(record["results"]) >= 1
    first = record["results"][0]
    assert first["parameter"] == "Total coliform*"
    assert first["unit"] == "CFU/ 100 ml"
    assert first["value"] == 0.0


def test_garbage_returns_none():
    assert parse_report("<html><body>nothing here</body></html>") is None
