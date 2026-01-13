# SPECTER WATCH - TODO

## High Priority
- [ ] Add Celery worker service in Railway (separate process for background tasks)
- [ ] Trigger initial NUFORC scrape to populate UFO reports
- [ ] Trigger initial USGS fetch to populate earthquakes and create watches

## Medium Priority
- [ ] Add geocoding for UFO reports (city/state → lat/lon)
- [ ] Pre-download magnetic grid or cache it in Railway volume
- [ ] Add PostgreSQL for production (currently SQLite)

## Low Priority
- [ ] Add email/webhook notifications for triggered watches
- [ ] Historical data import from SPECTER Phase 1-4 datasets
- [ ] Add authentication for admin endpoints
- [ ] Dashboard auto-refresh with WebSockets

## Completed
- [x] FastAPI backend with SQLAlchemy
- [x] NUFORC scraper implementation
- [x] USGS API client
- [x] SPECTER scoring engine (magnetic, shape, physical effects, seismic)
- [x] Watch system (72hr, 150km radius, M3.0+)
- [x] Dashboard with Leaflet.js map
- [x] Railway deployment
- [x] Redis service connected
- [x] Auto-download magnetic grid from USGS
