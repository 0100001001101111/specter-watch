"""Background tasks for SPECTER WATCH."""
import os
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

from .models.database import SessionLocal
from .models.schemas import UFOReport, Earthquake, Watch, SystemLog
from .services.nuforc_scraper import NUFORCScraper
from .services.usgs_client import USGSClient
from .services.scoring import get_scoring_engine
from .services.watch_manager import WatchManager
from .services.magnetic_grid import get_magnetic_grid

# Redis URL from environment or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "specter_watch",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    worker_prefetch_multiplier=1,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "scrape-nuforc-hourly": {
        "task": "app.tasks.scrape_nuforc",
        "schedule": crontab(minute=0),  # Every hour
    },
    "fetch-usgs-every-15min": {
        "task": "app.tasks.fetch_usgs_earthquakes",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "check-watches-every-5min": {
        "task": "app.tasks.check_watches",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "score-pending-reports-every-30min": {
        "task": "app.tasks.score_pending_reports",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
}


def log_event(level: str, component: str, message: str, details: dict = None):
    """Log an event to the database."""
    db = SessionLocal()
    try:
        log = SystemLog(
            level=level,
            component=component,
            message=message,
            details=details
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def scrape_nuforc(self):
    """Scrape recent NUFORC reports."""
    db = SessionLocal()
    try:
        log_event("INFO", "scraper", "Starting NUFORC scrape")

        with NUFORCScraper() as scraper:
            # Get recent months
            date_links = scraper.get_recent_dates(limit=2)

            new_count = 0
            for month_url in date_links:
                reports = scraper.scrape_month(month_url)

                for report_data in reports:
                    # Check if already exists
                    existing = db.query(UFOReport).filter(
                        UFOReport.nuforc_id == report_data['nuforc_id']
                    ).first()

                    if existing:
                        continue

                    # Create new report
                    report = UFOReport(
                        nuforc_id=report_data['nuforc_id'],
                        datetime=report_data['datetime'],
                        city=report_data['city'],
                        state=report_data['state'],
                        country=report_data['country'],
                        shape=report_data['shape'],
                        duration_seconds=report_data['duration_seconds'],
                        duration_text=report_data['duration_text'],
                        description=report_data['description']
                    )
                    db.add(report)
                    new_count += 1

            db.commit()
            log_event("INFO", "scraper", f"NUFORC scrape complete: {new_count} new reports")
            return {"new_reports": new_count}

    except Exception as e:
        log_event("ERROR", "scraper", f"NUFORC scrape failed: {str(e)}")
        self.retry(countdown=60)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def fetch_usgs_earthquakes(self):
    """Fetch recent earthquakes from USGS."""
    db = SessionLocal()
    try:
        log_event("INFO", "usgs", "Fetching USGS earthquakes")

        with USGSClient() as client:
            earthquakes = client.get_recent_earthquakes(
                days=1,
                min_magnitude=3.0,
                max_results=100
            )

            new_count = 0
            watch_count = 0
            manager = WatchManager(db)

            for eq_data in earthquakes:
                # Check if already exists
                existing = db.query(Earthquake).filter(
                    Earthquake.usgs_id == eq_data['usgs_id']
                ).first()

                if existing:
                    continue

                # Create new earthquake
                eq = Earthquake(
                    usgs_id=eq_data['usgs_id'],
                    datetime=eq_data['datetime'],
                    latitude=eq_data['latitude'],
                    longitude=eq_data['longitude'],
                    depth_km=eq_data['depth_km'],
                    magnitude=eq_data['magnitude'],
                    mag_type=eq_data['mag_type'],
                    place=eq_data['place']
                )
                db.add(eq)
                new_count += 1

                # Create watch for significant earthquakes
                watch = manager.create_watch_for_earthquake(eq_data)
                if watch:
                    watch_count += 1

            db.commit()
            log_event("INFO", "usgs", f"USGS fetch complete: {new_count} new, {watch_count} watches")
            return {"new_earthquakes": new_count, "new_watches": watch_count}

    except Exception as e:
        log_event("ERROR", "usgs", f"USGS fetch failed: {str(e)}")
        self.retry(countdown=60)
    finally:
        db.close()


@celery_app.task
def check_watches():
    """Check and update watch statuses."""
    db = SessionLocal()
    try:
        manager = WatchManager(db)

        # Check for expired watches
        expired = manager.check_expired_watches()

        # Get pending reports to match
        pending_reports = db.query(UFOReport).filter(
            UFOReport.datetime >= datetime.utcnow() - timedelta(days=3),
            UFOReport.latitude.isnot(None),
            UFOReport.longitude.isnot(None)
        ).all()

        # Match reports to active watches
        results = manager.match_reports_to_watches(pending_reports)

        log_event("INFO", "watch_manager",
                  f"Watch check: {expired} expired, {len(results)} matched")
        return {"expired": expired, "matched": len(results)}

    except Exception as e:
        log_event("ERROR", "watch_manager", f"Watch check failed: {str(e)}")
    finally:
        db.close()


@celery_app.task
def score_pending_reports():
    """Score reports that haven't been scored yet."""
    db = SessionLocal()
    try:
        scorer = get_scoring_engine()

        # Get unscored reports
        pending = db.query(UFOReport).filter(
            UFOReport.scored == False,
            UFOReport.latitude.isnot(None),
            UFOReport.longitude.isnot(None)
        ).limit(100).all()

        scored_count = 0
        for report in pending:
            try:
                # Get nearby earthquakes
                with USGSClient() as client:
                    earthquakes = client.get_earthquakes_near(
                        report.latitude,
                        report.longitude,
                        radius_km=150,
                        days=7
                    )

                # Score the report
                score = scorer.score_report(
                    lat=report.latitude,
                    lon=report.longitude,
                    shape=report.shape,
                    description=report.description,
                    report_datetime=report.datetime,
                    nearby_earthquakes=earthquakes
                )

                report.specter_score = score['total']
                report.score_breakdown = score
                report.scored = True

                # Also get magnetic anomaly
                grid = get_magnetic_grid()
                report.magnetic_anomaly = grid.get_anomaly(
                    report.latitude, report.longitude
                )

                scored_count += 1

            except Exception:
                continue

        db.commit()
        log_event("INFO", "scorer", f"Scored {scored_count} reports")
        return {"scored": scored_count}

    except Exception as e:
        log_event("ERROR", "scorer", f"Scoring failed: {str(e)}")
    finally:
        db.close()


@celery_app.task
def geocode_reports():
    """Geocode reports that don't have coordinates."""
    # This would use a geocoding service like Nominatim
    # For now, skip as it requires API setup
    return {"geocoded": 0}
