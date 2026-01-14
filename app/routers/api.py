"""API routes for UFO Pattern Analysis - Military Proximity Focus."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

from ..models.database import get_db
from ..models.schemas import UFOReport, Earthquake, HotspotCache
from ..services.usgs_client import USGSClient
from ..services.scoring import get_scoring_engine
from ..services.magnetic_grid import get_magnetic_grid

router = APIRouter(prefix="/api", tags=["api"])

# Military bases from ufo-patterns analysis
MILITARY_BASES = [
    # Air Force Bases
    {'name': 'Edwards AFB', 'lat': 34.905, 'lon': -117.884, 'type': 'test'},
    {'name': 'Nellis AFB', 'lat': 36.236, 'lon': -115.034, 'type': 'test'},
    {'name': 'White Sands', 'lat': 32.384, 'lon': -106.479, 'type': 'test'},
    {'name': 'Area 51/Groom Lake', 'lat': 37.235, 'lon': -115.811, 'type': 'test'},
    {'name': 'Wright-Patterson AFB', 'lat': 39.826, 'lon': -84.048, 'type': 'air_force'},
    {'name': 'Vandenberg AFB', 'lat': 34.733, 'lon': -120.568, 'type': 'space'},
    {'name': 'Patrick AFB', 'lat': 28.235, 'lon': -80.610, 'type': 'space'},
    {'name': 'Eglin AFB', 'lat': 30.483, 'lon': -86.525, 'type': 'test'},
    {'name': 'Luke AFB', 'lat': 33.535, 'lon': -112.383, 'type': 'air_force'},
    {'name': 'Davis-Monthan AFB', 'lat': 32.167, 'lon': -110.883, 'type': 'air_force'},
    {'name': 'Tinker AFB', 'lat': 35.415, 'lon': -97.387, 'type': 'air_force'},
    {'name': 'Hill AFB', 'lat': 41.124, 'lon': -111.973, 'type': 'air_force'},
    {'name': 'Travis AFB', 'lat': 38.263, 'lon': -121.927, 'type': 'air_force'},
    {'name': 'Langley AFB', 'lat': 37.083, 'lon': -76.361, 'type': 'air_force'},
    {'name': 'McChord AFB', 'lat': 47.138, 'lon': -122.476, 'type': 'air_force'},
    {'name': 'Holloman AFB', 'lat': 32.852, 'lon': -106.107, 'type': 'test'},
    {'name': 'Kirtland AFB', 'lat': 35.040, 'lon': -106.609, 'type': 'air_force'},
    {'name': 'Offutt AFB', 'lat': 41.118, 'lon': -95.913, 'type': 'air_force'},
    {'name': 'Barksdale AFB', 'lat': 32.501, 'lon': -93.663, 'type': 'air_force'},
    {'name': 'Malmstrom AFB', 'lat': 47.507, 'lon': -111.183, 'type': 'nuclear'},
    # Naval Air Stations
    {'name': 'NAS Patuxent River', 'lat': 38.286, 'lon': -76.411, 'type': 'naval_test'},
    {'name': 'NAS Oceana', 'lat': 36.821, 'lon': -76.033, 'type': 'naval'},
    {'name': 'NAS Lemoore', 'lat': 36.333, 'lon': -119.952, 'type': 'naval'},
    {'name': 'NAS Jacksonville', 'lat': 30.236, 'lon': -81.681, 'type': 'naval'},
    {'name': 'NAS North Island', 'lat': 32.699, 'lon': -117.199, 'type': 'naval'},
    {'name': 'NAS Whidbey Island', 'lat': 48.352, 'lon': -122.656, 'type': 'naval'},
    {'name': 'China Lake NAWC', 'lat': 35.686, 'lon': -117.692, 'type': 'naval_test'},
    {'name': 'Point Mugu NAS', 'lat': 34.120, 'lon': -119.121, 'type': 'naval_test'},
    # Major Army
    {'name': 'Fort Bragg', 'lat': 35.139, 'lon': -78.998, 'type': 'army'},
    {'name': 'Fort Hood', 'lat': 31.138, 'lon': -97.776, 'type': 'army'},
    {'name': 'Fort Campbell', 'lat': 36.668, 'lon': -87.474, 'type': 'army'},
    {'name': 'Fort Carson', 'lat': 38.738, 'lon': -104.789, 'type': 'army'},
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def get_nearest_base(lat: float, lon: float) -> dict:
    """Find the nearest military base to a location."""
    min_dist = float('inf')
    nearest = None
    for base in MILITARY_BASES:
        dist = haversine_km(lat, lon, base['lat'], base['lon'])
        if dist < min_dist:
            min_dist = dist
            nearest = base
    return {'distance_km': min_dist, 'base': nearest}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "SPECTER TRACKER",
        "version": "2.0.0",
        "description": "UFO-Geology Correlation Tracker"
    }


@router.get("/earthquakes")
async def get_earthquakes(
    days: int = Query(7, ge=1, le=30),
    min_magnitude: float = Query(3.0, ge=0, le=10),
    db: Session = Depends(get_db)
):
    """Get recent earthquakes (overlay data, not predictions)."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    earthquakes = db.query(Earthquake).filter(
        Earthquake.datetime >= cutoff,
        Earthquake.magnitude >= min_magnitude
    ).order_by(Earthquake.datetime.desc()).limit(100).all()

    return {
        "count": len(earthquakes),
        "note": "Earthquake overlay for context - no prediction implied",
        "earthquakes": [
            {
                "id": eq.id,
                "usgs_id": eq.usgs_id,
                "datetime": eq.datetime.isoformat() if eq.datetime else None,
                "latitude": eq.latitude,
                "longitude": eq.longitude,
                "magnitude": eq.magnitude,
                "place": eq.place
            }
            for eq in earthquakes
        ]
    }


