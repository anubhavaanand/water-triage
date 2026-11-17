import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from close_data_gaps import MISSING_LAB_PROBES, load_lab_probes  # noqa: E402


def test_no_live_session_tokens_in_source():
    """The s_id values are live WQMIS session tokens and must stay out of git."""
    offenders = {
        code: info["s_id"]
        for code, info in MISSING_LAB_PROBES.items()
        if info.get("s_id")
    }
    assert not offenders, f"live s_id tokens committed for: {sorted(offenders)}"


def test_lab_probe_defaults_are_complete():
    assert len(MISSING_LAB_PROBES) == 15
    for code, info in MISSING_LAB_PROBES.items():
        assert info["state"] in {"Bihar", "Uttar Pradesh"}
        assert info["unassigned_count"] > 0
        assert isinstance(info["internal_id"], int)


def test_overlay_merges_tokens_and_ignores_unknown_lab_ids(tmp_path):
    manifest = tmp_path / "lab_probes.local.json"
    manifest.write_text(
        json.dumps({"L268": "TOKEN-A", "L999": "SHOULD-BE-IGNORED"}),
        encoding="utf-8",
    )

    merged = load_lab_probes(manifest)

    assert merged["L268"]["s_id"] == "TOKEN-A"
    assert merged["L405"]["s_id"] == ""
    assert "L999" not in merged


def test_loader_degrades_without_manifest(tmp_path):
    merged = load_lab_probes(tmp_path / "absent.json")

    assert len(merged) == 15
    assert all(not info["s_id"] for info in merged.values())


def test_loader_survives_malformed_manifest(tmp_path):
    manifest = tmp_path / "lab_probes.local.json"
    manifest.write_text("{not valid json", encoding="utf-8")

    merged = load_lab_probes(manifest)

    assert len(merged) == 15
    assert all(not info["s_id"] for info in merged.values())