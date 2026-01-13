# SPECTER TRACKER v2.0 - Project State

## Live URL
**https://specter-watch-production.up.railway.app/**

## What Changed in v2.0

The earthquake precursor hypothesis was **NOT validated** in methodological review:
- At M>=4.0 threshold, signal inverted (0.62x ratio instead of 8.32x)
- The "8.32x elevation" was an artifact of using M>=1.0 threshold
- Watch system (72-hour prediction windows) has been **removed**

**What survives**: Magnetic-geology correlation (rho=-0.497, p<0.0001)

## What's Working
- Dashboard loads with dark theme UI (correlation tracker)
- Health endpoint (`/api/health`) responding
- Database (SQLite) initialized
- Redis connected for background tasks
- Geology map at `/map` with filter controls
- API documentation at `/docs`

## Tech Stack
- **Backend**: FastAPI + Gunicorn + Uvicorn
- **Database**: SQLite (SQLAlchemy ORM)
- **Background Tasks**: Celery + Redis
- **Templates**: Jinja2 + Leaflet.js for maps
- **Deployment**: Railway (Hobby tier)
- **Repo**: https://github.com/0100001001101111/specter-watch

## Architecture
```
specter-watch/
├── main.py              # FastAPI app entry
├── Dockerfile           # Railway deployment
├── METHODOLOGICAL_REVIEW.md  # Honest research assessment
├── app/
│   ├── models/          # SQLAlchemy schemas
│   ├── services/        # Business logic
│   │   ├── magnetic_grid.py   # USGS grid (lazy load)
│   │   ├── scoring.py         # SPECTER 0-75 scoring (v2.0)
│   │   ├── nuforc_scraper.py  # UFO report scraper
│   │   └── usgs_client.py     # Earthquake API
│   ├── routers/         # API + dashboard routes
│   └── templates/       # Jinja2 HTML
```

## Key Changes from v1.0
| Feature | v1.0 | v2.0 |
|---------|------|------|
| Watch system | 72hr prediction | **Removed** |
| Seismic scoring | 0-25 points | **Disabled** |
| Max score | 100 | 75 |
| Purpose | Earthquake predictor | Correlation tracker |

## Environment Variables (Railway)
- `DATABASE_URL` - Set automatically
- `REDIS_URL` - Connected to Redis service
- `MAGNETIC_GRID_PATH` - Set to download location
- `PORT` - Set by Railway (8080)

## Key Endpoints
| Endpoint | Description |
|----------|-------------|
| `/` | Dashboard (correlation tracker) |
| `/map` | Geology map with filters |
| `/api/health` | Health check |
| `/api/earthquakes` | Recent earthquakes (context only) |
| `/api/reports` | UFO reports |
| `/api/reports/by-geology` | Filter by magnetic zone |
| `/api/correlation` | Geology correlation stats |
| `/api/score?latitude=X&longitude=Y` | Score a location |
| `/docs` | Swagger API docs |

## Based On
SPECTER Phase 1-4 research findings:
- **Validated**: Magnetic-UFO correlation (rho=-0.497)
- **Validated**: Shape-geology association (orbs cluster in low-mag zones)
- **NOT Validated**: Earthquake precursor hypothesis
- **NOT Validated**: 8.32x elevation (artifact of M>=1.0 threshold)
