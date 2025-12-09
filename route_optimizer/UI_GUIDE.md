# 🎨 Web UI Guide - Route Optimizer

Web UI sederhana untuk testing Route Optimizer API dengan mudah.

---

## 🚀 Mengakses UI

Setelah server berjalan, buka browser dan akses:

```
http://localhost:8000/ui
```

Atau klik langsung: [http://localhost:8000/ui](http://localhost:8000/ui)

---

## 📋 Fitur UI

### 1. **Input Locations** (Panel Kiri)

Anda bisa input lokasi dengan 2 cara:

#### Cara 1: Menggunakan Alamat (Geocoding)
- Isi kolom **Address** dengan alamat lengkap
- Contoh: `Monas, Jakarta` atau `Grand Indonesia Mall, Jakarta`
- Biarkan kolom Latitude dan Longitude kosong
- API akan otomatis geocode alamat menjadi koordinat

#### Cara 2: Menggunakan Koordinat Langsung
- Kosongkan kolom Address
- Isi **Latitude** dan **Longitude**
- Contoh: `-6.2088` dan `106.8456`

### 2. **Quick Examples**

Klik tombol berikut untuk load data contoh:

- **📝 Example Jakarta**: Load alamat-alamat di Jakarta (butuh geocoding)
- **📌 Example Coords**: Load koordinat langsung (lebih cepat)

### 3. **Manage Locations**

- **➕ Add Location**: Tambah lokasi baru
- **✕ (X Button)**: Hapus lokasi tertentu
- **Minimum**: 2 lokasi diperlukan untuk optimasi

### 4. **Algorithm Parameters**

Sesuaikan parameter Genetic Algorithm:

- **Population Size** (50-1000):
  - Lebih kecil = lebih cepat, kurang akurat
  - Lebih besar = lebih lambat, lebih akurat
  - Default: 200

- **Generations** (50-2000):
  - Lebih sedikit = lebih cepat, mungkin kurang optimal
  - Lebih banyak = lebih lambat, lebih optimal
  - Default: 300

**Rekomendasi:**
- 5-10 lokasi: `pop_size=100, generations=200`
- 10-30 lokasi: `pop_size=200, generations=300`
- 30+ lokasi: `pop_size=300, generations=500`

### 5. **Optimize Route Button**

Klik tombol **🚀 Optimize Route** untuk memulai optimasi.

---

## 📊 Membaca Hasil (Panel Kanan)

### Metrics (Header Hijau)

Setelah optimasi selesai, Anda akan melihat:

- **📏 Distance**: Total jarak dalam kilometer
- **⏱️ Duration**: Estimasi waktu perjalanan (jika tersedia)
- **🔄 Generations**: Jumlah generasi yang dijalankan
- **💻 Time**: Waktu komputasi dalam detik

### Route List

Daftar lokasi dalam urutan optimal:

1. Setiap item menampilkan:
   - **Nomor urutan** (1, 2, 3, ...)
   - **Label lokasi**
   - **Koordinat** (lat, lon)

2. Ikuti urutan ini untuk rute pengiriman optimal

---

## 💡 Tips Penggunaan

### Testing Cepat
1. Klik **📌 Example Coords**
2. Langsung klik **🚀 Optimize Route**
3. Lihat hasil dalam 1-3 detik

### Testing dengan Geocoding
1. Klik **📝 Example Jakarta**
2. Klik **🚀 Optimize Route**
3. Tunggu ~5-10 detik (geocoding + optimasi)

### Custom Locations
1. Hapus semua lokasi (klik ✕)
2. Klik **➕ Add Location** beberapa kali
3. Input alamat atau koordinat Anda
4. Sesuaikan GA parameters jika perlu
5. Klik **🚀 Optimize Route**

---

## 🎯 Contoh Use Case

### Skenario: Pengiriman Paket di Jakarta

**Input:**
```
1. Monas, Jakarta
2. Grand Indonesia, Jakarta
3. Ancol, Jakarta Utara
4. Taman Mini Indonesia Indah
5. Kota Tua Jakarta
```

**Steps:**
1. Klik **📝 Example Jakarta** atau input manual
2. Set `pop_size=250, generations=400` untuk hasil lebih baik
3. Klik **🚀 Optimize Route**
4. Tunggu ~10-15 detik

**Output:**
- Urutan pengiriman optimal
- Total jarak (misal: 45.2 km)
- Estimasi waktu (misal: 75 menit)

---

## ⚠️ Troubleshooting

### Error: "Cannot connect to API server"

**Solusi:**
- Pastikan server berjalan di terminal
- Cek dengan: `http://localhost:8000/health`
- Restart server jika perlu

### Error: "Geocoding failed for address"

**Penyebab:**
- Alamat tidak valid atau terlalu ambigu
- Koneksi internet bermasalah
- Nominatim rate limit tercapai

**Solusi:**
- Gunakan alamat yang lebih spesifik
- Tunggu 1-2 detik antara request
- Atau gunakan koordinat langsung

### Result tidak muncul

**Solusi:**
- Buka Developer Console (F12)
- Lihat error di Console tab
- Check Network tab untuk API response

---

## 🔧 Customization

### Mengubah Warna Theme

Edit file `static/index.html`, bagian `<style>`:

```css
/* Main gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Ubah menjadi warna favorit Anda */
background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
```

### Menambah Preset Lokasi

Edit function `loadExampleJakarta()` di JavaScript:

```javascript
const examples = [
    { address: 'Alamat Baru 1', lat: '', lon: '' },
    { address: 'Alamat Baru 2', lat: '', lon: '' },
    // tambahkan lebih banyak...
];
```

---

## 📱 Mobile Friendly

UI sudah responsive untuk mobile:
- Grid otomatis jadi 1 kolom
- Input locations stack vertical
- Touch-friendly buttons

---

## 🔗 Links

- **Home**: http://localhost:8000/
- **Web UI**: http://localhost:8000/ui
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🎨 Screenshot Guide

### Initial View
- Panel kiri: Input form
- Panel kanan: "Enter locations..." message

### After Optimization
- Panel kiri: Input yang sudah diisi
- Panel kanan: 
  - Green header dengan metrics
  - Numbered route list

### Loading State
- Spinner animation
- "Optimizing route..." message

---

## 💻 Browser Support

Tested & working on:
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

---

Happy optimizing! 🚀
