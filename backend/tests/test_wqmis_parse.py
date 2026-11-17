from pathlib import Path

from etl.wqmis import parse_report

# Out-of-scope control. WaterTriage covers Uttar Pradesh and Bihar only
# (see AGENTS.md and scripts/district_registry.py), but the parser is
# region-agnostic: it reads whatever WQMIS publishes. This fixture is a real
# WQMIS report from Himachal Pradesh, kept precisely because it is outside
# the project's scope — it proves the parser keys off the HTML structure
# rather than any state name.
FIXTURE = Path(__file__).parent / "fixtures" / "report_himachal.html"


def test_parses_real_report():
    """Parse a real WQMIS report held as an out-of-scope control."""
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


def test_fixture_is_out_of_scope():
    """Guard the premise of the test above: this record is not UP or Bihar.

    If the fixture is ever swapped for an in-scope report, this assertion
    fails and the comment above must be rewritten.
    """
    record = parse_report(FIXTURE.read_text(errors="ignore"))
    assert record["state"] not in {"Uttar Pradesh", "Bihar"}


def test_garbage_returns_none():
    assert parse_report("<html><body>nothing here</body></html>") is None
