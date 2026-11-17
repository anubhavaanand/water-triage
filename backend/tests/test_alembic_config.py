"""Guards against machine-specific paths leaking back into the config."""

from pathlib import Path

import pytest

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
ALEMBIC_ENV = Path(__file__).resolve().parents[1] / "alembic" / "env.py"


def test_alembic_ini_has_no_absolute_developer_path():
    text = ALEMBIC_INI.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("sqlalchemy.url"):
            _, _, value = line.partition("=")
            value = value.strip()
            assert not Path(value).is_absolute(), (
                f"alembic.ini pins an absolute path: {value!r}"
            )
            assert "anubhavanand" not in value


def test_alembic_env_overrides_url_from_database_url():
    text = ALEMBIC_ENV.read_text(encoding="utf-8")
    assert "DATABASE_URL" in text
    assert 'set_main_option("sqlalchemy.url"' in text
