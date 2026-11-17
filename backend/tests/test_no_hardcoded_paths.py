"""No script may hardcode a developer's home directory or a DB password."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"

OFFENDERS = [
    "export_complete_wq6.py",
    "generate_chart.py",
    "load_cgwb_cpcb.py",
    "close_data_gaps.py",
    "load_data.py",
]


def test_scripts_have_no_personal_paths():
    for name in OFFENDERS:
        path = SCRIPTS / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Ignore comment lines, which may quote the old path for context.
        code = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        assert "/home/anubhavanand" not in code, f"{name} hardcodes a home directory"
        assert "SECRET_REDACTED" not in code, f"{name} has a placeholder password"


def test_no_literal_password_assignment():
    pattern = re.compile(r"password\s*=\s*['\"][^'\"]+['\"]")
    for name in OFFENDERS:
        path = SCRIPTS / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        code = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        assert not pattern.search(code), f"{name} assigns a literal password"
