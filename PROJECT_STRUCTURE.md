# 📁 Struktur Proyek - Last Mile Delivery Optimization

## 🎯 Overview
Proyek ini telah direstrukturisasi menjadi struktur package Python yang modular dan professional.

## 📂 Struktur Direktori

```
Last-Mile-Delivery-Optimization/
├── last_mile/                    # 📦 Package utama aplikasi
│   ├── __init__.py              # Entry point package
│   ├── app.py                   # ⚡ FastAPI application
│   │
│   ├── services/                # 🔧 Business Logic Layer
│   │   ├── __init__.py
│   │   ├── ga.py               # Genetic Algorithm untuk TSP
│   │   ├── geocode.py          # Geocoding menggunakan Nominatim
│   │   └── routing.py          # Distance matrix & OSRM routing
│   │
│   ├── core/                    # 🛠️ Core Utilities
│   │   ├── __init__.py
│   │   ├── storage.py          # Caching & file storage
│   │   └── utils.py            # Helper functions (haversine, dll)
│   │
│   ├── models/                  # 📋 Data Models
│   │   └── __init__.py         # Pydantic models (untuk future)
│   │
│   └── config/                  # ⚙️ Configuration
│       └── __init__.py         # App settings & constants
│
├── tests/                       # ✅ Test Suite
│   ├── __init__.py
│   ├── test_app.py             # API endpoint tests
│   ├── test_ga.py              # GA algorithm tests
│   ├── test_geocode.py         # Geocoding tests
│   ├── test_routing.py         # Routing tests
│   └── test_utils.py           # Utility function tests
│
├── static/                      # 🎨 Frontend Files
│   └── index.html              # Web UI
│
├── examples/                    # 📚 API Examples
│   └── API_EXAMPLES.md
│
├── run.py                       # 🚀 Main entry point
├── requirements.txt             # 📦 Dependencies
├── Dockerfile                   # 🐳 Container config
├── docker-compose.yml           # 🐳 Multi-container setup
├── pytest.ini                   # ⚙️ Pytest configuration
└── README.md                    # 📖 Dokumentasi utama
```

## 🚀 Cara Menjalankan

### Method 1: Direct Python
```bash
python run.py
```

### Method 2: Uvicorn Direct
```bash
uvicorn last_mile.app:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Docker
```bash
docker-compose up
```

## 📝 Import Guidelines

### Dari dalam package `last_mile`:
```python
# Import services
from last_mile.services.ga import solve_tsp, GAConfig
from last_mile.services.geocode import parse_input_locations
from last_mile.services.routing import build_distance_matrix

# Import core utilities
from last_mile.core.storage import cache_get, cache_set
from last_mile.core.utils import haversine

# Import app
from last_mile.app import app
```

### Untuk testing:
```python
# Test imports
from last_mile.services.ga import solve_tsp
from last_mile.app import app
```

## ✅ Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ga.py

# Run with coverage
pytest --cov=last_mile --cov-report=html
```

## 🎯 Keuntungan Struktur Baru

### ✨ Modular
- Setiap komponen punya tanggung jawab yang jelas
- Mudah menemukan kode yang dicari

### 🔄 Scalable
- Mudah menambah fitur baru tanpa mengacaukan struktur
- Dapat menambah module baru di `services/` atau `core/`

### 🧪 Testable
- Struktur memudahkan unit testing
- Import yang jelas dan konsisten

### 📦 Importable
- Bisa diimport sebagai Python package
- Mendukung relative dan absolute imports

### 🏗️ Professional
- Mengikuti best practices Python
- Struktur familiar untuk developer lain

## 📌 Notes

- Semua file Python lama di root sudah dihapus
- Imports di semua file sudah diupdate
- Tests sudah disesuaikan dengan struktur baru
- Dockerfile sudah diupdate untuk menjalankan `last_mile.app:app`

## 🔗 Endpoints

- **API Root**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Web UI**: http://localhost:8000/ui
- **Health Check**: http://localhost:8000/health
