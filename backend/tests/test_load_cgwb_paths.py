"""load_cgwb_cpcb must resolve paths from the repo root, not hardcoded dirs."""

import os
import re
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "load_cgwb_cpcb.py"


def test_no_hardcoded_legacy_paths():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Downloaded_Datasets" not in text
    assert "codebase/data" not in text


def test_resolves_paths_from_repo_root():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))" in text


def test_no_silent_except_pass():
    text = SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"except[^\n]*:\s*\n\s*pass", text)