@router.get("/earthquakes/live")
async def get_live_earthquakes(
    days: int = Query(1, ge=1, le=7),
    min_magnitude: float = Query(3.0, ge=0, le=10)
):
    """Fetch live earthquakes from USGS (context overlay only)."""
    with USGSClient() as client:
        earthquakes = client.get_recent_earthquakes(
            days=days,
            min_magnitude=min_magnitude
        )

    return {
        "count": len(earthquakes),
        "source": "USGS Live Feed",
        "note": "For map overlay context - not prediction targets",
        "earthquakes": earthquakes
    }


@router.get("/reports")
async def get_reports(
    days: int = Query(30, ge=1, le=365),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Get recent UFO reports with piezoelectric scores."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(UFOReport).filter(
        UFOReport.datetime >= cutoff
    )

    if min_score > 0:
        query = query.filter(UFOReport.specter_score >= min_score)

    reports = query.order_by(UFOReport.datetime.desc()).limit(100).all()

    return {
        "count": len(reports),
        "reports": [
            {
                "id": r.id,
                "datetime": r.datetime.isoformat() if r.datetime else None,
                "city": r.city,
                "state": r.state,
                "shape": r.shape,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "specter_score": r.specter_score,
                "magnetic_anomaly": r.magnetic_anomaly,
                "description": r.description[:200] if r.description else None
            }
            for r in reports
        ]
    }


