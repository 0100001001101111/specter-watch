"""API routes for SPECTER WATCH."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import get_db
from ..models.schemas import UFOReport, Earthquake, Watch, WatchResult, HotspotCache
from ..services.usgs_client import USGSClient
from ..services.scoring import get_scoring_engine
from ..services.watch_manager import WatchManager

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "SPECTER WATCH"
    }


@router.get("/earthquakes")
async def get_earthquakes(
    days: int = Query(7, ge=1, le=30),
    min_magnitude: float = Query(2.5, ge=0, le=10),
    db: Session = Depends(get_db)
):
    """Get recent earthquakes from database."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= cutoff,
        Earthquake.magnitude >= min_magnitude
    ).order_by(Earthquake.datetime.desc()).limit(100).all()

    return {
        "count": len(earthquakes),
        "earthquakes": [
            {
                "id": eq.id,
                "usgs_id": eq.usgs_id,
                "datetime": eq.datetime.isoformat() if eq.datetime else None,
                "latitude": eq.latitude,
                "longitude": eq.longitude,
                "magnitude": eq.magnitude,
                "place": eq.place
            }
            for eq in earthquakes
        ]
    }


@router.get("/earthquakes/live")
async def get_live_earthquakes(
    days: int = Query(1, ge=1, le=7),
    min_magnitude: float = Query(3.0, ge=0, le=10)
):
    """Fetch live earthquakes from USGS API."""
    with USGSClient() as client:
        earthquakes = client.get_recent_earthquakes(
            days=days,
            min_magnitude=min_magnitude
        )

    return {
        "count": len(earthquakes),
        "source": "USGS Live Feed",
        "earthquakes": earthquakes
    }


@router.get("/watches")
async def get_watches(
    status: str = Query("active", regex="^(active|triggered|expired|all)$"),
    db: Session = Depends(get_db)
):
    """Get SPECTER watches."""
    query = db.query(Watch)

    if status != "all":
        query = query.filter(Watch.status == status)

    watches = query.order_by(Watch.eq_datetime.desc()).limit(50).all()

    return {
        "count": len(watches),
        "watches": [
            {
                "id": w.id,
                "status": w.status,
                "eq_datetime": w.eq_datetime.isoformat() if w.eq_datetime else None,
                "eq_latitude": w.eq_latitude,
                "eq_longitude": w.eq_longitude,
                "eq_magnitude": w.eq_magnitude,
                "eq_place": w.eq_place,
                "watch_end": w.watch_end.isoformat() if w.watch_end else None,
                "magnetic_anomaly": w.magnetic_anomaly,
                "piezo_probability": w.piezo_probability
            }
            for w in watches
        ]
    }


