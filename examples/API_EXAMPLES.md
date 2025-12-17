# 📡 API Examples - Route Optimizer

Contoh-contoh penggunaan Route Optimizer API dengan berbagai bahasa dan tools.

---

## 1. cURL Examples

### Basic Request (Menggunakan Koordinat)

```bash
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
      {"lat": -6.2297, "lon": 106.8456, "label": "Point B"},
      {"lat": -6.2297, "lon": 106.8206, "label": "Point C"},
      {"lat": -6.1751, "lon": 106.8650, "label": "Point D"}
    ],
    "pop_size": 200,
    "generations": 300
  }'
```

### Request dengan Alamat (Geocoding)

```bash
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"address": "Monas, Jakarta", "label": "Monas"},
      {"address": "Grand Indonesia, Jakarta", "label": "Grand Indonesia"},
      {"address": "Ancol, Jakarta Utara", "label": "Ancol"},
      {"address": "Taman Mini Indonesia Indah", "label": "TMII"}
    ],
    "pop_size": 250,
    "generations": 400
  }'
```

### Request dengan Custom OSRM Server

```bash
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
      {"lat": -6.2297, "lon": 106.8456, "label": "Point B"}
    ],
    "osrm_url": "http://router.project-osrm.org",
    "use_duration": true,
    "pop_size": 200,
    "generations": 300
  }'
```

---

## 2. Python Examples

### Simple Request

```python
import requests
import json

url = "http://localhost:8000/solve"

payload = {
    "locations": [
        {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
        {"lat": -6.2297, "lon": 106.8456, "label": "Point B"},
        {"lat": -6.2297, "lon": 106.8206, "label": "Point C"},
    ],
    "pop_size": 200,
    "generations": 300
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    result = response.json()
    print("✅ Route optimized successfully!")
    print(f"\nOptimal route order:")
    for i, loc in enumerate(result['ordered'], 1):
        print(f"  {i}. {loc['label']} ({loc['lat']}, {loc['lon']})")
    
    print(f"\nTotal distance: {result['total_distance_m']/1000:.2f} km")
    print(f"Computation time: {result['computation_time_s']:.2f} seconds")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.json())
```

### Request dengan Geocoding

```python
import requests

url = "http://localhost:8000/solve"

# Daftar alamat pengiriman
delivery_addresses = [
    "Monas, Jakarta",
    "Grand Indonesia Mall, Jakarta",
    "Ancol, Jakarta Utara",
    "Taman Mini Indonesia Indah",
    "Kota Tua Jakarta"
]

payload = {
    "locations": [
        {"address": addr, "label": addr.split(",")[0]}
        for addr in delivery_addresses
    ],
    "pop_size": 250,
    "generations": 400
}

print("🚀 Optimizing route...")
response = requests.post(url, json=payload)

if response.status_code == 200:
    result = response.json()
    
    print(f"\n📍 Optimized Delivery Route ({len(result['ordered'])} stops):")
    print("=" * 60)
    
    for i, loc in enumerate(result['ordered'], 1):
        print(f"{i}. {loc['label']}")
        print(f"   📌 Coordinates: {loc['lat']:.4f}, {loc['lon']:.4f}")
    
    print("=" * 60)
    print(f"📏 Total Distance: {result['total_distance_m']/1000:.2f} km")
    if result.get('total_duration_s'):
        print(f"⏱️  Estimated Time: {result['total_duration_s']/60:.1f} minutes")
    print(f"⚙️  Generations: {result['generations_run']}")
    print(f"💻 Computation: {result['computation_time_s']:.2f}s")
else:
    print(f"❌ Error {response.status_code}: {response.json()['detail']}")
```

### Batch Processing

```python
import requests
import time

url = "http://localhost:8000/solve"

# Multiple batches of deliveries
batches = [
    {
        "name": "Batch 1 - North Jakarta",
        "locations": [
            {"lat": -6.1381, "lon": 106.8630, "label": "Kelapa Gading"},
            {"lat": -6.1223, "lon": 106.8975, "label": "Pantai Indah Kapuk"},
            {"lat": -6.1386, "lon": 106.7769, "label": "Pluit"},
        ]
    },
    {
        "name": "Batch 2 - South Jakarta",
        "locations": [
            {"lat": -6.2615, "lon": 106.7809, "label": "Senayan"},
            {"lat": -6.3019, "lon": 106.8173, "label": "Pondok Indah"},
            {"lat": -6.2745, "lon": 106.8060, "label": "Blok M"},
        ]
    }
]

results = []

for batch in batches:
    print(f"\n🔄 Processing {batch['name']}...")
    
    payload = {
        "locations": batch['locations'],
        "pop_size": 200,
        "generations": 300
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        results.append({
            "batch": batch['name'],
            "route": result['ordered'],
            "distance_km": result['total_distance_m'] / 1000
        })
        print(f"   ✅ Optimized: {result['total_distance_m']/1000:.2f} km")
    else:
        print(f"   ❌ Failed: {response.json()['detail']}")
    
    time.sleep(0.5)  # Rate limiting

# Summary
print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
for r in results:
    print(f"{r['batch']}: {r['distance_km']:.2f} km")
print(f"\nTotal distance: {sum(r['distance_km'] for r in results):.2f} km")
```

