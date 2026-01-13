"""SPECTER WATCH - Real-time UFO-Earthquake Correlation Tracker."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.models.database import init_db
from app.routers import api_router, dashboard_router
from app.services.magnetic_grid import get_magnetic_grid


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    print("=" * 60)
    print("SPECTER WATCH - Starting up...")
    print("=" * 60)

    try:
        # Initialize database
        print("Initializing database...")
        init_db()
    except Exception as e:
        print(f"Database init error (non-fatal): {e}")

    # Skip magnetic grid on startup - load lazily on first use
    print("Magnetic grid will load on first use...")

    print("SPECTER WATCH ready!")
    print("=" * 60)

    yield

    # Shutdown
    print("SPECTER WATCH shutting down...")


app = FastAPI(
    title="SPECTER TRACKER",
    description="UFO-Geology Correlation Tracker - Mapping reports on piezoelectric terrain",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(api_router)
app.include_router(dashboard_router)

# Serve static files if they exist
static_dir = os.path.join(os.path.dirname(__file__), "app", "templates", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "service": "SPECTER WATCH",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "earthquakes": "/api/earthquakes",
            "watches": "/api/watches",
            "reports": "/api/reports",
            "hotspots": "/api/hotspots",
            "stats": "/api/stats",
            "score": "/api/score",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
