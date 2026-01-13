"""Dashboard routes with HTML templates - SPECTER TRACKER v2.0."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from ..models.database import get_db
from ..models.schemas import UFOReport, Earthquake

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(tags=["dashboard"])


def get_correlation_stats(db: Session):
    """Calculate geology correlation statistics."""
    reports = db.query(UFOReport).filter(
        UFOReport.magnetic_anomaly.isnot(None),
        UFOReport.latitude.isnot(None)
    ).all()

    if len(reports) < 10:
        return None

    # Split by magnetic zone
    low_mag = [r for r in reports if abs(r.magnetic_anomaly or 999) < 100]
    high_mag = [r for r in reports if abs(r.magnetic_anomaly or 0) >= 100]

    low_mag_scores = [r.specter_score for r in low_mag if r.specter_score]
    high_mag_scores = [r.specter_score for r in high_mag if r.specter_score]

    # Orb/light shapes by zone
    orb_shapes = ['orb', 'sphere', 'circle', 'light', 'fireball', 'flash']
    low_mag_orbs = sum(1 for r in low_mag if r.shape and r.shape.lower() in orb_shapes)
    high_mag_orbs = sum(1 for r in high_mag if r.shape and r.shape.lower() in orb_shapes)

    return {
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
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page - SPECTER TRACKER v2.0."""
    now = datetime.utcnow()

    # Get geology-focused stats
    total_reports = db.query(func.count(UFOReport.id)).scalar() or 0

    low_magnetic_reports = db.query(func.count(UFOReport.id)).filter(
        UFOReport.magnetic_anomaly.isnot(None),
        UFOReport.magnetic_anomaly > -100,
        UFOReport.magnetic_anomaly < 100
    ).scalar() or 0

    high_score_count = db.query(func.count(UFOReport.id)).filter(
        UFOReport.specter_score >= 60
    ).scalar() or 0

    avg_score = db.query(func.avg(UFOReport.specter_score)).filter(
        UFOReport.scored == True
    ).scalar() or 0

    # Get reports
    high_score_reports = db.query(UFOReport).filter(
        UFOReport.specter_score >= 60
    ).order_by(UFOReport.specter_score.desc()).limit(10).all()

    recent_reports = db.query(UFOReport).filter(
        UFOReport.datetime >= now - timedelta(days=30)
    ).order_by(UFOReport.datetime.desc()).limit(10).all()

    # Get earthquakes (context only)
    recent_earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= now - timedelta(days=7),
        Earthquake.magnitude >= 3.0
    ).order_by(Earthquake.datetime.desc()).limit(10).all()

    # Get correlation stats
    correlation = get_correlation_stats(db)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "now": now,
        "stats": {
            "total_reports": total_reports,
            "low_magnetic_reports": low_magnetic_reports,
            "high_score_reports": high_score_count,
            "avg_score": round(avg_score, 1)
        },
        "correlation": correlation,
        "high_score_reports": high_score_reports,
        "recent_reports": recent_reports,
        "recent_earthquakes": recent_earthquakes
    })


@router.get("/map", response_class=HTMLResponse)
async def map_view(request: Request, db: Session = Depends(get_db)):
    """Interactive geology map view."""
    now = datetime.utcnow()

    # Get reports with location data
    recent_reports = db.query(UFOReport).filter(
        UFOReport.latitude.isnot(None),
        UFOReport.longitude.isnot(None)
    ).order_by(UFOReport.datetime.desc()).limit(500).all()

    # Get earthquakes (context overlay)
    recent_earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= now - timedelta(days=7)
    ).limit(100).all()

    # Serialize for JSON
    reports_data = [
        {
            "latitude": r.latitude,
            "longitude": r.longitude,
            "city": r.city,
            "state": r.state,
            "shape": r.shape,
            "specter_score": r.specter_score,
            "magnetic_anomaly": r.magnetic_anomaly
        }
        for r in recent_reports
    ]

    earthquakes_data = [
        {
            "latitude": eq.latitude,
            "longitude": eq.longitude,
            "magnitude": eq.magnitude,
            "place": eq.place,
            "datetime": eq.datetime.isoformat() if eq.datetime else None
        }
        for eq in recent_earthquakes
    ]

    return templates.TemplateResponse("map.html", {
        "request": request,
        "reports": reports_data,
        "earthquakes": earthquakes_data
    })
