# utils.py - Utility functions untuk kalkulasi geografis
import math  # Modul matematika untuk fungsi trigonometri dan konstanta
from typing import Tuple  # Type hint untuk tuple

R_EARTH = 6371000.0  # Radius bumi dalam meter. Konstanta untuk kalkulasi jarak great-circle

def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:  # Fungsi untuk menghitung jarak great-circle antara dua koordinat. Tuple[float, float] adalah type hint untuk tuple dengan 2 float (lat, lon)
    """
    Menghitung jarak great-circle dalam meter antara dua koordinat (lat, lon).
    
    Haversine formula adalah metode untuk menghitung jarak terpendek di permukaan bola
    antara dua titik berdasarkan koordinat latitude dan longitude.
    
    Args:
        coord1: Tuple (latitude, longitude) untuk titik pertama
        coord2: Tuple (latitude, longitude) untuk titik kedua
    
    Returns:
        Jarak dalam meter
    """
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])  # Unpack tuple coord1 ke lat1 dan lon1, lalu convert dari degrees ke radians. math.radians() convert degree to radian (needed for trig functions)
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])  # Convert coord2 ke radians
    dlat = lat2 - lat1  # Selisih latitude dalam radians
    dlon = lon2 - lon1  # Selisih longitude dalam radians
    a = math.sin(dlat/2.0)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2.0)**2  # Haversine formula part 1. **2 adalah pangkat 2. math.sin() dan math.cos() adalah fungsi trigonometri
    c = 2 * math.asin(math.sqrt(a))  # Haversine formula part 2. math.sqrt() adalah square root. math.asin() adalah arc sine (inverse sine)
    return R_EARTH * c  # Kalikan dengan radius bumi untuk mendapatkan jarak dalam meter
