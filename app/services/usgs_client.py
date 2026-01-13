"""USGS Earthquake Hazards API client."""
from datetime import datetime, timedelta
from typing import Optional
import httpx


class USGSClient:
    """Fetch earthquake data from USGS API."""

    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )

    def get_recent_earthquakes(
        self,
        days: int = 7,
        min_magnitude: float = 2.5,
        max_results: int = 500
    ) -> list:
        """Get recent earthquakes.

        Args:
            days: Number of days back to search
            min_magnitude: Minimum magnitude filter
            max_results: Maximum number of results

        Returns:
            List of earthquake dictionaries
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%d'),
            'endtime': end_time.strftime('%Y-%m-%d'),
            'minmagnitude': min_magnitude,
            'limit': max_results,
            'orderby': 'time'
        }

        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching USGS data: {e}")
            return []

        return self._parse_geojson(data)

    def get_earthquakes_near(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 150,
        days: int = 7,
        min_magnitude: float = 2.5
    ) -> list:
        """Get earthquakes near a location.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in km
            days: Days back to search
            min_magnitude: Minimum magnitude

        Returns:
            List of earthquake dictionaries
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%d'),
            'endtime': end_time.strftime('%Y-%m-%d'),
            'latitude': latitude,
            'longitude': longitude,
            'maxradiuskm': radius_km,
            'minmagnitude': min_magnitude,
            'orderby': 'time'
        }

        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching USGS data: {e}")
            return []

        return self._parse_geojson(data)

    def get_significant_earthquakes(self, days: int = 30) -> list:
        """Get significant/notable earthquakes.

        Args:
            days: Days back to search

        Returns:
            List of significant earthquake dictionaries
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        # Use significant earthquakes feed
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching significant earthquakes: {e}")
            return []

        return self._parse_geojson(data)

    def _parse_geojson(self, data: dict) -> list:
        """Parse USGS GeoJSON response into list of dictionaries."""
        earthquakes = []

        features = data.get('features', [])

        for feature in features:
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates', [None, None, None])

            # Parse timestamp
            timestamp_ms = props.get('time')
            if timestamp_ms:
                eq_datetime = datetime.utcfromtimestamp(timestamp_ms / 1000)
            else:
                eq_datetime = None

            earthquake = {
                'usgs_id': feature.get('id'),
                'datetime': eq_datetime,
                'latitude': coords[1] if len(coords) > 1 else None,
                'longitude': coords[0] if len(coords) > 0 else None,
                'depth_km': coords[2] if len(coords) > 2 else None,
                'magnitude': props.get('mag'),
                'mag_type': props.get('magType'),
                'place': props.get('place'),
                'url': props.get('url'),
                'felt': props.get('felt'),
                'alert': props.get('alert'),
                'tsunami': props.get('tsunami'),
                'significance': props.get('sig')
            }

            earthquakes.append(earthquake)

        return earthquakes

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