@router.get("/reports/by-geology")
async def get_reports_by_geology(
    geology_type: str = Query("low_magnetic", regex="^(low_magnetic|high_magnetic|all)$"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get reports filtered by geology type (magnetic signature)."""
    query = db.query(UFOReport).filter(
        UFOReport.latitude.isnot(None),
        UFOReport.magnetic_anomaly.isnot(None)
    )

    if geology_type == "low_magnetic":
        # Piezoelectric zone: |magnetic| < 100 nT
        query = query.filter(
            UFOReport.magnetic_anomaly > -100,
            UFOReport.magnetic_anomaly < 100
        )
    elif geology_type == "high_magnetic":
        # Non-piezoelectric: |magnetic| >= 100 nT
        query = query.filter(
            (UFOReport.magnetic_anomaly <= -100) | (UFOReport.magnetic_anomaly >= 100)
        )

    reports = query.order_by(UFOReport.specter_score.desc()).limit(limit).all()

    return {
        "count": len(reports),
        "geology_type": geology_type,
        "reports": [
            {
                "id": r.id,
                "datetime": r.datetime.isoformat() if r.datetime else None,
                "city": r.city,
                "state": r.state,
                "shape": r.shape,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "specter_score": r.specter_score,
                "magnetic_anomaly": r.magnetic_anomaly
            }
            for r in reports
        ]
    }


@router.get("/reports/high-score")
async def get_high_score_reports(
    min_score: float = Query(60, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get highest-scoring reports (likely piezoelectric terrain)."""
    reports = db.query(UFOReport).filter(
        UFOReport.specter_score >= min_score,
        UFOReport.scored == True
    ).order_by(UFOReport.specter_score.desc()).limit(limit).all()

    return {
        "count": len(reports),
        "min_score_filter": min_score,
        "interpretation": "High scores = low magnetic anomaly + orb/light shape + physical effects",
        "reports": [
            {
                "id": r.id,
                "datetime": r.datetime.isoformat() if r.datetime else None,
                "city": r.city,
                "state": r.state,
                "shape": r.shape,
                "specter_score": r.specter_score,
                "score_breakdown": r.score_breakdown,
                "magnetic_anomaly": r.magnetic_anomaly
            }
            for r in reports
        ]
    }


@router.get("/correlation")
async def get_geology_correlation(db: Session = Depends(get_db)):
    """Get correlation statistics between magnetic anomaly and report clustering."""
    # Get reports with magnetic data
    reports = db.query(UFOReport).filter(
        UFOReport.magnetic_anomaly.isnot(None),
        UFOReport.latitude.isnot(None)
    ).all()

    if len(reports) < 10:
        return {
            "status": "insufficient_data",
            "report_count": len(reports),
            "message": "Need at least 10 reports with magnetic data for correlation"
        }

    # Calculate statistics by magnetic zone
    low_mag = [r for r in reports if abs(r.magnetic_anomaly or 999) < 100]
    high_mag = [r for r in reports if abs(r.magnetic_anomaly or 0) >= 100]

    low_mag_scores = [r.specter_score for r in low_mag if r.specter_score]
    high_mag_scores = [r.specter_score for r in high_mag if r.specter_score]

    # Orb/light shapes by zone
    orb_shapes = ['orb', 'sphere', 'circle', 'light', 'fireball', 'flash']
    low_mag_orbs = sum(1 for r in low_mag if r.shape and r.shape.lower() in orb_shapes)
    high_mag_orbs = sum(1 for r in high_mag if r.shape and r.shape.lower() in orb_shapes)

    return {
        "status": "ok",
        "total_reports": len(reports),
        "zones": {
            "low_magnetic": {
                "count": len(low_mag),
                "avg_score": round(sum(low_mag_scores) / len(low_mag_scores), 1) if low_mag_scores else 0,
                "orb_percentage": round(100 * low_mag_orbs / len(low_mag), 1) if low_mag else 0
            },
            "high_magnetic": {
                "count": len(high_mag),
                "avg_score": round(sum(high_mag_scores) / len(high_mag_scores), 1) if high_mag_scores else 0,
                "orb_percentage": round(100 * high_mag_orbs / len(high_mag), 1) if high_mag else 0
            }
        },
        "interpretation": {
            "hypothesis": "Piezoelectric geology (low magnetic) produces more orb/light phenomena",
            "validated": "Magnetic-UFO correlation (rho=-0.497) is statistically significant",
            "note": "Earthquake timing correlation was NOT validated (M≥4.0 test failed)"
        }
    }


@router.get("/hotspots")
async def get_hotspots(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get hotspot locations by piezoelectric score."""
    hotspots = db.query(HotspotCache).order_by(
        HotspotCache.avg_specter_score.desc()
    ).limit(limit).all()

    return {
        "count": len(hotspots),
        "hotspots": [
            {
                "city": h.city,
                "state": h.state,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "report_count": h.report_count,
                "avg_specter_score": h.avg_specter_score,
                "magnetic_anomaly": h.magnetic_anomaly
            }
            for h in hotspots
        ]
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)

    # Counts
    total_reports = db.query(func.count(UFOReport.id)).scalar() or 0
    total_earthquakes = db.query(func.count(Earthquake.id)).scalar() or 0

    # Reports with magnetic data
    reports_with_mag = db.query(func.count(UFOReport.id)).filter(
        UFOReport.magnetic_anomaly.isnot(None)
    ).scalar() or 0

    # High score reports (piezoelectric terrain)
    high_score_count = db.query(func.count(UFOReport.id)).filter(
        UFOReport.specter_score >= 60
    ).scalar() or 0

    # Low magnetic reports
    low_mag_count = db.query(func.count(UFOReport.id)).filter(
        UFOReport.magnetic_anomaly.isnot(None),
        UFOReport.magnetic_anomaly > -100,
        UFOReport.magnetic_anomaly < 100
    ).scalar() or 0

    # Average score
    avg_score = db.query(func.avg(UFOReport.specter_score)).filter(
        UFOReport.scored == True
    ).scalar() or 0

    return {
        "timestamp": now.isoformat(),
        "totals": {
            "ufo_reports": total_reports,
            "earthquakes": total_earthquakes,
            "reports_with_magnetic_data": reports_with_mag
        },
        "geology": {
            "low_magnetic_reports": low_mag_count,
            "high_score_reports": high_score_count,
            "average_score": round(avg_score, 1)
        },
        "note": "SPECTER TRACKER v2.0 - Correlation tracker, not earthquake predictor"
    }


@router.post("/score")
async def score_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    shape: str = Query("unknown"),
    description: str = Query("")
):
    """Score a location for piezoelectric potential (no earthquake timing)."""
    scorer = get_scoring_engine()

    # Score WITHOUT earthquake proximity (removed from v2.0)
    score = scorer.score_report(
        lat=latitude,
        lon=longitude,
        shape=shape,
        description=description,
        report_datetime=datetime.utcnow(),
        nearby_earthquakes=[]  # Empty - no earthquake scoring in v2.0
    )

    # Get magnetic anomaly directly
    grid = get_magnetic_grid()
    magnetic = grid.get_anomaly(latitude, longitude)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "shape": shape,
        "score": score,
        "magnetic_anomaly": magnetic,
        "interpretation": {
            "piezoelectric_zone": abs(magnetic or 999) < 100 if magnetic else None,
            "note": "Score based on magnetic signature, shape, and physical effects only"
        }
    }


@router.get("/magnetic")
async def get_magnetic_at_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """[DEPRECATED] Get magnetic anomaly value at a specific location.

    Note: The geology/magnetic hypothesis did not survive rigorous testing.
    This endpoint is kept for historical purposes. Use /military-proximity instead.
    """
    grid = get_magnetic_grid()
    anomaly = grid.get_anomaly(latitude, longitude)

    if anomaly is None:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "magnetic_anomaly": None,
            "status": "out_of_grid_bounds",
            "deprecated": True,
            "note": "Geology hypothesis did not replicate. Use /api/military-proximity instead."
        }

    return {
        "latitude": latitude,
        "longitude": longitude,
        "magnetic_anomaly": round(anomaly, 1),
        "geology_type": "piezoelectric" if abs(anomaly) < 100 else "non_piezoelectric",
        "deprecated": True,
        "note": "Geology hypothesis did not replicate. Use /api/military-proximity instead."
    }


# =============================================================================
# NEW: Military Proximity Endpoints (Primary Analysis)
# =============================================================================

@router.get("/military-proximity")
async def get_military_proximity_stats(db: Session = Depends(get_db)):
    """Get statistics on UFO reports by distance to military bases.

    This is the PRIMARY finding: UFO reports are 5.47x more likely within 50km
    of military bases compared to random US locations (p < 0.0001).
    """
    # Get reports with location data
    reports = db.query(UFOReport).filter(
        UFOReport.latitude.isnot(None),
        UFOReport.longitude.isnot(None)
    ).all()

    if not reports:
        return {
            "status": "no_data",
            "message": "No reports with location data available"
        }

    # Calculate distances
    within_50 = 0
    within_100 = 0
    within_150 = 0
    base_counts = {}

    for r in reports:
        result = get_nearest_base(r.latitude, r.longitude)
        dist = result['distance_km']
        base_name = result['base']['name'] if result['base'] else 'Unknown'

        if dist <= 50:
            within_50 += 1
        if dist <= 100:
            within_100 += 1
            # Count by base
            base_counts[base_name] = base_counts.get(base_name, 0) + 1
        if dist <= 150:
            within_150 += 1

    total = len(reports)

    # Top bases by report proximity
    top_bases = sorted(base_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "status": "ok",
        "primary_finding": {
            "description": "UFO reports cluster near military bases",
            "statistical_significance": "p < 0.0001 (Mann-Whitney U)",
            "survives_bonferroni": True
        },
        "total_reports_analyzed": total,
        "by_distance": {
            "within_50km": {
                "count": within_50,
                "percentage": round(100 * within_50 / total, 1),
                "vs_random_baseline": "5.47x"
            },
            "within_100km": {
                "count": within_100,
                "percentage": round(100 * within_100 / total, 1),
                "vs_random_baseline": "3.81x"
            },
            "within_150km": {
                "count": within_150,
                "percentage": round(100 * within_150 / total, 1),
                "vs_random_baseline": "2.54x"
            }
        },
        "top_bases_within_100km": [
            {"name": name, "report_count": count}
            for name, count in top_bases
        ],
        "interpretation": "Most parsimonious explanation: People see military aircraft and misidentify them as UFOs, especially near test ranges where experimental aircraft fly."
    }


@router.get("/military-bases")
async def get_military_bases():
    """Get list of tracked military bases with coordinates."""
    return {
        "count": len(MILITARY_BASES),
        "bases": MILITARY_BASES,
        "note": "32 major US military bases including test ranges, air force bases, naval air stations, and army installations"
    }


@router.get("/military-proximity/check")
async def check_location_proximity(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Check how close a location is to the nearest military base."""
    result = get_nearest_base(latitude, longitude)

    proximity_category = "far"
    if result['distance_km'] <= 50:
        proximity_category = "close"
    elif result['distance_km'] <= 100:
        proximity_category = "medium"

    return {
        "latitude": latitude,
        "longitude": longitude,
        "nearest_base": result['base'],
        "distance_km": round(result['distance_km'], 1),
        "proximity_category": proximity_category,
        "note": f"UFO reports in the '{proximity_category}' category are {'5.47x' if proximity_category == 'close' else '3.81x' if proximity_category == 'medium' else '~baseline'} more common than random locations"
    }


@router.get("/what-failed")
async def get_failed_hypotheses():
    """Document what hypotheses did NOT survive rigorous testing.

    Transparency about failures is how science works.
    """
    return {
        "failed_hypotheses": [
            {
                "name": "SPECTER Hypothesis",
                "claim": "UFOs appear as earthquake precursors",
                "result": "FAILED at M≥4.0 threshold (inverted to 0.62x ratio)",
                "note": "The '8.32x elevation' claim was an artifact of using M≥1.0 threshold"
            },
            {
                "name": "FERRO Hypothesis",
                "claim": "UFOs cluster in iron-rich geology",
                "result": "Did not replicate in blind test",
                "note": "Magnetic correlation was statistically significant but explanation failed"
            },
            {
                "name": "Physical Effects Cases",
                "claim": "Physical evidence validates UFO encounters",
                "result": "Keyword noise, no verified patterns",
                "note": "'Physical effects' in descriptions ≠ actual verifiable evidence"
            },
            {
                "name": "Abduction Physical Evidence",
                "claim": "Abduction reports include verifiable physical evidence",
                "result": "None verified",
                "note": "No case with independently confirmed physical evidence"
            }
        ],
        "surviving_findings": [
            {
                "name": "Military Proximity",
                "effect_size": "5.47x within 50km",
                "p_value": "< 0.0001",
                "survives_bonferroni": True
            },
            {
                "name": "Temporal Patterns",
                "effect_size": "Evening: 61.8%, Summer: 32.4%",
                "p_value": "< 0.0001",
                "interpretation": "Reflects human behavior, not UFO behavior"
            },
            {
                "name": "Shape Evolution",
                "effect_size": "Disc: 30%→7%, Triangle: 3%→9.5%",
                "interpretation": "Cultural influence on perception"
            }
        ],
        "methodology_note": "All major patterns tested with Bonferroni correction (α = 0.05/6 = 0.0083)"
    }
