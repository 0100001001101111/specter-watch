# UFO Pattern Analysis: What the Data Actually Shows

Statistical analysis of 74,780 UFO reports reveals what survives rigorous testing - and what doesn't.

**Live Site**: https://specter-watch-production.up.railway.app/

## Primary Finding

**UFO reports are 5.47x more likely within 50km of military bases** (p < 0.0001, Mann-Whitney U test, survives Bonferroni correction).

| Distance | UFO Reports | Random Baseline | Ratio |
|----------|-------------|-----------------|-------|
| Within 50km | 10.5% | 1.9% | **5.47x** |
| Within 100km | 25.2% | 6.6% | **3.81x** |
| Within 150km | 35.1% | 13.8% | **2.54x** |

**Most parsimonious interpretation**: People see military aircraft and misidentify them as UFOs, especially near test ranges where experimental aircraft fly.

## What Survived Testing

| Pattern | Effect | p-value | Survives Correction |
|---------|--------|---------|---------------------|
| Military proximity | 5.47x within 50km | <0.0001 | **YES** |
| Time of day | 61.8% evening | <0.0001 | YES (human behavior) |
| Month | 32.4% summer | <0.0001 | YES (human behavior) |
| Shape evolution | Disc 30%→7%, Triangle 3%→10% | <0.0001 | YES (cultural) |

## What Failed Testing

| Hypothesis | Claim | Result |
|------------|-------|--------|
| **SPECTER** | UFOs as earthquake precursors | FAILED at M≥4.0 (inverted to 0.62x) |
| **FERRO** | UFOs in iron-rich geology | Did not replicate in blind test |
| **Physical Effects** | Physical evidence validates reports | Keyword noise, no verified patterns |
| **Abduction Evidence** | Verifiable physical evidence | None confirmed |

**Transparency about failures is how science works.**

## Features

- **Interactive Map**: Military bases + UFO density heatmap with proximity filtering
- **API**: `/api/military-proximity` endpoint for programmatic access
- **What Failed Section**: Full documentation of failed hypotheses
- **Methodology**: Open source analysis code

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main findings page |
| `GET /map` | Military proximity map |
| `GET /api/military-proximity` | Stats by distance to bases |
| `GET /api/military-bases` | List of tracked bases |
| `GET /api/military-proximity/check` | Check location proximity |
| `GET /api/what-failed` | Failed hypotheses documentation |
| `GET /api/docs` | Swagger API documentation |

### Deprecated Endpoints (kept for historical purposes)

| Endpoint | Note |
|----------|------|
| `GET /api/correlation` | Geology hypothesis did not replicate |
| `GET /api/magnetic` | Geology hypothesis did not replicate |
| `GET /api/reports/by-geology` | Geology hypothesis did not replicate |

## Local Development

```bash
pip install -r requirements.txt
python main.py
# Open http://localhost:8000
```

## Data Sources

- **UFO Reports**: Obiwan Database (74,780 US reports, 1906-2014)
- **Military Bases**: 32 major US installations (AFB, NAS, test ranges)
- **Random Baseline**: 10,000 Monte Carlo points within continental US

## Tech Stack

- **Backend**: FastAPI + Gunicorn + Uvicorn
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Maps**: Leaflet.js + Leaflet.heat
- **Deployment**: Railway

## Methodology Note

This is an **exploratory analysis**, not pre-registered research. All findings should be treated as hypothesis-generating, not hypothesis-confirming. The military proximity pattern is robust to multiple testing correction, but the interpretation (misidentification of aircraft) is inference, not proof.

## What This Analysis Does NOT Show

- Whether any UFO reports are genuinely unexplained
- What fraction are "real" vs misidentification
- Whether military proximity indicates something other than aircraft

## License

MIT License - Research project

---

*This site documents what we learned, not what we hoped to find.*
