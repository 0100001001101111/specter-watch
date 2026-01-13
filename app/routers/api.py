"""API routes for SPECTER TRACKER - Geology Correlation Tracker."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import get_db
from ..models.schemas import UFOReport, Earthquake, HotspotCache
from ..services.usgs_client import USGSClient
from ..services.scoring import get_scoring_engine
from ..services.magnetic_grid import get_magnetic_grid

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "SPECTER TRACKER",
        "version": "2.0.0",
        "description": "UFO-Geology Correlation Tracker"
    }


@router.get("/earthquakes")
async def get_earthquakes(
    days: int = Query(7, ge=1, le=30),
    min_magnitude: float = Query(3.0, ge=0, le=10),
    db: Session = Depends(get_db)
):
    """Get recent earthquakes (overlay data, not predictions)."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= cutoff,
        Earthquake.magnitude >= min_magnitude
    ).order_by(Earthquake.datetime.desc()).limit(100).all()

    return {
        "count": len(earthquakes),
        "note": "Earthquake overlay for context - no prediction implied",
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
    """Fetch live earthquakes from USGS (context overlay only)."""
    with USGSClient() as client:
        earthquakes = client.get_recent_earthquakes(
            days=days,
            min_magnitude=min_magnitude
        )

    return {
        "count": len(earthquakes),
        "source": "USGS Live Feed",
        "note": "For map overlay context - not prediction targets",
        "earthquakes": earthquakes
    }


@router.get("/reports")
async def get_reports(
    days: int = Query(30, ge=1, le=365),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Get recent UFO reports with piezoelectric scores."""
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


@router.get("/reports/by-geology")
async def get_reports_by_geology(
    geology_type: str = Query("low_magnetic", regex="^(low_magnetic|high_magnetic|all)$"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get reports filtered by geology type (magnetic signature)."""
    query = db.query(UFOReport).filter(
        UFOReport.latitude.isnot(None),
        UFOReport.magnetic_anomaly.isnot(None)
    )

    if geology_type == "low_magnetic":
        # Piezoelectric zone: |magnetic| < 100 nT
        query = query.filter(
            UFOReport.magnetic_anomaly > -100,
            UFOReport.magnetic_anomaly < 100
        )
    elif geology_type == "high_magnetic":
        # Non-piezoelectric: |magnetic| >= 100 nT
        query = query.filter(
            (UFOReport.magnetic_anomaly <= -100) | (UFOReport.magnetic_anomaly >= 100)
        )

    reports = query.order_by(UFOReport.specter_score.desc()).limit(limit).all()

    return {
        "count": len(reports),
        "geology_type": geology_type,
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
                "magnetic_anomaly": r.magnetic_anomaly
            }
            for r in reports
        ]
    }


