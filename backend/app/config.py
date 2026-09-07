import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'data' / 'watertriage.db'}")

if DATABASE_URL.startswith("sqlite:///"):
    raw_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if raw_path and raw_path != ":memory:":
        db_path = Path(raw_path)
        if not db_path.is_absolute():
            db_path = (ROOT_DIR / db_path).resolve()
            DATABASE_URL = f"sqlite:///{db_path}"
        db_path.parent.mkdir(parents=True, exist_ok=True)

