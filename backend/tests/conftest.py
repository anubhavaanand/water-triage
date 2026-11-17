import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TEST_DB = BACKEND_DIR.parent / "data" / "test_watertriage.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.engine import compute_scores, seed_bis_parameters  # noqa: E402
from app.main import app  # noqa: E402
from etl.load_data import load  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_bis_parameters(db)
        stats = load(db)
    assert stats["inserted"] > 0
    assert stats["scored"] > 0
    yield
    Base.metadata.drop_all(bind=engine)
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db():
    with SessionLocal() as session:
        yield session


__all__ = ["client", "db", "compute_scores", "seed_bis_parameters"]


def drop_test_sample(db, sample_id):
    """Delete a sample and its village so tests do not collide on villages."""
    from app.models import Village, WaterSample

    village_id = db.query(WaterSample.village_id).filter(
        WaterSample.id == sample_id
    ).scalar()
    db.query(WaterSample).filter(WaterSample.id == sample_id).delete(
        synchronize_session=False
    )
    if village_id is not None:
        db.query(Village).filter(Village.id == village_id).delete(
            synchronize_session=False
        )
    db.commit()


__all__ += ["drop_test_sample"]
