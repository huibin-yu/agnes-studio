"""Utility Functions"""
import os
import re
import secrets
from pathlib import Path
from datetime import datetime, timezone


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove potentially dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    filename = re.sub(r'\.\.', '_', filename)  # Prevent directory traversal
    filename = filename[:200]  # Limit length
    return filename


def generate_short_id(length: int = 8) -> str:
    """Generate a short random ID"""
    return secrets.token_hex(length // 2)


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def ensure_dir(path: str) -> Path:
    """Ensure directory exists"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_timestamp() -> str:
    """Get current UTC timestamp string"""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def get_date_dir() -> str:
    """Get date-based directory structure"""
    return datetime.now(timezone.utc).strftime("%Y/%m/%d")
