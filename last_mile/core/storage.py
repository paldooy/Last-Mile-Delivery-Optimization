# storage.py - Modul untuk caching sederhana menggunakan file JSON
# Digunakan untuk cache hasil geocoding dan distance matrix agar tidak perlu request ulang

import json  # Modul untuk parsing dan serializing JSON
import os  # Modul untuk operasi file system
from typing import Any, Optional  # Type hints untuk any type dan optional values

CACHE_DIR = os.getenv("ROUTE_CACHE_DIR", "./.cache")  # Mendapatkan cache directory dari environment variable, default ke "./.cache" jika tidak ada. os.getenv(key, default) mengambil env var
os.makedirs(CACHE_DIR, exist_ok=True)  # Membuat direktori cache jika belum ada. exist_ok=True artinya tidak error jika direktori sudah ada

def cache_get(key: str) -> Optional[Any]:  # Fungsi untuk mengambil data dari cache. Return Optional[Any] artinya bisa return any type atau None
    """Mengambil data dari cache berdasarkan key. Return None jika tidak ditemukan atau error."""
    path = os.path.join(CACHE_DIR, f"{key}.json")  # Membuat path file cache dengan format key.json. os.path.join() menggabungkan path dengan separator yang sesuai OS
    if not os.path.exists(path):  # Cek apakah file cache ada. os.path.exists() return True jika path ada
        return None  # Return None jika file tidak ada
    try:  # Try-except untuk handle error saat baca file
        with open(path, "r", encoding="utf-8") as f:  # Buka file dalam mode read ("r") dengan encoding UTF-8. 'with' statement otomatis close file setelah selesai
            return json.load(f)  # Parse JSON file dan return hasilnya. json.load(file) membaca file dan convert JSON ke Python object (dict/list/etc)
    except Exception:  # Catch semua exception (file corrupt, invalid JSON, etc)
        return None  # Return None jika ada error

def cache_set(key: str, value: Any) -> None:  # Fungsi untuk menyimpan data ke cache. Return None (void function)
    """Menyimpan data ke cache dengan key tertentu."""
    path = os.path.join(CACHE_DIR, f"{key}.json")  # Membuat path file cache
    with open(path, "w", encoding="utf-8") as f:  # Buka file dalam mode write ("w"), akan create/overwrite file
        json.dump(value, f, ensure_ascii=False, indent=2)  # Serialize Python object ke JSON dan tulis ke file. ensure_ascii=False agar karakter Unicode tidak di-escape. indent=2 untuk pretty print (readable)