---

## 3. JavaScript/Node.js Examples

### Using Fetch API

```javascript
const url = "http://localhost:8000/solve";

const payload = {
  locations: [
    { lat: -6.2088, lon: 106.8456, label: "Point A" },
    { lat: -6.2297, lon: 106.8456, label: "Point B" },
    { lat: -6.2297, lon: 106.8206, label: "Point C" }
  ],
  pop_size: 200,
  generations: 300
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => {
  console.log('✅ Route optimized successfully!');
  console.log('\nOptimal route:');
  data.ordered.forEach((loc, i) => {
    console.log(`  ${i + 1}. ${loc.label}`);
  });
  console.log(`\nTotal distance: ${(data.total_distance_m / 1000).toFixed(2)} km`);
})
.catch(error => {
  console.error('❌ Error:', error);
});
```

### Using Axios (Node.js)

```javascript
const axios = require('axios');

async function optimizeRoute() {
  try {
    const response = await axios.post('http://localhost:8000/solve', {
      locations: [
        { address: "Monas, Jakarta", label: "Monas" },
        { address: "Grand Indonesia, Jakarta", label: "Grand Indonesia" },
        { address: "Ancol, Jakarta Utara", label: "Ancol" }
      ],
      pop_size: 200,
      generations: 300
    });

    const result = response.data;
    
    console.log('🚀 Optimized Route:');
    result.ordered.forEach((loc, idx) => {
      console.log(`${idx + 1}. ${loc.label} (${loc.lat}, ${loc.lon})`);
    });
    
    console.log(`\n📏 Total Distance: ${(result.total_distance_m / 1000).toFixed(2)} km`);
    console.log(`⏱️  Computation Time: ${result.computation_time_s.toFixed(2)}s`);
    
    return result;
  } catch (error) {
    if (error.response) {
      console.error('❌ Error:', error.response.data.detail);
    } else {
      console.error('❌ Network error:', error.message);
    }
  }
}

optimizeRoute();
```

---

## 4. PowerShell Examples

### Basic Request

```powershell
$url = "http://localhost:8000/solve"

$body = @{
    locations = @(
        @{lat = -6.2088; lon = 106.8456; label = "Point A"},
        @{lat = -6.2297; lon = 106.8456; label = "Point B"},
        @{lat = -6.2297; lon = 106.8206; label = "Point C"}
    )
    pop_size = 200
    generations = 300
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"

Write-Host "✅ Route optimized!" -ForegroundColor Green
Write-Host "`nOptimal route:"
$i = 1
foreach ($loc in $response.ordered) {
    Write-Host "  $i. $($loc.label) ($($loc.lat), $($loc.lon))"
    $i++
}
Write-Host "`nTotal distance: $([math]::Round($response.total_distance_m / 1000, 2)) km"
```

---

## 5. Expected Response Format

```json
{
  "ordered": [
    {
      "index": 0,
      "label": "Point A",
      "lat": -6.2088,
      "lon": 106.8456
    },
    {
      "index": 2,
      "label": "Point C",
      "lat": -6.2297,
      "lon": 106.8206
    },
    {
      "index": 1,
      "label": "Point B",
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

---

## 6. Error Responses

### 400 Bad Request - Insufficient Locations

```json
{
  "detail": "Provide at least 2 locations"
}
```

### 400 Bad Request - Geocoding Failed

```json
{
  "detail": "Geocoding failed for address: Invalid Address XYZ"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Error calculating distances: Connection timeout"
}
```

---

## 7. Testing with Browser

1. Buka browser dan akses: `http://localhost:8000/docs`
2. Klik endpoint **POST /solve**
3. Klik **"Try it out"**
4. Masukkan JSON request di body
5. Klik **"Execute"**
6. Lihat response di bagian bawah

---

## 8. Performance Testing

```python
import requests
import time
import statistics

url = "http://localhost:8000/solve"

# Test dengan berbagai ukuran
test_cases = [
    {"name": "Small (5 points)", "count": 5},
    {"name": "Medium (20 points)", "count": 20},
    {"name": "Large (50 points)", "count": 50}
]

for test in test_cases:
    locations = [
        {"lat": -6.2 + i*0.01, "lon": 106.8 + i*0.01, "label": f"Point {i}"}
        for i in range(test['count'])
    ]
    
    times = []
    for _ in range(3):  # 3 runs
        start = time.time()
        response = requests.post(url, json={
            "locations": locations,
            "pop_size": 200,
            "generations": 300
        })
        times.append(time.time() - start)
    
    if response.status_code == 200:
        print(f"\n{test['name']}:")
        print(f"  Avg time: {statistics.mean(times):.2f}s")
        print(f"  Min time: {min(times):.2f}s")
        print(f"  Max time: {max(times):.2f}s")
        result = response.json()
        print(f"  Distance: {result['total_distance_m']/1000:.2f} km")
```

---

## 📝 Notes

- Semua request menggunakan `Content-Type: application/json`
- Response selalu dalam format JSON
- Pastikan server berjalan di `localhost:8000` (atau sesuaikan URL)
- Untuk geocoding, pastikan koneksi internet aktif
- Rate limit Nominatim: 1 request/second (sudah dihandle otomatis)
