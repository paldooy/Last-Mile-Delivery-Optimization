# 🎯 Quick Reference - Web UI

## 🚀 Akses Cepat

```
http://localhost:8000/ui
```

---

## ⌨️ Cara Cepat Testing

### Method 1: Example Coordinates (Tercepat - 1-3 detik)
1. Klik **📌 Example Coords**
2. Klik **🚀 Optimize Route**
3. ✅ Done!

### Method 2: Example Addresses (5-10 detik, butuh geocoding)
1. Klik **📝 Example Jakarta**
2. Klik **🚀 Optimize Route**
3. ✅ Done!

### Method 3: Custom Input
1. Input alamat atau koordinat
2. Klik **➕ Add Location** untuk tambah
3. Atur GA parameters (opsional)
4. Klik **🚀 Optimize Route**
5. ✅ Done!

---

## 📝 Input Format

### Alamat (Geocoding)
```
Monas, Jakarta
Grand Indonesia Mall, Jakarta
Ancol, Jakarta Utara
```

### Koordinat (Langsung)
```
Latitude:  -6.2088
Longitude: 106.8456
```

---

## ⚙️ Recommended Settings

| Jumlah Lokasi | Pop Size | Generations | Time |
|---------------|----------|-------------|------|
| 5-10          | 100      | 200         | ~1s  |
| 10-20         | 200      | 300         | ~2s  |
| 20-30         | 250      | 400         | ~4s  |
| 30-50         | 300      | 500         | ~8s  |

---

## 📊 Output Explained

```
✅ Route Optimized!
📏 Distance: 45.23 km    → Total jarak perjalanan
⏱️  Duration: 68.5 min   → Estimasi waktu (jika tersedia)
🔄 Generations: 300      → Jumlah iterasi GA
💻 Time: 2.34s          → Waktu komputasi

1. Monas             -6.1751, 106.8271
2. Grand Indonesia   -6.1951, 106.8211
3. Ancol             -6.1223, 106.8975
...
```

---

## 🔧 Keyboard Shortcuts

- **Enter** di input field → Tidak ada (belum implemented)
- **Tab** → Navigate antar fields
- **Esc** → Tidak ada (belum implemented)

---

## ❌ Common Errors

### "Cannot connect to API server"
```bash
# Solution: Start server
cd route_optimizer
python app.py
```

### "Geocoding failed for address"
```
Cause: Invalid/ambiguous address
Fix: Use more specific address or coordinates
```

### "Provide at least 2 locations"
```
Cause: Less than 2 valid locations
Fix: Add more locations
```

---

## 💡 Pro Tips

1. **Koordinat Lebih Cepat**: Gunakan koordinat langsung untuk skip geocoding
2. **Test Dulu Kecil**: Mulai dengan 3-5 lokasi untuk test cepat
3. **Tuning Parameters**: Experiment dengan pop_size dan generations
4. **Save Results**: Screenshot atau copy hasil untuk dokumentasi
5. **Browser Console**: Buka F12 untuk debug jika ada error

---

## 🎨 UI Elements

| Element | Function |
|---------|----------|
| 📌 Example Coords | Load 5 sample coordinates |
| 📝 Example Jakarta | Load 4 Jakarta addresses |
| ➕ Add Location | Add new location input |
| ✕ Button | Remove location |
| 🚀 Optimize Route | Start optimization |
| Green Header | Shows metrics after success |
| Route List | Optimal order with numbers |

---

## 🔗 Related Pages

- Main API: http://localhost:8000/
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Full Guide: `UI_GUIDE.md`
- Examples: `examples/API_EXAMPLES.md`

---

Made with ❤️ for easier testing!
