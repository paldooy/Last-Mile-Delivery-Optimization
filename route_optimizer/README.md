# 🚚 Route Optimizer - Delivery Route Optimization API

**Route Optimizer** adalah aplikasi backend Python yang mengoptimalkan urutan pengiriman (delivery route) menggunakan **Genetic Algorithm** untuk menyelesaikan masalah **Traveling Salesman Problem (TSP)**. Aplikasi ini menggunakan **Nominatim** untuk geocoding dan **OSRM** untuk perhitungan jarak/durasi perjalanan.

---

## 📋 Fitur Utama

✅ **Geocoding Otomatis** - Konversi alamat ke koordinat menggunakan Nominatim (OpenStreetMap)  
✅ **Distance Matrix** - Perhitungan jarak menggunakan OSRM API dengan fallback ke Haversine  
✅ **Genetic Algorithm** - Optimasi rute dengan TSP solver yang efisien  
✅ **RESTful API** - FastAPI dengan dokumentasi otomatis (Swagger/ReDoc)  
✅ **Web UI** - Interface visual untuk testing yang mudah (NEW!)  
✅ **Caching** - Caching hasil geocoding dan distance matrix untuk performa  
✅ **Error Handling** - Retry mechanism dan logging yang lengkap  
✅ **Docker Ready** - Containerized deployment dengan multi-stage build  

---

## 🏗️ Struktur Proyek

```
route_optimizer/
├── app.py              # FastAPI main application
├── ga.py               # Genetic Algorithm TSP solver
├── geocode.py          # Nominatim geocoding with caching
├── routing.py          # OSRM distance matrix with fallback
├── storage.py          # File-based caching system
├── utils.py            # Haversine distance calculation
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container configuration
├── .env.example        # Environment variables template
├── static/
│   └── index.html      # Web UI for testing
├── tests/
│   ├── test_ga.py      # GA unit tests
│   ├── test_geocode.py # Geocoding tests
│   ├── test_routing.py # Routing unit tests
│   ├── test_app.py     # API endpoint tests
│   └── test_utils.py   # Utility tests
└── README.md           # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional, untuk containerized deployment)
- OSRM server (optional, akan fallback ke haversine jika tidak tersedia)

### 1. Clone & Install

```bash
cd route_optimizer
pip install -r requirements.txt
```

### 2. Setup Environment (Opsional)

```bash
cp .env.example .env
# Edit .env sesuai kebutuhan
```

### 3. Jalankan Server

```bash
# Development mode dengan auto-reload
python app.py

# Atau menggunakan uvicorn langsung
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di `http://localhost:8000`

### 4. Akses Aplikasi

- **🎨 Web UI (Recommended)**: http://localhost:8000/ui
- **📚 Swagger UI**: http://localhost:8000/docs
- **📖 ReDoc**: http://localhost:8000/redoc
- **💚 Health Check**: http://localhost:8000/health

> 💡 **Tip**: Gunakan Web UI untuk testing yang lebih mudah dan visual!

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t route-optimizer .
```

### Run Container

```bash
docker run -d \
  --name route-optimizer \
  -p 8000:8000 \
  -e OSRM_URL=http://router.project-osrm.org \
  route-optimizer
```

### Docker Compose (Opsional)

Buat file `docker-compose.yml`:

```yaml
version: '3.8'
services:
  route-optimizer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OSRM_URL=http://router.project-osrm.org
      - PORT=8000
    volumes:
      - ./.cache:/app/.cache
    restart: unless-stopped
```

Jalankan:
```bash
docker-compose up -d
```

---

## 📡 API Usage

### Endpoint: `POST /solve`

Menghitung rute optimal dari daftar lokasi.

#### Request Body

```json
{
  "locations": [
    {
      "address": "Jl. Sudirman No. 1, Jakarta",
      "label": "Customer A"
    },
    {
      "lat": -6.2297,
      "lon": 106.8206,
      "label": "Customer B"
    },
    {
      "lat": -6.2088,
      "lon": 106.8456,
      "label": "Customer C"
    }
  ],
  "pop_size": 200,
  "generations": 300,
  "use_duration": false
}
```

#### Response

```json
{
  "ordered": [
    {
      "index": 0,
      "label": "Customer A",
      "lat": -6.2088,
      "lon": 106.8456
    },
    {
      "index": 2,
      "label": "Customer C",
      "lat": -6.2297,
      "lon": 106.8206
    },
    {
      "index": 1,
      "label": "Customer B",
      "lat": -6.2297,
      "lon": 106.8456
    }
  ],
  "total_distance_m": 5234.56,
  "total_duration_s": 720.5,
  "generations_run": 300,
  "computation_time_s": 1.23
}
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
      {"lat": -6.2297, "lon": 106.8456, "label": "Point B"},
      {"lat": -6.2297, "lon": 106.8206, "label": "Point C"}
    ],
    "pop_size": 200,
    "generations": 300
  }'
