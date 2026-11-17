from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import all_routers
from .database import Base, SessionLocal, engine
from .engine import seed_bis_parameters


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        with SessionLocal() as db:
            seed_bis_parameters(db)
    except Exception as e:
        import warnings
        warnings.warn(f"DB seeding skipped ({e!s}); API running in offline mode.")
    yield


app = FastAPI(
    title="WaterTriage API",
    description="Water quality risk scoring and intervention prioritization for UP & Bihar",
    version="0.1.0",
    lifespan=lifespan,
)

import os

_cors_origins = os.environ.get("CORS_ORIGINS", "")
allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()] if _cors_origins else ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

for router in all_routers:
    app.include_router(router, prefix="/api")

# Serve the React dashboard if the dist folder exists
dashboard_dist = Path(
    os.environ.get(
        "WATERTRIAGE_DASHBOARD_DIST",
        Path(__file__).resolve().parents[2] / "dashboard" / "dist",
    )
)
if os.path.isdir(dashboard_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(dashboard_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_dashboard(full_path: str):
        # Allow API routes to pass through (handled by routers above, but just in case)
        if full_path.startswith("api/"):
            return {"error": "Endpoint not found"}

        # Serve exact file if it exists in dist
        file_path = os.path.join(dashboard_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for React Router / SPA
        return FileResponse(os.path.join(dashboard_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {"service": "watertriage", "docs": "/docs", "warning": "Frontend dist folder not found"}
