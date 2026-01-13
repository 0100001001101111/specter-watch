"""SPECTER scoring engine v2.0 - calculates piezoelectric probability.

NOTE: Earthquake precursor hypothesis was NOT validated in methodological review.
The M>=4.0 test showed inverted signal (0.62x ratio). Seismic scoring is disabled.
Only magnetic correlation (rho=-0.497) survives rigorous statistical testing.
"""
from datetime import datetime
from typing import Optional
from .magnetic_grid import get_magnetic_grid


class ScoringEngine:
    """Calculate SPECTER scores for UFO reports.

    v2.0 Changes:
    - Seismic proximity scoring DISABLED (precursor hypothesis failed validation)
    - Max score is now 75 (magnetic + shape + physical effects)
    - Focus on geology correlation only
    """

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

    # Keywords indicating physical effects (electromagnetic/tectonic)
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
        report_datetime: datetime = None,
        nearby_earthquakes: list = None  # IGNORED in v2.0
    ) -> dict:
        """Calculate SPECTER score for a UFO report.

        v2.0: Earthquake proximity is NOT scored (hypothesis failed validation).

        Args:
            lat: Latitude
            lon: Longitude
            shape: Reported shape
            description: Report description text
            report_datetime: When the sighting occurred (unused in v2.0)
            nearby_earthquakes: IGNORED - earthquake precursor not validated

        Returns:
            Dictionary with total score and breakdown (max 75)
        """
        breakdown = {}

        # 1. MAGNETIC SIGNATURE (0-30 points) - VALIDATED
        magnetic_score = self._score_magnetic(lat, lon)
        breakdown['magnetic'] = magnetic_score

        # 2. SHAPE CLASSIFICATION (0-20 points) - VALIDATED
        shape_score = self._score_shape(shape)
        breakdown['shape'] = shape_score

        # 3. PHYSICAL EFFECTS (0-25 points) - correlates with geology
        physical_score = self._score_physical_effects(description)
        breakdown['physical_effects'] = physical_score

        # 4. SEISMIC PROXIMITY - DISABLED (precursor hypothesis failed M>=4.0 test)
        # The 8.32x ratio was an artifact of low magnitude threshold (M>=1.0)
        # At M>=4.0, the ratio inverted to 0.62x
        breakdown['seismic'] = 0.0
        breakdown['seismic_note'] = 'Disabled in v2.0 (precursor hypothesis not validated)'

        # Calculate total (max 75 in v2.0)
        total = magnetic_score + shape_score + physical_score
        breakdown['total'] = total

        # Add interpretation (adjusted for 75-point max)
        if total >= 55:
            breakdown['interpretation'] = 'HIGH piezoelectric probability'
        elif total >= 35:
            breakdown['interpretation'] = 'MODERATE piezoelectric probability'
        else:
            breakdown['interpretation'] = 'LOW piezoelectric probability'

        return breakdown

    def _score_magnetic(self, lat: float, lon: float) -> float:
        """Score based on magnetic anomaly (low = good for piezo).

        This is the most robust finding (rho=-0.497, survives Bonferroni).

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
        Shape-geology association survives Bonferroni (p=0.002).
        """
        if not shape:
            return 5.0  # Default for unknown

        shape_lower = shape.lower().strip()

        # Check for matches
        for piezo_shape, weight in self.PIEZO_SHAPES.items():
            if piezo_shape in shape_lower:
                return 20.0 * weight

        # Non-piezoelectric shapes (structured craft)
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
