import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AnalysisSession, SpeedEvent
from app.schemas import SessionOut
from app.config import settings
from app.detection import process_video

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

DEMO_VIDEO = os.path.join(os.path.dirname(__file__), "..", "..", "demo", "traffic-demo.mp4")


def _run_analysis(db: Session, video_path: str, filename: str, speed_limit_kmh: float, pixels_per_meter: float, calibrated: bool):
    session_id = uuid.uuid4().hex[:12]
    evidence_dir = os.path.join(settings.upload_dir, "evidence", session_id)

    session = AnalysisSession(
        id=session_id, source_filename=filename, speed_limit_kmh=speed_limit_kmh,
        pixels_per_meter=pixels_per_meter, calibrated=calibrated, status="processing",
    )
    db.add(session)
    db.commit()

    try:
        result = process_video(video_path, speed_limit_kmh, pixels_per_meter, evidence_dir=evidence_dir)
    except Exception as e:
        session.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Analysis failed: {e}")

    for ev in result["events"]:
        db.add(SpeedEvent(
            session_id=session_id,
            vehicle_track_id=ev["vehicle_track_id"],
            vehicle_class=ev["vehicle_class"],
            estimated_speed_kmh=ev["estimated_speed_kmh"],
            speed_limit_kmh=speed_limit_kmh,
            is_speeding=ev["is_speeding"],
            frame_number=ev["frame_number"],
            evidence_path=ev["evidence_path"],
        ))

    session.total_vehicles = result["total_vehicles"]
    session.max_speed_kmh = result["max_speed_kmh"]
    session.avg_speed_kmh = result["avg_speed_kmh"]
    session.speeding_count = result["speeding_count"]
    session.status = "completed"
    db.commit()
    db.refresh(session)
    return session


@router.post("", response_model=SessionOut)
async def analyze_video(
    file: UploadFile = File(...),
    speed_limit_kmh: float = Form(default=settings.default_speed_limit_kmh),
    pixels_per_meter: float = Form(default=settings.default_pixels_per_meter),
    calibrated: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    allowed = settings.allowed_video_types.split(",")
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    upload_path = os.path.join(settings.upload_dir, f"{uuid.uuid4().hex[:8]}_{file.filename}")
    with open(upload_path, "wb") as f:
        f.write(contents)

    return _run_analysis(db, upload_path, file.filename, speed_limit_kmh, pixels_per_meter, calibrated)


@router.post("/demo", response_model=SessionOut)
def analyze_demo(
    speed_limit_kmh: float = Form(default=settings.default_speed_limit_kmh),
    pixels_per_meter: float = Form(default=settings.default_pixels_per_meter),
    db: Session = Depends(get_db),
):
    if not os.path.exists(DEMO_VIDEO):
        raise HTTPException(status_code=404, detail="Demo video not found on server")
    return _run_analysis(db, DEMO_VIDEO, "traffic-demo.mp4", speed_limit_kmh, pixels_per_meter, calibrated=False)
