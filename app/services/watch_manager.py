"""Watch management - create and monitor SPECTER watches."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from ..models.schemas import Watch, WatchResult, Earthquake, UFOReport
from .magnetic_grid import get_magnetic_grid


class WatchManager:
    """Manage SPECTER watch predictions."""

    WATCH_DURATION_HOURS = 72
    WATCH_RADIUS_KM = 150
    MIN_MAGNITUDE = 3.0

    def __init__(self, db: Session):
        self.db = db
        self.magnetic_grid = get_magnetic_grid()

    def create_watch_for_earthquake(self, earthquake: dict) -> Optional[Watch]:
        """Create a new watch for an earthquake.

        Args:
            earthquake: Earthquake dict with lat, lon, magnitude, datetime, etc.

        Returns:
            Created Watch object or None if not eligible
        """
        # Check minimum magnitude
        magnitude = earthquake.get('magnitude', 0)
        if magnitude < self.MIN_MAGNITUDE:
            return None

        # Check if watch already exists
        usgs_id = earthquake.get('usgs_id')
        if usgs_id:
            existing = self.db.query(Earthquake).filter(
                Earthquake.usgs_id == usgs_id
            ).first()
            if existing:
                existing_watch = self.db.query(Watch).filter(
                    Watch.earthquake_id == existing.id
                ).first()
                if existing_watch:
                    return existing_watch

        # Get earthquake datetime
        eq_datetime = earthquake.get('datetime')
        if isinstance(eq_datetime, str):
            eq_datetime = datetime.fromisoformat(eq_datetime.replace('Z', '+00:00'))

        # Don't create watches for old earthquakes
        if eq_datetime and (datetime.utcnow() - eq_datetime.replace(tzinfo=None)) > timedelta(hours=self.WATCH_DURATION_HOURS):
            return None

        # Get magnetic anomaly at epicenter
        lat = earthquake.get('latitude')
        lon = earthquake.get('longitude')
        magnetic_anomaly = None
        piezo_probability = 0.5  # Default

        if lat and lon:
            magnetic_anomaly = self.magnetic_grid.get_anomaly(lat, lon)
            if magnetic_anomaly is not None:
                # Calculate piezo probability based on magnetic signature
                abs_mag = abs(magnetic_anomaly)
                if abs_mag < 50:
                    piezo_probability = 0.9
                elif abs_mag < 100:
                    piezo_probability = 0.7
                elif abs_mag < 200:
                    piezo_probability = 0.4
                else:
                    piezo_probability = 0.2

        # Create or get earthquake record
        eq_record = None
        if usgs_id:
            eq_record = self.db.query(Earthquake).filter(
                Earthquake.usgs_id == usgs_id
            ).first()

        if not eq_record:
            eq_record = Earthquake(
                usgs_id=usgs_id or f"manual_{datetime.utcnow().timestamp()}",
                datetime=eq_datetime,
                latitude=lat,
                longitude=lon,
                depth_km=earthquake.get('depth_km'),
                magnitude=magnitude,
                mag_type=earthquake.get('mag_type'),
                place=earthquake.get('place')
            )
            self.db.add(eq_record)
            self.db.flush()

        # Create watch
        watch = Watch(
            earthquake_id=eq_record.id,
            eq_datetime=eq_datetime,
            eq_latitude=lat,
            eq_longitude=lon,
            eq_magnitude=magnitude,
            eq_place=earthquake.get('place'),
            watch_radius_km=self.WATCH_RADIUS_KM,
            watch_start=eq_datetime,
            watch_end=eq_datetime + timedelta(hours=self.WATCH_DURATION_HOURS) if eq_datetime else None,
            magnetic_anomaly=magnetic_anomaly,
            piezo_probability=piezo_probability,
            status='active'
        )

        self.db.add(watch)
        self.db.commit()

        return watch

    def check_expired_watches(self) -> int:
        """Mark expired watches and return count."""
        now = datetime.utcnow()

        expired = self.db.query(Watch).filter(
            Watch.status == 'active',
            Watch.watch_end < now
        ).all()

        for watch in expired:
            watch.status = 'expired'

        self.db.commit()
        return len(expired)

    def match_reports_to_watches(self, reports: list) -> list:
        """Match new UFO reports to active watches.

        Args:
            reports: List of UFOReport objects

        Returns:
            List of created WatchResult objects
        """
        active_watches = self.db.query(Watch).filter(
            Watch.status == 'active'
        ).all()

        results = []

        for report in reports:
            if report.latitude is None or report.longitude is None:
                continue

            for watch in active_watches:
                if watch.eq_latitude is None or watch.eq_longitude is None:
                    continue

                # Check distance
                distance = self._haversine(
                    report.latitude, report.longitude,
                    watch.eq_latitude, watch.eq_longitude
                )

                if distance > watch.watch_radius_km:
                    continue

                # Check time window
                if report.datetime is None or watch.watch_start is None:
                    continue

                report_dt = report.datetime
                if report_dt.tzinfo:
                    report_dt = report_dt.replace(tzinfo=None)

                watch_start = watch.watch_start
                if watch_start.tzinfo:
                    watch_start = watch_start.replace(tzinfo=None)

                watch_end = watch.watch_end
                if watch_end and watch_end.tzinfo:
                    watch_end = watch_end.replace(tzinfo=None)

                if not (watch_start <= report_dt <= (watch_end or datetime.utcnow())):
                    continue

                # Create match result
                time_delta = (report_dt - watch_start).total_seconds() / 3600

                result = WatchResult(
                    watch_id=watch.id,
                    ufo_report_id=report.id,
                    distance_km=distance,
                    time_delta_hours=time_delta
                )

                self.db.add(result)
                results.append(result)

                # Mark watch as triggered
                watch.status = 'triggered'

        self.db.commit()
        return results

    def get_active_watches(self) -> list:
        """Get all active watches."""
        return self.db.query(Watch).filter(
            Watch.status == 'active'
        ).order_by(Watch.eq_datetime.desc()).all()

    def get_triggered_watches(self, limit: int = 20) -> list:
        """Get recently triggered watches."""
        return self.db.query(Watch).filter(
            Watch.status == 'triggered'
        ).order_by(Watch.eq_datetime.desc()).limit(limit).all()

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two points."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c
