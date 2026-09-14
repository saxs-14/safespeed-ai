from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import Base, engine
from app.auth import require_api_key
from app.rate_limit import rate_limit
from app.routers import health, analyze, events, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(os.path.join(settings.upload_dir, "evidence"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(health.router)
app.include_router(
    analyze.router,
    dependencies=[Depends(require_api_key), Depends(rate_limit(max_requests=10, window_seconds=60))],
)
app.include_router(events.router, dependencies=[Depends(require_api_key)])
app.include_router(dashboard.router, dependencies=[Depends(require_api_key)])


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs"}