@router.post("/watches/create")
async def create_watch_for_earthquake(
    usgs_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Create a watch for a specific earthquake."""
    # Fetch earthquake from USGS
    with USGSClient() as client:
        earthquakes = client.get_recent_earthquakes(days=7, min_magnitude=0)
        eq = next((e for e in earthquakes if e.get('usgs_id') == usgs_id), None)

    if not eq:
        raise HTTPException(status_code=404, detail="Earthquake not found")

    manager = WatchManager(db)
    watch = manager.create_watch_for_earthquake(eq)

    if not watch:
        raise HTTPException(status_code=400, detail="Could not create watch")

    return {
        "message": "Watch created",
        "watch_id": watch.id,
        "eq_magnitude": watch.eq_magnitude,
        "piezo_probability": watch.piezo_probability
    }


@router.get("/reports")
async def get_reports(
    days: int = Query(7, ge=1, le=90),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Get recent UFO reports."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(UFOReport).filter(
        UFOReport.datetime >= cutoff
    )

    if min_score > 0:
        query = query.filter(UFOReport.specter_score >= min_score)

    reports = query.order_by(UFOReport.datetime.desc()).limit(100).all()

    return {
        "count": len(reports),
        "reports": [
            {
                "id": r.id,
                "datetime": r.datetime.isoformat() if r.datetime else None,
                "city": r.city,
                "state": r.state,
                "shape": r.shape,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "specter_score": r.specter_score,
                "magnetic_anomaly": r.magnetic_anomaly,
                "description": r.description[:200] if r.description else None
            }
            for r in reports
        ]
    }


@router.get("/reports/high-score")
async def get_high_score_reports(
    min_score: float = Query(70, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get highest-scoring reports."""
    reports = db.query(UFOReport).filter(
        UFOReport.specter_score >= min_score,
        UFOReport.scored == True
    ).order_by(UFOReport.specter_score.desc()).limit(limit).all()

    return {
        "count": len(reports),
        "min_score_filter": min_score,
        "reports": [
            {
                "id": r.id,
                "datetime": r.datetime.isoformat() if r.datetime else None,
                "city": r.city,
                "state": r.state,
                "shape": r.shape,
                "specter_score": r.specter_score,
                "score_breakdown": r.score_breakdown,
                "magnetic_anomaly": r.magnetic_anomaly
            }
            for r in reports
        ]
    }


@router.get("/hotspots")
async def get_hotspots(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get cached hotspot analysis."""
    hotspots = db.query(HotspotCache).order_by(
        HotspotCache.avg_specter_score.desc()
    ).limit(limit).all()

    return {
        "count": len(hotspots),
        "hotspots": [
            {
                "city": h.city,
                "state": h.state,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "report_count": h.report_count,
                "avg_specter_score": h.avg_specter_score,
                "magnetic_anomaly": h.magnetic_anomaly,
                "seismic_ratio": h.seismic_ratio
            }
            for h in hotspots
        ]
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Counts
    total_reports = db.query(func.count(UFOReport.id)).scalar() or 0
    total_earthquakes = db.query(func.count(Earthquake.id)).scalar() or 0
    active_watches = db.query(func.count(Watch.id)).filter(
        Watch.status == 'active'
    ).scalar() or 0
    triggered_watches = db.query(func.count(Watch.id)).filter(
        Watch.status == 'triggered'
    ).scalar() or 0

    # Recent activity
    reports_24h = db.query(func.count(UFOReport.id)).filter(
        UFOReport.date_scraped >= last_24h
    ).scalar() or 0
    earthquakes_7d = db.query(func.count(Earthquake.id)).filter(
        Earthquake.datetime >= last_7d
    ).scalar() or 0

    # High score reports
    high_score_count = db.query(func.count(UFOReport.id)).filter(
        UFOReport.specter_score >= 70
    ).scalar() or 0

    # Average score
    avg_score = db.query(func.avg(UFOReport.specter_score)).filter(
        UFOReport.scored == True
    ).scalar() or 0

    return {
        "timestamp": now.isoformat(),
        "totals": {
            "ufo_reports": total_reports,
            "earthquakes": total_earthquakes,
            "active_watches": active_watches,
            "triggered_watches": triggered_watches
        },
        "recent": {
            "reports_24h": reports_24h,
            "earthquakes_7d": earthquakes_7d
        },
        "scoring": {
            "high_score_reports": high_score_count,
            "average_score": round(avg_score, 1)
        }
    }


@router.post("/score")
async def score_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    shape: str = Query("unknown"),
    description: str = Query("")
):
    """Score a hypothetical sighting location."""
    scorer = get_scoring_engine()

    # Get nearby earthquakes
    with USGSClient() as client:
        earthquakes = client.get_earthquakes_near(
            latitude, longitude, radius_km=150, days=7
        )

    score = scorer.score_report(
        lat=latitude,
        lon=longitude,
        shape=shape,
        description=description,
        report_datetime=datetime.utcnow(),
        nearby_earthquakes=earthquakes
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "shape": shape,
        "score": score,
        "nearby_earthquakes": len(earthquakes)
    }
