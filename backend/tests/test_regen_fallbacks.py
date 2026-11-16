"""regen_fallbacks must not overwrite the committed meta.json."""

import json
import shutil
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
OUT = Path(__file__).resolve().parents[2] / "dashboard" / "public"


def test_enrich_does_not_mutate_source(tmp_path, monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "regen_fallbacks", SCRIPTS / "regen_fallbacks.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    src = OUT / "meta.json"
    if not src.exists():
        import pytest

        pytest.skip("dashboard/public/meta.json not present")

    original = src.read_text(encoding="utf-8")
    before = json.loads(original)

    # Point VAL_DIR at a temp dir so wq6_summary is simply skipped.
    monkeypatch.setattr(mod, "VAL_DIR", tmp_path)
    result = mod.enrich_meta_offline(src)

    # The committed file must be byte-identical afterwards.
    assert src.read_text(encoding="utf-8") == original
    assert result is not None
    assert result["corpus"]["samples"] == before["corpus"]["samples"]
