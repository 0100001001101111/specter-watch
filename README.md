# SPECTER WATCH

Real-time UFO-Earthquake Correlation Tracker based on the SPECTER piezoelectric hypothesis.

## Overview

SPECTER WATCH monitors earthquakes in real-time and creates "watch zones" around them. When UFO reports appear within 150km and 72 hours of an earthquake in piezoelectric geology, it tracks the correlation.

## Features

- **Live Earthquake Monitoring**: Fetches M3.0+ earthquakes from USGS every 15 minutes
- **NUFORC Scraping**: Scrapes recent UFO reports from NUFORC hourly
- **SPECTER Scoring**: 0-100 score based on:
  - Magnetic signature (low = piezoelectric zone)
  - Shape classification (orbs/lights = higher score)
  - Physical effects keywords (earthquake, static, etc.)
  - Seismic proximity (distance and time to recent earthquakes)
- **Watch System**: Creates 72-hour, 150km radius watch zones for M3.0+ earthquakes
- **Dashboard**: Dark-themed real-time dashboard with map visualization

## Tech Stack

- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM (SQLite locally, PostgreSQL in production)
- **Celery + Redis**: Background task processing
- **Jinja2**: HTML templates
- **Leaflet.js**: Interactive maps

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py

# Or with uvicorn
uvicorn main:app --reload

# Open http://localhost:8000
```

## Railway Deployment

1. Create a new Railway project
2. Add a Redis service
3. Add a PostgreSQL service (optional, SQLite works for hobby tier)
4. Deploy this repository
5. Set environment variables:
   - `REDIS_URL` (auto-set by Railway)
   - `DATABASE_URL` (auto-set by Railway if using PostgreSQL)

**Note**: The `magnetic.xyz` file (74MB USGS magnetic grid) is automatically downloaded from USGS on first startup if not present. This may take a few minutes on cold start.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard |
| `GET /map` | Interactive map |
| `GET /api/health` | Health check |
| `GET /api/earthquakes` | Recent earthquakes |
| `GET /api/earthquakes/live` | Live USGS feed |
| `GET /api/watches` | SPECTER watches |
| `GET /api/reports` | UFO reports |
| `GET /api/reports/high-score` | High-scoring reports |
| `GET /api/hotspots` | Cached hotspot analysis |
| `GET /api/stats` | System statistics |
| `POST /api/score` | Score a location |

## Based on SPECTER Research

This application implements the findings from SPECTER (Seismic Piezoelectric Effect Correlation Tracker Evidence Research):

- **SF Bay Area**: 8.32x elevation in UFO reports during seismically active periods
- **Low magnetic signature**: <50 nT correlates with piezoelectric geology
- **Franciscan/Serpentinite**: Quartz-bearing formations produce piezoelectric effects
- **Loma Prieta 1989**: Both SF reports on October 17, 1989 - the exact day of the M6.9 earthquake

## File Structure

```
specter-watch/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── magnetic.xyz         # USGS magnetic anomaly grid (65MB)
├── Procfile            # Railway process definitions
├── railway.json        # Railway configuration
├── nixpacks.toml       # Nixpacks build config
├── app/
│   ├── models/
│   │   ├── database.py  # SQLAlchemy setup
│   │   └── schemas.py   # Database models
│   ├── services/
│   │   ├── magnetic_grid.py   # Grid interpolator
│   │   ├── scoring.py         # SPECTER scoring engine
│   │   ├── nuforc_scraper.py  # NUFORC web scraper
│   │   ├── usgs_client.py     # USGS API client
│   │   └── watch_manager.py   # Watch zone management
│   ├── routers/
│   │   ├── api.py       # REST API routes
│   │   └── dashboard.py # HTML dashboard routes
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── map.html
│   │   └── watch_detail.html
│   └── tasks.py         # Celery background tasks
└── README.md
```

## License

Research project - MIT License
