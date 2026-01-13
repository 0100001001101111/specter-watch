"""Magnetic anomaly grid loader and interpolator."""
import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from functools import lru_cache


class MagneticGrid:
    """Load and query USGS magnetic anomaly grid."""

    def __init__(self, grid_path: str = None):
        self.grid_path = grid_path or os.getenv(
            "MAGNETIC_GRID_PATH",
            os.path.join(os.path.dirname(__file__), "..", "..", "magnetic.xyz")
        )
        self._interpolator = None
        self._loaded = False

    def load(self):
        """Load the magnetic grid into memory."""
        if self._loaded:
            return

        if not os.path.exists(self.grid_path):
            print(f"Warning: Magnetic grid not found at {self.grid_path}")
            self._loaded = True
            return

        print(f"Loading magnetic grid from {self.grid_path}...")

        # Load XYZ format: lon, lat, magnetic_anomaly
        data = np.loadtxt(self.grid_path, skiprows=0)

        lons = np.unique(data[:, 0])
        lats = np.unique(data[:, 1])

        # Reshape to grid
        n_lon = len(lons)
        n_lat = len(lats)

        # Create 2D grid
        values = data[:, 2].reshape((n_lat, n_lon))

        # Create interpolator
        self._interpolator = RegularGridInterpolator(
            (lats, lons),
            values,
            method='linear',
            bounds_error=False,
            fill_value=np.nan
        )

        self._loaded = True
        print(f"Magnetic grid loaded: {n_lat}x{n_lon} points")
        print(f"  Lat range: {lats.min():.2f} to {lats.max():.2f}")
        print(f"  Lon range: {lons.min():.2f} to {lons.max():.2f}")

    def get_anomaly(self, lat: float, lon: float) -> float:
        """Get magnetic anomaly at a location.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Magnetic anomaly in nT, or None if out of bounds
        """
        if not self._loaded:
            self.load()

        if self._interpolator is None:
            return None

        try:
            value = float(self._interpolator((lat, lon)))
            if np.isnan(value):
                return None
            return value
        except Exception:
            return None

    def get_anomalies_batch(self, coords: list) -> list:
        """Get magnetic anomalies for multiple locations.

        Args:
            coords: List of (lat, lon) tuples

        Returns:
            List of magnetic anomalies (or None for out-of-bounds)
        """
        return [self.get_anomaly(lat, lon) for lat, lon in coords]


# Global singleton
_magnetic_grid = None


def get_magnetic_grid() -> MagneticGrid:
    """Get the global magnetic grid instance."""
    global _magnetic_grid
    if _magnetic_grid is None:
        _magnetic_grid = MagneticGrid()
    return _magnetic_grid
