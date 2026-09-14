from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SpeedEventOut(BaseModel):
    id: int
    session_id: str
    vehicle_track_id: int
    vehicle_class: str
    estimated_speed_kmh: float
    speed_limit_kmh: float
    is_speeding: bool
    frame_number: int
    timestamp: datetime
    evidence_path: Optional[str] = None

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id: str
    source_filename: str
    speed_limit_kmh: float
    pixels_per_meter: float
    calibrated: bool
    total_vehicles: int
    max_speed_kmh: float
    avg_speed_kmh: float
    speeding_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_vehicles: int
    average_speed_kmh: float
    max_speed_kmh: float
    speeding_count: int
    total_sessions: int
    speed_limit_kmh: float
