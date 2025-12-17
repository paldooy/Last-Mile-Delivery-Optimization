# routing.py - Service untuk menghitung jarak dan durasi antar lokasi menggunakan OSRM atau Haversine fallback
import requests  # Library untuk HTTP requests ke OSRM API
from typing import List, Tuple, Optional  # Type hints
from last_mile.core.utils import haversine  # Import fungsi haversine untuk fallback calculation
from last_mile.core.storage import cache_get, cache_set  # Fungsi caching untuk menghindari repeated OSRM requests
import hashlib  # Library untuk hashing (create unique cache key)
import json  # Untuk serialize coordinates untuk hashing
import logging  # Untuk logging

logger = logging.getLogger(__name__)  # Create logger instance

DEFAULT_OSRM_URL = "http://localhost:5000"  # Default OSRM server URL (assumes OSRM running locally)
OSRM_TIMEOUT = 30  # Timeout untuk OSRM requests dalam detik
MAX_RETRIES = 2  # Maximum retry attempts untuk OSRM requests


def _create_cache_key(locations: List[dict]) -> str:  # Private function (prefix _) untuk membuat unique cache key dari list locations
    """Membuat unique cache key dari list locations menggunakan MD5 hash."""  
    coords_str = json.dumps([(loc['lat'], loc['lon']) for loc in locations], sort_keys=True)  # List comprehension untuk extract coordinates, json.dumps() serialize ke JSON string. sort_keys=True untuk konsisten ordering
    return "distmat_" + hashlib.md5(coords_str.encode()).hexdigest()[:16]  # MD5 hash dari coords_str. encode() convert string ke bytes. hexdigest() return hash dalam format hex string. [:16] ambil 16 karakter pertama saja


def _coordinates_list(locations: List[dict]) -> str:  # Private function untuk format coordinates ke string format yang dibutuhkan OSRM
    """Format coordinates ke string format OSRM: 'lon,lat;lon,lat;...'"""  
    return ";".join(f"{loc['lon']},{loc['lat']}" for loc in locations)  # List comprehension dengan join. OSRM butuh format "lon,lat" (longitude dulu), dipisahkan semicolon


def build_distance_matrix(  # Fungsi utama untuk build distance matrix antara semua lokasi
    locations: List[dict],  # List locations dengan format [{"lat": x, "lon": y}, ...]
    osrm_base_url: str = DEFAULT_OSRM_URL,  # OSRM server URL, default ke localhost:5000
    use_duration: bool = False,  # True jika ingin optimasi by duration, False untuk distance
    retries: int = MAX_RETRIES  # Jumlah retry attempts
) -> Tuple[List[List[float]], Optional[List[List[float]]], Optional[str]]:  # Return tuple: (distances matrix, durations matrix atau None, polyline atau None)
    """  
    Build distance matrix menggunakan OSRM API, fallback ke Haversine jika gagal.
    
    Returns:
        Tuple of (distance_matrix, duration_matrix, polyline)
        - distance_matrix: 2D array jarak dalam meter
        - duration_matrix: 2D array durasi dalam detik (None jika use_duration=False)
        - polyline: Encoded polyline untuk visualisasi (None jika OSRM gagal)
    """

    if not locations or len(locations) < 2:  # Validasi input: cek jika locations kosong atau < 2 lokasi
        return [[0.0]], None, None  # Return matrix 1x1 dengan jarak 0 jika tidak ada lokasi yang cukup

    # --- CHECK CACHE ---
    cache_key = _create_cache_key(locations)  # Buat unique cache key dari locations
    cached = cache_get(cache_key)  # Coba ambil dari cache
    if cached:  # Jika ada di cache
        logger.info("Cache hit for OSRM matrix")  # Log cache hit
        polyline = cached.get("polyline")  # Ambil polyline dari cache. dict.get(key) return None jika key tidak ada

        # jika polyline kosong, request ulang
        if not polyline:  # Jika polyline tidak ada di cache (could be None atau empty string)
            polyline = get_osrm_polyline(locations, osrm_base_url)  # Request polyline dari OSRM
            cached["polyline"] = polyline  # Update cached data dengan polyline baru
            cache_set(cache_key, cached)  # Save updated cache

        return cached["distances"], cached.get("durations"), polyline  # Return cached data


    coords = _coordinates_list(locations)  # Format coordinates ke format OSRM string
    table_url = f"{osrm_base_url}/table/v1/driving/{coords}"  # Build OSRM table endpoint URL. /table endpoint return distance matrix
    params = {"annotations": "distance,duration"}  # Query params: request both distance dan duration annotations

    polyline = None  # Inisialisasi polyline dengan None

    # --- TRY OSRM TABLE ---
    for attempt in range(retries):  # Retry loop
        try:  # Try-except untuk handle request errors
            r = requests.get(table_url, params=params, timeout=OSRM_TIMEOUT)  # HTTP GET request ke OSRM

            if r.status_code == 200:  # Status 200 = success
                j = r.json()  # Parse JSON response
                distances = j.get("distances")  # Ambil distances matrix dari response. Ini adalah 2D array (list of lists)
                durations = j.get("durations") if use_duration else None  # Ambil durations hanya jika use_duration=True, otherwise None

                if distances and len(distances) == len(locations):  # Validasi: cek jika distances ada dan ukurannya sesuai dengan jumlah locations
                    polyline = get_osrm_polyline(locations, osrm_base_url)  # Request polyline untuk visualisasi rute

                    cache_set(cache_key, {  # Save ke cache
                        "distances": distances,  # Distance matrix
                        "durations": durations,  # Duration matrix
                        "polyline": polyline  # Polyline string
                    })

                    return distances, durations, polyline  # Return hasil OSRM

        except:  # Catch semua exceptions (timeout, network error, etc)
            pass  # Ignore error dan lanjut ke retry atau fallback. pass adalah no-op statement

    # --- FALLBACK HAVERSINE ---
    distances, durations = _haversine_fallback(locations)  # Jika OSRM gagal setelah semua retries, gunakan Haversine fallback
    cache_set(cache_key, {  # Save fallback results ke cache
        "distances": distances,
        "durations": durations,
        "polyline": None  # Polyline None karena tidak ada OSRM routing
    })
    return distances, durations, None  # Return fallback results tanpa polyline


