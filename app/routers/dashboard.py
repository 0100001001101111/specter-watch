"""Dashboard routes with HTML templates."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from ..models.database import get_db
from ..models.schemas import UFOReport, Earthquake, Watch, WatchResult

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    now = datetime.utcnow()

    # Get stats
    active_watches = db.query(Watch).filter(Watch.status == 'active').count()
    triggered_watches = db.query(Watch).filter(Watch.status == 'triggered').count()

    recent_reports = db.query(UFOReport).filter(
        UFOReport.datetime >= now - timedelta(days=7)
    ).count()

    high_score_reports = db.query(UFOReport).filter(
        UFOReport.specter_score >= 70
    ).order_by(UFOReport.specter_score.desc()).limit(10).all()

    recent_earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= now - timedelta(days=3),
        Earthquake.magnitude >= 3.0
    ).order_by(Earthquake.datetime.desc()).limit(10).all()

    active_watch_list = db.query(Watch).filter(
        Watch.status == 'active'
    ).order_by(Watch.eq_datetime.desc()).limit(10).all()

    triggered_list = db.query(Watch).filter(
        Watch.status == 'triggered'
    ).order_by(Watch.eq_datetime.desc()).limit(10).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "now": now,
        "stats": {
            "active_watches": active_watches,
            "triggered_watches": triggered_watches,
            "recent_reports": recent_reports
        },
        "high_score_reports": high_score_reports,
        "recent_earthquakes": recent_earthquakes,
        "active_watches": active_watch_list,
        "triggered_watches": triggered_list
    })


@router.get("/map", response_class=HTMLResponse)
async def map_view(request: Request, db: Session = Depends(get_db)):
    """Interactive map view."""
    now = datetime.utcnow()

    # Get data for map
    active_watches = db.query(Watch).filter(
        Watch.status == 'active'
    ).all()

    recent_reports = db.query(UFOReport).filter(
        UFOReport.datetime >= now - timedelta(days=7),
        UFOReport.latitude.isnot(None),
        UFOReport.longitude.isnot(None)
    ).limit(100).all()

    recent_earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= now - timedelta(days=7)
    ).limit(100).all()

    return templates.TemplateResponse("map.html", {
        "request": request,
        "watches": active_watches,
        "reports": recent_reports,
        "earthquakes": recent_earthquakes
    })


@router.get("/watch/{watch_id}", response_class=HTMLResponse)
async def watch_detail(request: Request, watch_id: int, db: Session = Depends(get_db)):
    """Watch detail page."""
    watch = db.query(Watch).filter(Watch.id == watch_id).first()

    if not watch:
        return HTMLResponse(content="Watch not found", status_code=404)

    # Get matched reports
    results = db.query(WatchResult).filter(
        WatchResult.watch_id == watch_id
    ).all()

    matched_reports = []
    for result in results:
        report = db.query(UFOReport).filter(
            UFOReport.id == result.ufo_report_id
        ).first()
        if report:
            matched_reports.append({
                "report": report,
                "distance_km": result.distance_km,
                "time_delta_hours": result.time_delta_hours
            })

    return templates.TemplateResponse("watch_detail.html", {
        "request": request,
        "watch": watch,
        "matched_reports": matched_reports
    })
