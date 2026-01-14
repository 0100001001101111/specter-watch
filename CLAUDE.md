# UFO Pattern Analysis - Project State

## Live URL
**https://specter-watch-production.up.railway.app/**

## What This Project Shows

Primary finding: **UFO reports are 5.47x more likely within 50km of military bases** (p < 0.0001).

This is a "what we learned" site documenting:
- What survived rigorous statistical testing
- What failed testing (transparency about failures)
- Interactive map of military proximity correlation

## What Changed

The geology/earthquake precursor hypotheses (SPECTER, FERRO) **did not survive rigorous testing**:
- SPECTER earthquake precursor: FAILED at M≥4.0 threshold
- FERRO geology correlation: Did not replicate in blind test
- Physical effects cases: Keyword noise, no verified patterns

**What survived**: Military proximity (5.47x), temporal patterns (human behavior), shape evolution (cultural).

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main findings page |
| `/map` | Military proximity map with heatmap |
| `/api/military-proximity` | Stats by distance to bases |
| `/api/military-bases` | List of 32 tracked military bases |
| `/api/military-proximity/check` | Check a location's proximity |
| `/api/what-failed` | Documentation of failed hypotheses |
| `/api/docs` | Swagger API documentation |

### Deprecated (kept for historical purposes)
- `/api/correlation` - geology hypothesis failed
- `/api/magnetic` - geology hypothesis failed
- `/api/reports/by-geology` - geology hypothesis failed

## Tech Stack
- **Backend**: FastAPI + Gunicorn + Uvicorn
- **Database**: SQLite (SQLAlchemy ORM), PostgreSQL in production
- **Maps**: Leaflet.js + Leaflet.heat plugin
- **Deployment**: Railway (auto-deploys from GitHub)

## File Structure

```
specter-watch/
├── main.py                 # FastAPI application
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── Dockerfile              # Railway deployment
├── app/
│   ├── models/
│   │   ├── database.py     # SQLAlchemy setup
│   │   └── schemas.py      # Database models
│   ├── services/
│   │   ├── magnetic_grid.py    # (deprecated) USGS grid
│   │   ├── scoring.py          # (deprecated) SPECTER scoring
│   │   ├── nuforc_scraper.py   # UFO report scraper
│   │   └── usgs_client.py      # Earthquake API
│   ├── routers/
│   │   ├── api.py          # REST API routes (includes military proximity)
│   │   └── dashboard.py    # HTML dashboard routes
│   └── templates/
│       ├── base.html       # Base layout with SEO
│       ├── dashboard.html  # Main findings page
│       └── map.html        # Military proximity map
```

## Environment Variables (Railway)
- `DATABASE_URL` - Set automatically
- `REDIS_URL` - Connected to Redis service
- `PORT` - Set by Railway (8080)

## Important Notes

- This is a static "what we learned" site, not an active tracker
- The geology services are deprecated but kept for backwards compatibility
- All statistics come from the ufo-patterns analysis (74,780 US reports)
- Military base coordinates are hardcoded from the analysis
