# simple file/in-memory cache
# storage.py
import json
import os
from typing import Any, Optional

CACHE_DIR = os.getenv("ROUTE_CACHE_DIR", "./.cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_get(key: str) -> Optional[Any]:
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def cache_set(key: str, value: Any) -> None:
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
