"""Application Configuration"""
import secrets
import warnings
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Agnes AI
    AGNES_API_KEY: str
    AGNES_API_BASE: str = "https://apihub.agnes-ai.com/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./agnes_studio.db"

    # JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Storage
    UPLOAD_DIR: str = "./uploads"
    GENERATED_DIR: str = "./generated"
    BASE_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Generation Settings
    IMAGE_DEFAULT_SIZE: str = "1024x768"
    VIDEO_DEFAULT_FRAMES: int = 121
    VIDEO_DEFAULT_FPS: int = 24

    # Pricing (credits)
    IMAGE_COST: int = 1  # 1 credit per image
    VIDEO_COST_PER_SECOND: int = 2  # 2 credits per second of video
    FREE_CREDITS_ON_REGISTER: int = 12
    REFERRAL_BONUS: int = 5

    # Rate limiting (requests per minute)
    RATE_LIMIT_AUTH: str = "5/minute"  # Login/Register
    RATE_LIMIT_GENERATE: str = "10/hour"  # Image/Video generation
    RATE_LIMIT_DEFAULT: str = "60/minute"  # Default for other endpoints

    # Agnes AI Models
    IMAGE_MODELS: dict = {
        "agnes-image-2.0-flash": "Fast image generation (text-to-image, image-to-image)",
        "agnes-image-2.1-flash": "Enhanced image generation with better high-density details (recommended)"
    }
    VIDEO_MODEL: str = "agnes-video-v2.0"

    # Valid image sizes
    VALID_IMAGE_SIZES: list = [
        "1024x768",   # Standard
        "1024x1024",  # Square
        "768x1024",   # Portrait
        "2048x2048",  # 2K Square
        "4096x4096",  # 4K Square
        "1816x1024",  # 16:9 Wide
        "1024x1816",  # 9:16 Portrait
    ]

    # Valid frame counts (must be 8n+1 and <= 441)
    VALID_FRAME_COUNTS: list = [81, 121, 161, 241, 441]
    DEFAULT_FRAME_RATE: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Enforce secure SECRET_KEY
if not settings.SECRET_KEY or settings.SECRET_KEY in (
    "change-me-in-production",
    "change-me-to-a-secure-random-string",
    "",
):
    raise RuntimeError(
        "SECRET_KEY must be set to a secure random value in .env. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )
