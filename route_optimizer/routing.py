import requests
from typing import List, Tuple, Optional
from utils import haversine
from storage import cache_get, cache_set
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_OSRM_URL = "http://localhost:5000"
OSRM_TIMEOUT = 30
MAX_RETRIES = 2


def _create_cache_key(locations: List[dict]) -> str:
    coords_str = json.dumps([(loc['lat'], loc['lon']) for loc in locations], sort_keys=True)
    return "distmat_" + hashlib.md5(coords_str.encode()).hexdigest()[:16]


def _coordinates_list(locations: List[dict]) -> str:
    return ";".join(f"{loc['lon']},{loc['lat']}" for loc in locations)


def build_distance_matrix(
    locations: List[dict],
    osrm_base_url: str = DEFAULT_OSRM_URL,
    use_duration: bool = False,
    retries: int = MAX_RETRIES
) -> Tuple[List[List[float]], Optional[List[List[float]]], Optional[str]]:

    if not locations or len(locations) < 2:
        return [[0.0]], None, None

    # --- CHECK CACHE ---
    cache_key = _create_cache_key(locations)
    cached = cache_get(cache_key)
    if cached:
        logger.info("Cache hit for OSRM matrix")
        polyline = cached.get("polyline")

        # jika polyline kosong, request ulang
        if not polyline:
            polyline = get_osrm_polyline(locations, osrm_base_url)
            cached["polyline"] = polyline
            cache_set(cache_key, cached)

        return cached["distances"], cached.get("durations"), polyline


    coords = _coordinates_list(locations)
    table_url = f"{osrm_base_url}/table/v1/driving/{coords}"
    params = {"annotations": "distance,duration"}

    polyline = None

    # --- TRY OSRM TABLE ---
    for attempt in range(retries):
        try:
            r = requests.get(table_url, params=params, timeout=OSRM_TIMEOUT)

            if r.status_code == 200:
                j = r.json()
                distances = j.get("distances")
                durations = j.get("durations") if use_duration else None

                if distances and len(distances) == len(locations):
                    polyline = get_osrm_polyline(locations, osrm_base_url)

                    cache_set(cache_key, {
                        "distances": distances,
                        "durations": durations,
                        "polyline": polyline
                    })

                    return distances, durations, polyline

        except:
            pass

    # --- FALLBACK HAVERSINE ---
    distances, durations = _haversine_fallback(locations)
    cache_set(cache_key, {
        "distances": distances,
        "durations": durations,
        "polyline": None
    })
    return distances, durations, None


def _haversine_fallback(locations: List[dict]):
    n = len(locations)
    distances = [[0.0] * n for _ in range(n)]
    durations = [[0.0] * n for _ in range(n)]
    speed = 40_000 / 3600.0  # 40 km/h in m/s

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = haversine(
                (locations[i]["lat"], locations[i]["lon"]),
                (locations[j]["lat"], locations[j]["lon"])
            )
            distances[i][j] = d
            durations[i][j] = d / speed

    return distances, durations


def get_osrm_polyline(locations: List[dict], osrm_base_url: str = DEFAULT_OSRM_URL):
    if len(locations) < 2:
        return None

    coords = ";".join(f"{loc['lon']},{loc['lat']}" for loc in locations)
    params = {"overview": "full", "geometries": "polyline"}
    url = f"{osrm_base_url}/route/v1/driving/{coords}"

    try:
        r = requests.get(url, params=params, timeout=OSRM_TIMEOUT)
        if r.status_code == 200:
            j = r.json()
            return j["routes"][0]["geometry"]
    except:
        pass

    return None
