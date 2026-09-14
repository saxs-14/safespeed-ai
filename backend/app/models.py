from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from datetime import datetime, timezone
from app.database import Base


class SpeedEvent(Base):
    __tablename__ = "speed_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    vehicle_track_id = Column(Integer)
    vehicle_class = Column(String)
    estimated_speed_kmh = Column(Float)
    speed_limit_kmh = Column(Float)
    is_speeding = Column(Boolean, default=False)
    frame_number = Column(Integer)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    evidence_path = Column(String, nullable=True)


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String, primary_key=True, index=True)
    source_filename = Column(String)
    speed_limit_kmh = Column(Float)
    pixels_per_meter = Column(Float)
    calibrated = Column(Boolean, default=False)
    total_vehicles = Column(Integer, default=0)
    max_speed_kmh = Column(Float, default=0.0)
    avg_speed_kmh = Column(Float, default=0.0)
    speeding_count = Column(Integer, default=0)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
