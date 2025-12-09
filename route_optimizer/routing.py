# routing.py
import requests
from typing import List, Tuple, Optional
from utils import haversine
from storage import cache_get, cache_set
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_OSRM_URL = "http://localhost:5000"
OSRM_TIMEOUT = 30  # seconds
MAX_RETRIES = 2

def _create_cache_key(locations: List[dict]) -> str:
    """Create a unique cache key based on all location coordinates"""
    coords_str = json.dumps([(loc['lat'], loc['lon']) for loc in locations], sort_keys=True)
    return "distmat_" + hashlib.md5(coords_str.encode()).hexdigest()[:16]

def _coordinates_list(locations: List[dict]) -> str:
    """Format coordinates for OSRM API: lon,lat;lon,lat;..."""
    return ";".join(f"{loc['lon']},{loc['lat']}" for loc in locations)

def build_distance_matrix(
    locations: List[dict], 
    osrm_base_url: str = DEFAULT_OSRM_URL, 
    use_duration: bool = False,
    retries: int = MAX_RETRIES
) -> Tuple[List[List[float]], Optional[List[List[float]]]]:
    """
    Build distance and duration matrices using OSRM API.
    Falls back to haversine distance if OSRM fails.
    
    Args:
        locations: List of dicts with 'lat' and 'lon' keys
        osrm_base_url: Base URL for OSRM API
        use_duration: Whether to calculate duration matrix
        retries: Number of retry attempts for OSRM
        
    Returns:
        Tuple of (distance_matrix_meters, duration_matrix_seconds_or_none)
    """
    if not locations or len(locations) < 2:
        logger.warning("Less than 2 locations provided")
        return [[0.0]], None
    
    # Check cache
    cache_key = _create_cache_key(locations)
    cached = cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for distance matrix ({len(locations)} locations)")
        return cached["distances"], cached.get("durations")

    # Try OSRM API
    coords = _coordinates_list(locations)
    table_url = f"{osrm_base_url}/table/v1/driving/{coords}"
    params = {"annotations": "distance,duration"}
    
    for attempt in range(retries):
        try:
            logger.info(f"Requesting OSRM distance matrix (attempt {attempt + 1}/{retries})")
            r = requests.get(table_url, params=params, timeout=OSRM_TIMEOUT)
            
            if r.status_code == 200:
                j = r.json()
                distances = j.get("distances")
                durations = j.get("durations") if use_duration else None
                
                if distances and len(distances) == len(locations):
                    logger.info(f"Successfully got OSRM distance matrix ({len(locations)} locations)")
                    cache_set(cache_key, {"distances": distances, "durations": durations})
                    return distances, durations
                else:
                    logger.warning("OSRM response missing or incomplete distance data")
            else:
                logger.warning(f"OSRM returned status {r.status_code}")
                
        except requests.Timeout:
            logger.warning(f"OSRM request timeout (attempt {attempt + 1})")
        except requests.ConnectionError:
            logger.warning(f"Cannot connect to OSRM server at {osrm_base_url}")
            break  # No point retrying connection errors
        except Exception as e:
            logger.error(f"OSRM request error: {str(e)}")
    
    # Fallback to haversine
    logger.warning("Falling back to haversine distance calculation")
    return _haversine_fallback(locations, cache_key)

def _haversine_fallback(
    locations: List[dict], 
    cache_key: str
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Calculate distance and duration matrices using haversine formula.
    Estimates duration using average speed of 40 km/h.
    """
    n = len(locations)
    distances = [[0.0] * n for _ in range(n)]
    durations = [[0.0] * n for _ in range(n)]
    avg_speed_m_s = 40_000 / 3600.0  # 40 km/h in m/s
    
    for i in range(n):
        for j in range(n):
            if i == j:
                distances[i][j] = 0.0
                durations[i][j] = 0.0
            else:
                d = haversine(
                    (locations[i]["lat"], locations[i]["lon"]), 
                    (locations[j]["lat"], locations[j]["lon"])
                )
                distances[i][j] = d
                durations[i][j] = d / avg_speed_m_s
    
    cache_set(cache_key, {"distances": distances, "durations": durations})
    logger.info(f"Haversine fallback completed ({n} locations)")
    return distances, durations
