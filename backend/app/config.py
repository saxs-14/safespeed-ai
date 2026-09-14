import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SafeSpeed AI"
    database_url: str = "sqlite:///./safespeed.db"
    default_speed_limit_kmh: float = 60.0
    default_pixels_per_meter: float = 8.0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 100
    allowed_video_types: str = "video/mp4,video/avi,video/x-msvideo,video/quicktime"
    allowed_image_types: str = "image/jpeg,image/png"

    class Config:
        env_file = ".env"


settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
