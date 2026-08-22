from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import all_routers
from .database import Base, SessionLocal, engine
from .engine import seed_bis_parameters


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_bis_parameters(db)
    yield


app = FastAPI(
    title="WaterTriage API",
    description="Water quality risk scoring and intervention prioritization for UP & Bihar",
    version="0.1.0",
    lifespan=lifespan,
)

for router in all_routers:
    app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"service": "watertriage", "docs": "/docs"}
