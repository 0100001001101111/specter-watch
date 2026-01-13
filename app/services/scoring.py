"""SPECTER scoring engine - calculates piezoelectric probability."""
from datetime import datetime, timedelta
from typing import Optional
from .magnetic_grid import get_magnetic_grid


class ScoringEngine:
    """Calculate SPECTER scores for UFO reports."""

    # Shapes associated with piezoelectric phenomena
    PIEZO_SHAPES = {
        'orb': 1.0,
        'sphere': 1.0,
        'circle': 0.9,
        'fireball': 0.9,
        'light': 0.8,
        'flash': 0.8,
        'oval': 0.7,
        'egg': 0.7,
        'disk': 0.6,
        'changing': 0.6,
    }

    # Keywords indicating physical effects
    PHYSICAL_KEYWORDS = [
        'earthquake', 'tremor', 'shaking', 'rumbling',
        'static', 'electrical', 'tingling', 'hair standing',
        'compass', 'magnetic', 'interference', 'radio',
        'car stopped', 'engine died', 'lights flickered',
        'ground shook', 'seismic', 'quake'
    ]

    def __init__(self):
        self.magnetic_grid = get_magnetic_grid()

    def score_report(
        self,
        lat: float,
        lon: float,
        shape: str,
        description: str,
        report_datetime: datetime,
        nearby_earthquakes: list = None
    ) -> dict:
        """Calculate SPECTER score for a UFO report.

        Args:
            lat: Latitude
            lon: Longitude
            shape: Reported shape
            description: Report description text
            report_datetime: When the sighting occurred
            nearby_earthquakes: List of nearby recent earthquakes

        Returns:
            Dictionary with total score and breakdown
        """
        breakdown = {}

        # 1. MAGNETIC SIGNATURE (0-30 points)
        magnetic_score = self._score_magnetic(lat, lon)
        breakdown['magnetic'] = magnetic_score

        # 2. SHAPE CLASSIFICATION (0-20 points)
        shape_score = self._score_shape(shape)
        breakdown['shape'] = shape_score

        # 3. PHYSICAL EFFECTS (0-25 points)
        physical_score = self._score_physical_effects(description)
        breakdown['physical_effects'] = physical_score

        # 4. SEISMIC PROXIMITY (0-25 points)
        seismic_score = self._score_seismic(
            lat, lon, report_datetime, nearby_earthquakes
        )
        breakdown['seismic'] = seismic_score

        # Calculate total
        total = sum(breakdown.values())
        breakdown['total'] = total

        # Add interpretation
        if total >= 70:
            breakdown['interpretation'] = 'HIGH piezoelectric probability'
        elif total >= 40:
            breakdown['interpretation'] = 'MODERATE piezoelectric probability'
        else:
            breakdown['interpretation'] = 'LOW piezoelectric probability'

        return breakdown

    def _score_magnetic(self, lat: float, lon: float) -> float:
        """Score based on magnetic anomaly (low = good for piezo).

        Scoring:
        - < 50 nT (absolute): 30 points (ideal piezoelectric zone)
        - 50-100 nT: 20 points
        - 100-200 nT: 10 points
        - > 200 nT: 0 points (high magnetic = non-piezoelectric)
        """
        if lat is None or lon is None:
            return 0.0

        anomaly = self.magnetic_grid.get_anomaly(lat, lon)
        if anomaly is None:
            return 10.0  # Default if out of grid bounds

        abs_anomaly = abs(anomaly)

        if abs_anomaly < 50:
            return 30.0
        elif abs_anomaly < 100:
            return 20.0
        elif abs_anomaly < 200:
            return 10.0
        else:
            return 0.0

    def _score_shape(self, shape: str) -> float:
        """Score based on reported shape.

        Orbs/spheres/lights are most consistent with plasma phenomena.
        """
        if not shape:
            return 5.0  # Default for unknown

        shape_lower = shape.lower().strip()

        # Check for matches
        for piezo_shape, weight in self.PIEZO_SHAPES.items():
            if piezo_shape in shape_lower:
                return 20.0 * weight

        # Non-piezoelectric shapes
        if any(s in shape_lower for s in ['triangle', 'chevron', 'rectangle', 'cigar']):
            return 0.0

        return 5.0  # Default for unrecognized

    def _score_physical_effects(self, description: str) -> float:
        """Score based on physical effects in description.

        Keywords suggesting electromagnetic/seismic effects score higher.
        """
        if not description:
            return 0.0

        desc_lower = description.lower()
        matches = 0

        for keyword in self.PHYSICAL_KEYWORDS:
            if keyword in desc_lower:
                matches += 1

        # Cap at 25 points
        return min(matches * 5, 25.0)

    def _score_seismic(
        self,
        lat: float,
        lon: float,
        report_datetime: datetime,
        earthquakes: list = None
    ) -> float:
        """Score based on nearby recent seismic activity.

        Args:
            lat: Report latitude
            lon: Report longitude
            report_datetime: When sighting occurred
            earthquakes: List of dicts with lat, lon, datetime, magnitude

        Returns:
            Score from 0-25 based on seismic proximity
        """
        if not earthquakes or lat is None or lon is None:
            return 0.0

        max_score = 0.0

        for eq in earthquakes:
            # Calculate distance (simple approximation)
            eq_lat = eq.get('latitude') or eq.get('lat')
            eq_lon = eq.get('longitude') or eq.get('lon')
            eq_time = eq.get('datetime') or eq.get('time')
            eq_mag = eq.get('magnitude') or eq.get('mag', 0)

            if eq_lat is None or eq_lon is None:
                continue

            dist_km = self._haversine(lat, lon, eq_lat, eq_lon)

            # Time difference
            if isinstance(eq_time, str):
                eq_time = datetime.fromisoformat(eq_time.replace('Z', '+00:00'))
            if report_datetime.tzinfo is None and eq_time.tzinfo is not None:
                eq_time = eq_time.replace(tzinfo=None)

            time_diff = abs((report_datetime - eq_time).total_seconds() / 3600)  # hours

            # Score based on proximity
            # Within 72 hours and 150 km = full points
            if dist_km <= 150 and time_diff <= 72:
                # Distance factor (closer = better)
                dist_factor = max(0, 1 - (dist_km / 150))
                # Time factor (more recent = better)
                time_factor = max(0, 1 - (time_diff / 72))
                # Magnitude factor
                mag_factor = min(eq_mag / 5.0, 1.0) if eq_mag else 0.5

                score = 25.0 * dist_factor * time_factor * mag_factor
                max_score = max(max_score, score)

        return max_score

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c


# Global singleton
_scoring_engine = None


def get_scoring_engine() -> ScoringEngine:
    """Get the global scoring engine instance."""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ScoringEngine()
    return _scoring_engine