```

### Python Example

```python
import requests

url = "http://localhost:8000/solve"
payload = {
    "locations": [
        {"address": "Monas, Jakarta", "label": "Monas"},
        {"address": "Grand Indonesia, Jakarta", "label": "Grand Indonesia"},
        {"address": "Ancol, Jakarta", "label": "Ancol"}
    ],
    "pop_size": 200,
    "generations": 300
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Optimal route:")
for loc in result['ordered']:
    print(f"  {loc['index']}. {loc['label']}")
print(f"Total distance: {result['total_distance_m']/1000:.2f} km")
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
pytest

# Run dengan coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_ga.py -v
```

### Test Coverage

```bash
# Install coverage
pip install pytest-cov

# Generate HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OSRM_URL` | `http://localhost:5000` | OSRM server URL |
| `PORT` | `8000` | Server port |
| `ROUTE_CACHE_DIR` | `./.cache` | Cache directory |
| `LOG_LEVEL` | `INFO` | Logging level |

### GA Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `pop_size` | 200 | 50-1000 | Population size |
| `generations` | 300 | 50-2000 | Number of generations |
| `crossover_rate` | 0.9 | 0-1 | Crossover probability |
| `mutation_rate` | 0.02 | 0-1 | Mutation probability |
| `elite_size` | 5 | 1-20 | Elite individuals kept |

---

## 📊 Performance & Limitations

### Performance

- **20 lokasi**: ~0.5-2 detik
- **50 lokasi**: ~2-5 detik
- **100+ lokasi**: ~10-30 detik (tergantung parameter GA)

### Limitations

1. **Nominatim Rate Limit**: 1 request/second (sudah dihandle dengan delay)
2. **OSRM Limitations**: Tergantung pada OSRM server yang digunakan
3. **Memory Usage**: ~50-100MB untuk 50 lokasi
4. **Optimal Solution**: GA tidak menjamin solusi optimal global, tapi mendekati

### Optimization Tips

- Untuk < 20 lokasi: gunakan `pop_size=100, generations=200`
- Untuk 20-50 lokasi: gunakan `pop_size=200, generations=300`
- Untuk > 50 lokasi: gunakan `pop_size=300, generations=500`
- Gunakan koordinat langsung jika memungkinkan (skip geocoding)
- Pertimbangkan OSRM server lokal untuk performa lebih baik

---

## 🔧 Troubleshooting

### OSRM Connection Error

Jika OSRM tidak tersedia, aplikasi akan otomatis fallback ke perhitungan Haversine.

```bash
# Gunakan public OSRM demo server
export OSRM_URL=http://router.project-osrm.org

# Atau jalankan OSRM lokal dengan Docker
docker run -d -p 5000:5000 \
  -v "${PWD}/osrm-data:/data" \
  osrm/osrm-backend osrm-routed --algorithm mld /data/indonesia-latest.osrm
```

### Geocoding Failures

Jika geocoding gagal:
- Cek koneksi internet
- Pastikan format alamat jelas dan lengkap
- Gunakan koordinat langsung jika memungkinkan

### Cache Issues

```bash
# Clear cache
rm -rf .cache/

# Atau set cache dir ke tempat lain
export ROUTE_CACHE_DIR=/tmp/route-cache
```

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

MIT License - silakan digunakan untuk proyek komersial maupun non-komersial.

---

## 👨‍💻 Author

Developed for Last-Mile Delivery Optimization project.

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OSRM API](http://project-osrm.org/)
- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)
- [Genetic Algorithms for TSP](https://en.wikipedia.org/wiki/Travelling_salesman_problem)
