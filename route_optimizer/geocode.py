# Nominatim geocoding
# geocode.py
import requests
import time
from typing import Tuple, Optional, Dict, List
from storage import cache_get, cache_set
import logging

logger = logging.getLogger(__name__)

USER_AGENT = "RouteOptimizer/1.0 (your-email@example.com)"
NOMINATIM_DELAY = 1.0  # seconds between requests (Nominatim policy)
MAX_RETRIES = 3

def geocode_address(
    address: str, 
    rate_limit_sleep: float = NOMINATIM_DELAY,
    retries: int = MAX_RETRIES
) -> Optional[Tuple[float, float]]:
    """
    Use Nominatim to geocode an address. Returns (lat, lon) or None.
    Respects rate limit and implements retry logic.
    Caches results to avoid repeated requests.
    
    Args:
        address: Street address to geocode
        rate_limit_sleep: Seconds to wait between requests
        retries: Number of retry attempts
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    # Check cache first
    key = "geocode_" + address.replace("/", "_").replace(" ", "_")[:200]
    cached = cache_get(key)
    if cached:
        logger.debug(f"Cache hit for address: {address}")
        return (cached["lat"], cached["lon"])

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(retries):
        try:
            logger.info(f"Geocoding '{address}' (attempt {attempt + 1}/{retries})")
            r = requests.get(url, params=params, headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                if data and len(data) > 0:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    cache_set(key, {"lat": lat, "lon": lon})
                    time.sleep(rate_limit_sleep)  # Respect Nominatim usage policy
                    logger.info(f"Successfully geocoded '{address}' -> ({lat}, {lon})")
                    return (lat, lon)
                else:
                    logger.warning(f"No results found for address: {address}")
                    return None
            elif r.status_code == 429:
                # Rate limited
                wait_time = rate_limit_sleep * (attempt + 1) * 2
                logger.warning(f"Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"Geocoding failed with status {r.status_code}: {r.text}")
                
        except requests.Timeout:
            logger.error(f"Timeout while geocoding '{address}' (attempt {attempt + 1})")
            if attempt < retries - 1:
                time.sleep(rate_limit_sleep)
        except Exception as e:
            logger.error(f"Error geocoding '{address}': {str(e)}")
            if attempt < retries - 1:
                time.sleep(rate_limit_sleep)
    
    logger.error(f"Failed to geocode '{address}' after {retries} attempts")
    return None

def parse_input_locations(items: list) -> List[Dict]:
    """
    items: list of either {"address": "..."} or {"lat": x, "lon": y}
    returns list of {"label": str, "lat": float, "lon": float}
    """
    out = []
    for i, it in enumerate(items):
        if "address" in it:
            coords = geocode_address(it["address"])
            if coords is None:
                raise ValueError(f"Geocoding failed for address: {it['address']}")
            out.append({"label": it.get("label", it["address"]), "lat": coords[0], "lon": coords[1]})
        elif "lat" in it and "lon" in it:
            out.append({"label": it.get("label", f"pt_{i}"), "lat": float(it["lat"]), "lon": float(it["lon"])})
        else:
            raise ValueError("Each item must contain 'address' or 'lat' & 'lon'")
    return out
