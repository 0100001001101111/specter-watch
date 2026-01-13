"""NUFORC (National UFO Reporting Center) web scraper."""
import re
import hashlib
from datetime import datetime
from typing import Optional
import httpx
from bs4 import BeautifulSoup


class NUFORCScraper:
    """Scrape recent UFO reports from NUFORC website."""

    BASE_URL = "https://nuforc.org"
    REPORTS_URL = f"{BASE_URL}/webreports/ndxevent.html"

    # US state abbreviations to full names for geocoding
    US_STATES = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
    }

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'SPECTER-WATCH/1.0 (Research Project)'
            }
        )

    def get_recent_dates(self, limit: int = 30) -> list:
        """Get list of recent report dates from index page.

        Returns:
            List of date URLs (e.g., ['ndxe202401.html', 'ndxe202312.html', ...])
        """
        try:
            response = self.client.get(self.REPORTS_URL)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching NUFORC index: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        # Find monthly index pages
        date_links = []
        for link in links:
            href = link['href']
            if 'ndxe' in href and href.endswith('.html'):
                date_links.append(href)

        return date_links[:limit]

    def scrape_month(self, month_url: str) -> list:
        """Scrape all reports from a monthly index page.

        Args:
            month_url: URL path like 'ndxe202401.html'

        Returns:
            List of report dictionaries
        """
        full_url = f"{self.BASE_URL}/webreports/{month_url}"

        try:
            response = self.client.get(full_url)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching month {month_url}: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        reports = []

        # Find the table with reports
        table = soup.find('table')
        if not table:
            return []

        rows = table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            try:
                report = self._parse_row(cols)
                if report:
                    reports.append(report)
            except Exception as e:
                continue

        return reports

    def _parse_row(self, cols) -> Optional[dict]:
        """Parse a table row into a report dictionary."""
        # Column structure: Date/Time, City, State, Country, Shape, Duration, Summary

        # Get detail link for full report
        link = cols[0].find('a')
        detail_url = link['href'] if link else None

        # Parse date/time
        date_str = cols[0].get_text(strip=True)
        report_datetime = self._parse_datetime(date_str)

        # Location
        city = cols[1].get_text(strip=True) if len(cols) > 1 else ''
        state = cols[2].get_text(strip=True) if len(cols) > 2 else ''
        country = cols[3].get_text(strip=True) if len(cols) > 3 else 'USA'

        # Shape
        shape = cols[4].get_text(strip=True) if len(cols) > 4 else ''

        # Duration
        duration_text = cols[5].get_text(strip=True) if len(cols) > 5 else ''
        duration_seconds = self._parse_duration(duration_text)

        # Summary/Description
        summary = cols[6].get_text(strip=True) if len(cols) > 6 else ''

        # Generate unique ID
        nuforc_id = self._generate_id(date_str, city, state)

        return {
            'nuforc_id': nuforc_id,
            'datetime': report_datetime,
            'city': city,
            'state': state,
            'country': country if country else 'USA',
            'shape': shape,
            'duration_seconds': duration_seconds,
            'duration_text': duration_text,
            'description': summary,
            'detail_url': detail_url
        }

    def get_report_detail(self, detail_url: str) -> Optional[str]:
        """Fetch full description from report detail page."""
        full_url = f"{self.BASE_URL}/webreports/{detail_url}"

        try:
            response = self.client.get(full_url)
            response.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the report text
        for font in soup.find_all('font'):
            text = font.get_text(strip=True)
            if len(text) > 100:  # Likely the description
                return text

        return None

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse NUFORC date format."""
        formats = [
            '%m/%d/%y %H:%M',
            '%m/%d/%Y %H:%M',
            '%Y-%m-%d %H:%M',
            '%m/%d/%y',
            '%m/%d/%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_duration(self, duration_text: str) -> Optional[int]:
        """Parse duration text to seconds."""
        if not duration_text:
            return None

        text = duration_text.lower()
        total_seconds = 0

        # Hours
        match = re.search(r'(\d+)\s*hour', text)
        if match:
            total_seconds += int(match.group(1)) * 3600

        # Minutes
        match = re.search(r'(\d+)\s*min', text)
        if match:
            total_seconds += int(match.group(1)) * 60

        # Seconds
        match = re.search(r'(\d+)\s*sec', text)
        if match:
            total_seconds += int(match.group(1))

        return total_seconds if total_seconds > 0 else None

    def _generate_id(self, date_str: str, city: str, state: str) -> str:
        """Generate unique ID for a report."""
        unique_str = f"{date_str}_{city}_{state}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