@router.get("/reports/high-score")
async def get_high_score_reports(
    min_score: float = Query(60, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get highest-scoring reports (likely piezoelectric terrain)."""
    reports = db.query(UFOReport).filter(
        UFOReport.specter_score >= min_score,
        UFOReport.scored == True
    ).order_by(UFOReport.specter_score.desc()).limit(limit).all()

    return {
        "count": len(reports),
        "min_score_filter": min_score,
        "interpretation": "High scores = low magnetic anomaly + orb/light shape + physical effects",
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


@router.get("/correlation")
async def get_geology_correlation(db: Session = Depends(get_db)):
    """Get correlation statistics between magnetic anomaly and report clustering."""
    # Get reports with magnetic data
    reports = db.query(UFOReport).filter(
        UFOReport.magnetic_anomaly.isnot(None),
        UFOReport.latitude.isnot(None)
    ).all()

    if len(reports) < 10:
        return {
            "status": "insufficient_data",
            "report_count": len(reports),
            "message": "Need at least 10 reports with magnetic data for correlation"
        }

    # Calculate statistics by magnetic zone
    low_mag = [r for r in reports if abs(r.magnetic_anomaly or 999) < 100]
    high_mag = [r for r in reports if abs(r.magnetic_anomaly or 0) >= 100]

    low_mag_scores = [r.specter_score for r in low_mag if r.specter_score]
    high_mag_scores = [r.specter_score for r in high_mag if r.specter_score]

    # Orb/light shapes by zone
    orb_shapes = ['orb', 'sphere', 'circle', 'light', 'fireball', 'flash']
    low_mag_orbs = sum(1 for r in low_mag if r.shape and r.shape.lower() in orb_shapes)
    high_mag_orbs = sum(1 for r in high_mag if r.shape and r.shape.lower() in orb_shapes)

    return {
        "status": "ok",
        "total_reports": len(reports),
        "zones": {
            "low_magnetic": {
                "count": len(low_mag),
                "avg_score": round(sum(low_mag_scores) / len(low_mag_scores), 1) if low_mag_scores else 0,
                "orb_percentage": round(100 * low_mag_orbs / len(low_mag), 1) if low_mag else 0
            },
            "high_magnetic": {
                "count": len(high_mag),
                "avg_score": round(sum(high_mag_scores) / len(high_mag_scores), 1) if high_mag_scores else 0,
                "orb_percentage": round(100 * high_mag_orbs / len(high_mag), 1) if high_mag else 0
            }
        },
        "interpretation": {
            "hypothesis": "Piezoelectric geology (low magnetic) produces more orb/light phenomena",
            "validated": "Magnetic-UFO correlation (rho=-0.497) is statistically significant",
            "note": "Earthquake timing correlation was NOT validated (M≥4.0 test failed)"
        }
    }


@router.get("/hotspots")
async def get_hotspots(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get hotspot locations by piezoelectric score."""
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
                "magnetic_anomaly": h.magnetic_anomaly
            }
            for h in hotspots
        ]
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)

    # Counts
    total_reports = db.query(func.count(UFOReport.id)).scalar() or 0
    total_earthquakes = db.query(func.count(Earthquake.id)).scalar() or 0

    # Reports with magnetic data
    reports_with_mag = db.query(func.count(UFOReport.id)).filter(
        UFOReport.magnetic_anomaly.isnot(None)
    ).scalar() or 0

    # High score reports (piezoelectric terrain)
    high_score_count = db.query(func.count(UFOReport.id)).filter(
        UFOReport.specter_score >= 60
    ).scalar() or 0

    # Low magnetic reports
    low_mag_count = db.query(func.count(UFOReport.id)).filter(
        UFOReport.magnetic_anomaly.isnot(None),
        UFOReport.magnetic_anomaly > -100,
        UFOReport.magnetic_anomaly < 100
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
            "reports_with_magnetic_data": reports_with_mag
        },
        "geology": {
            "low_magnetic_reports": low_mag_count,
            "high_score_reports": high_score_count,
            "average_score": round(avg_score, 1)
        },
        "note": "SPECTER TRACKER v2.0 - Correlation tracker, not earthquake predictor"
    }


@router.post("/score")
async def score_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    shape: str = Query("unknown"),
    description: str = Query("")
):
    """Score a location for piezoelectric potential (no earthquake timing)."""
    scorer = get_scoring_engine()

    # Score WITHOUT earthquake proximity (removed from v2.0)
    score = scorer.score_report(
        lat=latitude,
        lon=longitude,
        shape=shape,
        description=description,
        report_datetime=datetime.utcnow(),
        nearby_earthquakes=[]  # Empty - no earthquake scoring in v2.0
    )

    # Get magnetic anomaly directly
    grid = get_magnetic_grid()
    magnetic = grid.get_anomaly(latitude, longitude)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "shape": shape,
        "score": score,
        "magnetic_anomaly": magnetic,
        "interpretation": {
            "piezoelectric_zone": abs(magnetic or 999) < 100 if magnetic else None,
            "note": "Score based on magnetic signature, shape, and physical effects only"
        }
    }


@router.get("/magnetic")
async def get_magnetic_at_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Get magnetic anomaly value at a specific location."""
    grid = get_magnetic_grid()
    anomaly = grid.get_anomaly(latitude, longitude)

    if anomaly is None:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "magnetic_anomaly": None,
            "status": "out_of_grid_bounds"
        }

    return {
        "latitude": latitude,
        "longitude": longitude,
        "magnetic_anomaly": round(anomaly, 1),
        "geology_type": "piezoelectric" if abs(anomaly) < 100 else "non_piezoelectric",
        "interpretation": "Low |anomaly| (<100 nT) indicates potential piezoelectric terrain"
    }
