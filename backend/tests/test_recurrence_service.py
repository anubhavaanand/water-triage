"""Integration tests for recurrence_service against the real PostgreSQL database."""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Use env variable INTEGRATION_DB_URL
POSTGRES_URL = os.environ.get("INTEGRATION_DB_URL", "postgresql://jjm_user:D0hL5JJbc8JazKfcXKI8@localhost:5432/jjm_triage")

try:
    _engine = create_engine(POSTGRES_URL)
    with _engine.connect() as _conn:
        _conn.execute(text("SELECT 1"))
except Exception as exc:  # pragma: no cover
    pytest.skip(f"PostgreSQL unavailable at {POSTGRES_URL}: {exc}", allow_module_level=True)

from sqlalchemy.orm import sessionmaker  # noqa: E402
from app.engine.recurrence_service import list_recurrent_districts  # noqa: E402

SessionTesting = sessionmaker(bind=_engine)

@pytest.fixture
def pg_db():
    session = SessionTesting()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_list_recurrent_districts(pg_db):
    res = list_recurrent_districts(pg_db)
    assert isinstance(res, list)
