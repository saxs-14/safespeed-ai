from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import SpeedEvent, AnalysisSession
from app.schemas import DashboardSummary
from app.config import settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total_vehicles = db.query(func.count(SpeedEvent.id)).scalar() or 0
    avg_speed = db.query(func.avg(SpeedEvent.estimated_speed_kmh)).scalar() or 0.0
    max_speed = db.query(func.max(SpeedEvent.estimated_speed_kmh)).scalar() or 0.0
    speeding = db.query(func.count(SpeedEvent.id)).filter(SpeedEvent.is_speeding == True).scalar() or 0  # noqa: E712
    total_sessions = db.query(func.count(AnalysisSession.id)).scalar() or 0

    return DashboardSummary(
        total_vehicles=total_vehicles,
        average_speed_kmh=round(avg_speed, 1),
        max_speed_kmh=round(max_speed, 1),
        speeding_count=speeding,
        total_sessions=total_sessions,
        speed_limit_kmh=settings.default_speed_limit_kmh,
    )
