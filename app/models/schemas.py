"""SQLAlchemy models for SPECTER WATCH."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, Boolean, JSON
from .database import Base


class UFOReport(Base):
    """UFO sighting report from NUFORC."""
    __tablename__ = "ufo_reports"

    id = Column(Integer, primary_key=True, index=True)
    nuforc_id = Column(String(50), unique=True, index=True)
    datetime = Column(DateTime, index=True)
    city = Column(String(100))
    state = Column(String(50))
    country = Column(String(50), default="USA")
    shape = Column(String(50))
    duration_seconds = Column(Integer)
    duration_text = Column(String(100))
    description = Column(Text)

    # Computed fields
    latitude = Column(Float)
    longitude = Column(Float)
    magnetic_anomaly = Column(Float)  # nT from grid
    specter_score = Column(Float)  # 0-100
    score_breakdown = Column(JSON)  # Detailed scoring

    # Processing metadata
    date_scraped = Column(DateTime, default=datetime.utcnow)
    geocoded = Column(Boolean, default=False)
    scored = Column(Boolean, default=False)


class Earthquake(Base):
    """Earthquake event from USGS."""
    __tablename__ = "earthquakes"

    id = Column(Integer, primary_key=True, index=True)
    usgs_id = Column(String(50), unique=True, index=True)
    datetime = Column(DateTime, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    depth_km = Column(Float)
    magnitude = Column(Float, index=True)
    mag_type = Column(String(10))
    place = Column(String(200))

    # Processing metadata
    date_fetched = Column(DateTime, default=datetime.utcnow)


class Watch(Base):
    """Active SPECTER watch prediction."""
    __tablename__ = "watches"

    id = Column(Integer, primary_key=True, index=True)
    earthquake_id = Column(Integer, index=True)  # FK to earthquakes

    # Earthquake details (denormalized for speed)
    eq_datetime = Column(DateTime)
    eq_latitude = Column(Float)
    eq_longitude = Column(Float)
    eq_magnitude = Column(Float)
    eq_place = Column(String(200))

    # Watch parameters
    watch_radius_km = Column(Float, default=150.0)
    watch_start = Column(DateTime)
    watch_end = Column(DateTime)  # 72 hours after earthquake

    # Magnetic context
    magnetic_anomaly = Column(Float)
    piezo_probability = Column(Float)  # 0-1 based on geology

    # Status
    status = Column(String(20), default="active")  # active, expired, triggered
    created_at = Column(DateTime, default=datetime.utcnow)


class WatchResult(Base):
    """UFO reports that occurred during a watch window."""
    __tablename__ = "watch_results"

    id = Column(Integer, primary_key=True, index=True)
    watch_id = Column(Integer, index=True)  # FK to watches
    ufo_report_id = Column(Integer, index=True)  # FK to ufo_reports

    distance_km = Column(Float)  # Distance from earthquake epicenter
    time_delta_hours = Column(Float)  # Hours after earthquake

    created_at = Column(DateTime, default=datetime.utcnow)


class HotspotCache(Base):
    """Cached hotspot analysis for dashboard."""
    __tablename__ = "hotspot_cache"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100))
    state = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)

    report_count = Column(Integer)
    avg_specter_score = Column(Float)
    magnetic_anomaly = Column(Float)
    seismic_ratio = Column(Float)

    last_updated = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    """System activity log."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR
    component = Column(String(50))  # scraper, usgs, scorer, etc.
    message = Column(Text)
    details = Column(JSON)
