# SPECTER TRACKER v2.0

UFO-Geology Correlation Tracker - Mapping UAP reports on piezoelectric terrain.

## Overview

SPECTER TRACKER v2.0 analyzes the correlation between UFO/UAP reports and geological features, specifically low-magnetic (piezoelectric) terrain. This is a **correlation tracker**, not a prediction system.

**Important**: The earthquake precursor hypothesis (v1.0) was NOT validated. At the M>=4.0 threshold, the signal inverted (0.62x ratio). The "8.32x elevation" claim was an artifact of using too-low magnitude thresholds. Only the **magnetic-geology correlation** (rho=-0.497) survives rigorous statistical testing.

## What's Validated

- **Magnetic Anomaly Correlation** (rho=-0.497, p<0.0001, survives Bonferroni)
  - Low magnetic signature correlates with UFO report clusters
  - This is the most robust finding

- **Shape-Geology Association** (p=0.002)
  - Orb/light/sphere shapes cluster in low-magnetic zones
  - Consistent with piezoelectric plasma hypothesis

## What's NOT Validated

- **Earthquake Precursor Hypothesis** - FAILED at M>=4.0 threshold
- **72-hour watch window** - Not statistically supported
- **8.32x elevation claim** - Artifact of methodology, not evidence

## Features

- **Geology Map**: Interactive map showing reports colored by magnetic zone
- **SPECTER Score**: 0-75 score based on:
  - Magnetic signature (0-30 points) - low = piezoelectric zone
  - Shape classification (0-20 points) - orbs/lights score higher
  - Physical effects keywords (0-25 points) - earthquake, static, etc.
  - ~~Seismic proximity~~ - **DISABLED in v2.0**
- **Correlation Dashboard**: Running statistics on low-mag vs high-mag zones
- **NUFORC Integration**: Scrapes UFO reports from NUFORC
- **USGS Data**: Earthquake overlay for geographic context (NOT prediction)

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

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard |
| `GET /map` | Geology map |
| `GET /api/health` | Health check |
| `GET /api/earthquakes` | Recent earthquakes (context only) |
| `GET /api/earthquakes/live` | Live USGS feed |
| `GET /api/reports` | UFO reports |
| `GET /api/reports/by-geology` | Reports filtered by magnetic zone |
| `GET /api/reports/high-score` | High-scoring reports |
| `GET /api/correlation` | Geology correlation statistics |
| `GET /api/hotspots` | Cached hotspot analysis |
| `GET /api/stats` | System statistics |
| `POST /api/score` | Score a location |
| `GET /api/magnetic` | Get magnetic anomaly at location |

## Scoring (v2.0)

```
SPECTER Score (0-75 max):
├── Magnetic Signature (0-30)
│   ├── < 50 nT:  30 points (piezoelectric zone)
│   ├── 50-100:   20 points
│   ├── 100-200:  10 points
│   └── > 200:    0 points
├── Shape Classification (0-20)
│   ├── orb/sphere/light: 20 points
│   ├── fireball/flash:   18 points
│   ├── oval/egg:         14 points
│   └── triangle/cigar:   0 points
└── Physical Effects (0-25)
    └── +5 per keyword (earthquake, static, compass, etc.)
```

**Note**: Seismic proximity scoring is **disabled** in v2.0. The earthquake precursor hypothesis was not validated.

## Methodological Review

See `METHODOLOGICAL_REVIEW.md` for the full honest assessment of the SPECTER research, including:
- Why the 8.32x claim doesn't hold at M>=4.0
- What statistical tests survive Bonferroni correction
- The difference between correlation and causation

## File Structure

```
specter-watch/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Railway deployment
├── METHODOLOGICAL_REVIEW.md  # Honest assessment
├── app/
│   ├── models/
│   │   ├── database.py  # SQLAlchemy setup
│   │   └── schemas.py   # Database models
│   ├── services/
│   │   ├── magnetic_grid.py   # Grid interpolator
│   │   ├── scoring.py         # SPECTER scoring (v2.0)
│   │   ├── nuforc_scraper.py  # NUFORC web scraper
│   │   └── usgs_client.py     # USGS API client
│   ├── routers/
│   │   ├── api.py       # REST API routes
│   │   └── dashboard.py # HTML dashboard routes
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       └── map.html
└── README.md
```

## License

Research project - MIT License
