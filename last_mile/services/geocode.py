# geocode.py - Service untuk mengkonversi alamat menjadi koordinat GPS menggunakan Nominatim (OpenStreetMap)
import requests  # Library untuk HTTP requests
import time  # Untuk delay/sleep antara requests
from typing import Tuple, Optional, Dict, List  # Type hints
from last_mile.core.storage import cache_get, cache_set  # Fungsi caching untuk menghindari repeated requests
import logging  # Untuk logging

logger = logging.getLogger(__name__)  # Create logger instance untuk modul ini

USER_AGENT = "RouteOptimizer/1.0 (your-email@example.com)"  # User agent untuk identify aplikasi kita ke Nominatim API (required by Nominatim policy)
NOMINATIM_DELAY = 1.0  # Delay dalam detik antara requests (Nominatim policy: max 1 request/second)
MAX_RETRIES = 3  # Maksimal percobaan retry jika request gagal

def geocode_address(
    address: str,  # Alamat yang akan di-geocode
    rate_limit_sleep: float = NOMINATIM_DELAY,  # Delay antar request, default dari konstanta
    retries: int = MAX_RETRIES  # Jumlah retry, default dari konstanta
) -> Optional[Tuple[float, float]]:  # Return tuple (lat, lon) atau None jika gagal
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
    key = "geocode_" + address.replace("/", "_").replace(" ", "_")[:200]  # Buat cache key dari address. replace() mengganti karakter "/" dan spasi dengan "_" untuk safe filename. [:200] limit panjang key max 200 karakter (slice notation)
    cached = cache_get(key)  # Coba ambil dari cache
    if cached:  # Jika ada di cache
        logger.debug(f"Cache hit for address: {address}")  # Log cache hit (level debug)
        return (cached["lat"], cached["lon"])  # Return tuple (lat, lon) dari cache. cached adalah dict dengan key "lat" dan "lon"

    url = "https://nominatim.openstreetmap.org/search"  # Endpoint Nominatim API untuk search/geocoding
    params = {"q": address, "format": "json", "limit": 1}  # Query parameters: q=query address, format=json untuk JSON response, limit=1 ambil result pertama saja
    headers = {"User-Agent": USER_AGENT}  # HTTP headers dengan User-Agent (required by Nominatim)
    
    for attempt in range(retries):  # Loop retry. range(3) menghasilkan [0, 1, 2], jadi max 3 kali percobaan
        try:  # Try-except untuk handle request errors
            logger.info(f"Geocoding '{address}' (attempt {attempt + 1}/{retries})")  # Log attempt number (attempt + 1 karena attempt dimulai dari 0)
            r = requests.get(url, params=params, headers=headers, timeout=10)  # HTTP GET request dengan params dan headers. timeout=10 artinya max wait 10 detik
            
            if r.status_code == 200:  # Status code 200 = OK/success
                data = r.json()  # Parse JSON response ke Python object (list of dicts). r.json() adalah shortcut untuk json.loads(r.text)
                if data and len(data) > 0:  # Cek jika data tidak empty dan ada minimal 1 result
                    lat = float(data[0]["lat"])  # Ambil latitude dari result pertama (index 0). float() convert string ke float number
                    lon = float(data[0]["lon"])  # Ambil longitude
                    cache_set(key, {"lat": lat, "lon": lon})  # Simpan ke cache agar tidak perlu request lagi untuk address yang sama
                    time.sleep(rate_limit_sleep)  # Sleep/delay untuk respect Nominatim rate limit (max 1 req/sec). time.sleep() menghentikan eksekusi untuk beberapa detik
                    logger.info(f"Successfully geocoded '{address}' -> ({lat}, {lon})")  # Log success
                    return (lat, lon)  # Return tuple coordinates
                else:  # Jika data empty atau tidak ada result
                    logger.warning(f"No results found for address: {address}")  # Log warning
                    return None  # Return None karena tidak ditemukan
            elif r.status_code == 429:  # Status code 429 = Too Many Requests (rate limited)
                # Rate limited
                wait_time = rate_limit_sleep * (attempt + 1) * 2  # Exponential backoff: wait lebih lama setiap retry. Attempt 0: 2s, attempt 1: 4s, attempt 2: 6s
                logger.warning(f"Rate limited, waiting {wait_time}s before retry...")  # Log rate limit
                time.sleep(wait_time)  # Sleep sebelum retry
            else:  # Status code lainnya (400, 500, etc)
                logger.error(f"Geocoding failed with status {r.status_code}: {r.text}")  # Log error dengan status code dan response text
                
        except requests.Timeout:  # Catch timeout exception (request melebihi 10 detik)
            logger.error(f"Timeout while geocoding '{address}' (attempt {attempt + 1})")  # Log timeout
            if attempt < retries - 1:  # Jika bukan attempt terakhir (attempt < 2 untuk max 3 retries)
                time.sleep(rate_limit_sleep)  # Sleep before retry
        except Exception as e:  # Catch semua exception lainnya (network error, etc)
            logger.error(f"Error geocoding '{address}': {str(e)}")  # Log error dengan detail exception
            if attempt < retries - 1:  # Jika bukan attempt terakhir
                time.sleep(rate_limit_sleep)  # Sleep before retry
    
    logger.error(f"Failed to geocode '{address}' after {retries} attempts")  # Log final failure setelah semua retry gagal
    return None  # Return None jika semua attempts gagal

def parse_input_locations(items: list) -> List[Dict]:  # Fungsi untuk parse dan validate input locations. items adalah list of dicts, return List[Dict]
    """
    Parse dan geocode list of locations.
    
    items: list of either {"address": "..."} or {"lat": x, "lon": y}
    returns list of {"label": str, "lat": float, "lon": float}
    
    Raises ValueError jika geocoding gagal atau format invalid
    """
    out = []  # Inisialisasi list output kosong
    for i, it in enumerate(items):  # Loop dengan enumerate untuk dapat index dan item. enumerate(["a", "b"]) menghasilkan [(0, "a"), (1, "b")]
        if "address" in it:  # Cek jika item punya key "address". Operator 'in' untuk check key existence di dict
            coords = geocode_address(it["address"])  # Geocode address menjadi coordinates
            if coords is None:  # Jika geocoding gagal (return None)
                raise ValueError(f"Geocoding failed for address: {it['address']}")  # Raise ValueError dengan pesan error. Ini akan di-catch di app.py
            out.append({"label": it.get("label", it["address"]), "lat": coords[0], "lon": coords[1]})  # Append ke output. it.get("label", default) ambil label jika ada, kalau tidak pakai address sebagai label. coords[0] adalah lat, coords[1] adalah lon
        elif "lat" in it and "lon" in it:  # Jika item punya lat dan lon (koordinat langsung)
            out.append({"label": it.get("label", f"pt_{i}"), "lat": float(it["lat"]), "lon": float(it["lon"])})  # Append ke output. Default label adalah "pt_0", "pt_1", etc jika tidak ada label. f"pt_{i}" adalah f-string dengan variable i
        else:  # Jika format tidak valid (tidak ada address maupun lat/lon)
            raise ValueError("Each item must contain 'address' or 'lat' & 'lon'")  # Raise ValueError
    return out  # Return list of parsed locations
