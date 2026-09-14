import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models import SpeedEvent
from app.schemas import SpeedEventOut

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=List[SpeedEventOut])
def list_events(
    session_id: Optional[str] = None,
    speeding_only: bool = False,
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(SpeedEvent)
    if session_id:
        q = q.filter(SpeedEvent.session_id == session_id)
    if speeding_only:
        q = q.filter(SpeedEvent.is_speeding == True)  # noqa: E712
    return q.order_by(SpeedEvent.timestamp.desc()).limit(limit).all()


@router.get("/export")
def export_events(session_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(SpeedEvent)
    if session_id:
        q = q.filter(SpeedEvent.session_id == session_id)
    events = q.order_by(SpeedEvent.timestamp.desc()).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "session_id", "vehicle_track_id", "vehicle_class",
        "estimated_speed_kmh", "speed_limit_kmh", "is_speeding",
        "frame_number", "timestamp",
    ])
    for e in events:
        writer.writerow([
            e.id, e.session_id, e.vehicle_track_id, e.vehicle_class,
            e.estimated_speed_kmh, e.speed_limit_kmh, e.is_speeding,
            e.frame_number, e.timestamp,
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=safespeed_events.csv"},
    )
