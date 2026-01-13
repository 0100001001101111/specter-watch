# SPECTER TRACKER v2.0 - TODO

## Completed (v2.0 Pivot)
- [x] Remove watch system (earthquake precursor not validated)
- [x] Update scoring engine (seismic scoring disabled)
- [x] Update dashboard (correlation tracker, not predictor)
- [x] Update map (geology-based coloring, filters)
- [x] Update API routes (remove watches, add geology endpoints)
- [x] Update documentation (honest about what's validated)

## High Priority
- [ ] Trigger initial NUFORC scrape to populate UFO reports
- [ ] Trigger initial USGS fetch to populate earthquakes (context only)
- [ ] Add Celery worker service in Railway (separate process)

## Medium Priority
- [ ] Add geocoding for UFO reports (city/state -> lat/lon)
- [ ] Pre-download magnetic grid or cache it in Railway volume
- [ ] Add PostgreSQL for production (currently SQLite)
- [ ] Historical data import from SPECTER Phase 1-4 datasets

## Low Priority
- [ ] Dashboard auto-refresh with WebSockets
- [ ] Add authentication for admin endpoints
- [ ] Export correlation data to CSV/JSON

## Research Follow-up
- [ ] Re-analyze with larger M>=4.0 earthquake dataset
- [ ] Geographic replication study (non-California data)
- [ ] Temporal holdout validation (post-2015 data)

## Deprecated (v1.0 features - removed)
- ~~Watch system (72hr prediction windows)~~
- ~~Seismic proximity scoring~~
- ~~Watch notifications~~
