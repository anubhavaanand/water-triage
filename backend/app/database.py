import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

# Attempt to use the configured DATABASE_URL (e.g. PostgreSQL from Render).
# If that database is unreachable or credentials are invalid, fall back to
# an in-memory SQLite database so the API can still start and serve offline
# data (recorded fallback JSONs, scoring logic, etc.).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Proactively test the connection (lazy connect engines won't fail until later)
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
except Exception as e:
    import warnings
    warnings.warn(
        f"DATABASE_URL connection failed ({e!s}); falling back to in-memory SQLite. "
        "Live DB endpoints will return empty/404 responses."
    )
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
