# SPECTER WATCH - Project State

## Live URL
**https://specter-watch-production.up.railway.app/**

## What's Working
- Dashboard loads with dark theme UI
- Health endpoint (`/api/health`) responding
- Database (SQLite) initialized
- Redis connected for background tasks
- Map view at `/map`
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
├── app/
│   ├── models/          # SQLAlchemy schemas
│   ├── services/        # Business logic
│   │   ├── magnetic_grid.py   # USGS grid (lazy load)
│   │   ├── scoring.py         # SPECTER 0-100 scoring
│   │   ├── nuforc_scraper.py  # UFO report scraper
│   │   ├── usgs_client.py     # Earthquake API
│   │   └── watch_manager.py   # 72hr watch zones
│   ├── routers/         # API + dashboard routes
│   ├── templates/       # Jinja2 HTML
│   └── tasks.py         # Celery background jobs
```

## Known Issues
1. **Celery workers not running** - Need separate Railway service for worker process
2. **Magnetic grid not loaded** - 74MB file downloads lazily on first scoring request (slow first request)
3. **No data yet** - NUFORC scraper and USGS fetcher need to run to populate

## Environment Variables (Railway)
- `DATABASE_URL` - Set automatically
- `REDIS_URL` - Connected to Redis service
- `MAGNETIC_GRID_PATH` - Set to download location
- `PORT` - Set by Railway (8080)

## Key Endpoints
| Endpoint | Description |
|----------|-------------|
| `/` | Dashboard |
| `/map` | Interactive map |
| `/api/health` | Health check |
| `/api/earthquakes` | Recent earthquakes |
| `/api/earthquakes/live` | Live USGS feed |
| `/api/watches` | SPECTER watches |
| `/api/reports` | UFO reports |
| `/api/score?latitude=X&longitude=Y` | Score a location |
| `/docs` | Swagger API docs |

## Based On
SPECTER Phase 1-4 research findings:
- SF Bay 8.32x UFO-seismic correlation
- Piezoelectric geology (Franciscan/serpentinite)
- Loma Prieta 1989: Reports on exact earthquake day