def _haversine_fallback(locations: List[dict]):  # Private function untuk calculate distance matrix menggunakan Haversine formula (fallback jika OSRM gagal)
    """
    Calculate distance dan duration matrix menggunakan Haversine formula.
    Digunakan sebagai fallback jika OSRM tidak tersedia.
    Duration di-estimate menggunakan asumsi kecepatan rata-rata.
    """
    n = len(locations)  # Jumlah lokasi
    distances = [[0.0] * n for _ in range(n)]  # Inisialisasi 2D array n x n dengan nilai 0.0. List comprehension dengan nested loop: [[0,0,0], [0,0,0], [0,0,0]] untuk n=3
    durations = [[0.0] * n for _ in range(n)]  # Inisialisasi duration matrix
    speed = 40_000 / 3600.0  # Asumsi kecepatan rata-rata 40 km/h convert ke m/s. 40_000 meter/jam dibagi 3600 detik = m/s. Underscore di 40_000 hanya untuk readability (sama dengan 40000)

    for i in range(n):  # Loop untuk setiap lokasi sebagai source
        for j in range(n):  # Loop untuk setiap lokasi sebagai destination
            if i == j:  # Jika source dan destination sama
                continue  # Skip, karena distance dari i ke i adalah 0 (sudah di-init)
            d = haversine(  # Calculate distance menggunakan Haversine formula
                (locations[i]["lat"], locations[i]["lon"]),  # Koordinat source (tuple)
                (locations[j]["lat"], locations[j]["lon"])  # Koordinat destination (tuple)
            )
            distances[i][j] = d  # Set distance di matrix
            durations[i][j] = d / speed  # Calculate duration = distance / speed. Ini adalah estimate kasar

    return distances, durations  # Return tuple (distances, durations)


def get_osrm_polyline(locations: List[dict], osrm_base_url: str = DEFAULT_OSRM_URL):  # Fungsi untuk mendapatkan polyline dari OSRM route endpoint
    """
    Mendapatkan encoded polyline dari OSRM untuk visualisasi rute di map.
    Polyline adalah format encoded Google Polyline untuk merepresentasikan path/rute.
    """
    if len(locations) < 2:  # Validasi: butuh minimal 2 lokasi untuk membuat route
        return None  # Return None jika tidak cukup lokasi

    coords = ";".join(f"{loc['lon']},{loc['lat']}" for loc in locations)  # Format coordinates ke OSRM string format
    params = {"overview": "full", "geometries": "polyline"}  # Query params: overview=full untuk complete route geometry, geometries=polyline untuk format polyline (bisa juga geojson)
    url = f"{osrm_base_url}/route/v1/driving/{coords}"  # Build OSRM route endpoint URL. /route endpoint return detailed route dengan geometry

    try:  # Try-except untuk handle errors
        r = requests.get(url, params=params, timeout=OSRM_TIMEOUT)  # HTTP GET request
        if r.status_code == 200:  # Status 200 = success
            j = r.json()  # Parse JSON response
            return j["routes"][0]["geometry"]  # Return polyline string. j["routes"] adalah array routes, ambil [0] route pertama, lalu ["geometry"] untuk polyline string
    except:  # Catch semua exceptions
        pass  # Ignore error, return None

    return None  # Return None jika request gagal
