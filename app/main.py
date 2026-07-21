"""FastAPI application entry point — replaces Flask app.py."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup: verify DB connection
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
    yield
    # Shutdown: dispose engine
    engine.dispose()


app = FastAPI(
    title="房屋租赁系统 API",
    description="House Rental System — FastAPI Migration",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Mount v1 API router
app.include_router(api_v1_router)

# Serve locally uploaded avatars from the same relative URLs returned by the API.
images_dir = Path(__file__).resolve().parent.parent / "images"
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=images_dir), name="images")


@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI backend is running."}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.get("/readyz")
def readyz():
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return Response(
            content='{"status":"not ready"}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )
