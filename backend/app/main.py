"""Agnes Studio - Main FastAPI Application"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api import auth, images, videos, gallery, users, api_keys
from app.models.database import engine, Base

# Structured logging with configurable level
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("agnes_studio")

# SQLite concurrency warning
if "sqlite" in settings.DATABASE_URL and os.environ.get("UVICORN_WORKERS", "1") != "1":
    logger.warning(
        "⚠️  SQLite detected with multiple workers. This may cause database locking issues. "
        "Consider using PostgreSQL for production with multiple workers."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    logger.info("Starting Agnes Studio API...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")
    yield
    # Shutdown: cleanup
    logger.info("Shutting down Agnes Studio API...")
    await engine.dispose()


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Agnes Studio API",
    description="AI Image & Video Generation Platform powered by Agnes AI",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - restrict to specific methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BASE_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Global exception handler - do not leak internal details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Static files for generated content
generated_dir = Path("generated")
generated_dir.mkdir(exist_ok=True)
app.mount("/generated", StaticFiles(directory=str(generated_dir)), name="generated")

# Static files for uploads (reference images, etc.)
uploads_dir = Path(settings.UPLOAD_DIR)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# API Routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(api_keys.router, prefix="/api/keys", tags=["api_keys"])


@app.get("/api/health")
async def health_check():
    """Health check with dependency verification"""
    db_ok = False
    try:
        from app.core.database import async_session
        async with async_session() as session:
            await session.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")

    return {
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
    }
