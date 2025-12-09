# utils.py
import math
from typing import Tuple

R_EARTH = 6371000.0  # meters

def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Return great-circle distance in meters between two (lat, lon)."""
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2.0)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2.0)**2
    c = 2 * math.asin(math.sqrt(a))
    return R_EARTH * c
