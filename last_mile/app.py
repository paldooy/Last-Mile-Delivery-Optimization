# app.py - File utama aplikasi FastAPI untuk optimasi rute pengiriman
from fastapi import FastAPI, HTTPException  # Import FastAPI framework dan HTTPException untuk handling error
from fastapi.middleware.cors import CORSMiddleware  # Middleware untuk mengizinkan akses dari browser (CORS)
from fastapi.staticfiles import StaticFiles  # Untuk serve file statis (HTML, CSS, JS)
from fastapi.responses import FileResponse  # Untuk mengirim file sebagai response
from pydantic import BaseModel, Field  # Untuk validasi data request/response
from typing import List, Optional  # Type hints untuk list dan optional values
from last_mile.services.geocode import parse_input_locations  # Fungsi untuk convert address ke koordinat
from last_mile.services.routing import build_distance_matrix, DEFAULT_OSRM_URL  # Fungsi untuk hitung jarak antar lokasi
from last_mile.services.ga import solve_tsp, solve_tsp_with_fixed_points, GAConfig  # Algoritma Genetika untuk optimasi rute
import uvicorn  # Server ASGI untuk menjalankan FastAPI
import os  # Modul untuk operasi sistem file dan environment variables
import logging  # Untuk logging informasi dan error
import time  # Untuk menghitung waktu eksekusi
import os  # Import ulang os (redundant, bisa dihapus)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Mendapatkan absolute path dari direktori file ini (__file__ adalah path file app.py, os.path.abspath() membuat path absolut, os.path.dirname() mengambil direktori parent)

# Konfigurasi logging untuk mencatat aktivitas aplikasi
logging.basicConfig(  # Mengatur konfigurasi dasar logging
    level=logging.INFO,  # Set level logging ke INFO (akan log INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Format output: timestamp - nama logger - level - pesan
)
logger = logging.getLogger(__name__)  # Membuat logger instance dengan nama modul ini (__name__ akan menjadi 'last_mile.app')  # Membuat logger instance dengan nama modul ini (__name__ akan menjadi 'last_mile.app')

app = FastAPI(  # Membuat instance aplikasi FastAPI
    title="Route Optimizer API",  # Judul API yang akan muncul di dokumentasi
    description="Optimize delivery routes using Genetic Algorithm, Nominatim Geocoding, and OSRM routing",  # Deskripsi fungsi API
    version="1.0.0"  # Versi API
)

# CORS middleware untuk mengizinkan akses dari browser (Cross-Origin Resource Sharing)
app.add_middleware(  # Menambahkan middleware ke aplikasi FastAPI
    CORSMiddleware,  # Jenis middleware yang digunakan (CORS)
    allow_origins=["*"],  # Mengizinkan request dari semua origin/domain ("*" = semua, bisa diganti dengan list domain spesifik untuk produksi)
    allow_credentials=True,  # Mengizinkan pengiriman cookies dan credentials dalam request
    allow_methods=["*"],  # Mengizinkan semua HTTP methods (GET, POST, PUT, DELETE, dll)
    allow_headers=["*"],  # Mengizinkan semua HTTP headers
)

class InputLocation(BaseModel):  # Model Pydantic untuk validasi input lokasi
    address: Optional[str] = Field(None, description="Street address to geocode")  # Alamat jalan yang akan dikonversi ke koordinat (optional, bisa None)
    lat: Optional[float] = Field(None, description="Latitude coordinate")  # Koordinat latitude (optional)
    lon: Optional[float] = Field(None, description="Longitude coordinate")  # Koordinat longitude (optional)
    label: Optional[str] = Field(None, description="Custom label for this location")  # Label kustom untuk lokasi (optional)
    
    class Config:  # Konfigurasi tambahan untuk model
        json_schema_extra = {  # Contoh data untuk dokumentasi API (akan muncul di Swagger UI)
            "example": {
                "address": "Jl. Sudirman No. 1, Jakarta",  # Contoh alamat
                "label": "Customer A"  # Contoh label
            }
        }

class SolveRequest(BaseModel):  # Model untuk request endpoint /solve
    locations: List[InputLocation] = Field(..., min_length=2, description="List of locations (min 2)")  # List lokasi minimal 2 (... artinya required/wajib)
    osrm_url: Optional[str] = Field(None, description="Custom OSRM server URL")  # URL server OSRM custom (jika None, akan gunakan default)
    use_duration: Optional[bool] = Field(False, description="Optimize by duration instead of distance")  # True = optimasi berdasarkan waktu tempuh, False = berdasarkan jarak
    pop_size: Optional[int] = Field(200, ge=50, le=1000, description="GA population size")  # Ukuran populasi Algoritma Genetika (ge=greater equal/min 50, le=less equal/max 1000)
    generations: Optional[int] = Field(300, ge=50, le=2000, description="GA generations")  # Jumlah generasi/iterasi GA (min 50, max 2000)
    start_index: Optional[int] = Field(None, description="Index of fixed start location (0-based)")  # Index lokasi start yang fixed/tetap (0-based, artinya dimulai dari 0)
    end_index: Optional[int] = Field(None, description="Index of fixed end location (0-based)")  # Index lokasi end yang fixed/tetap
    
    class Config:  # Konfigurasi model
        json_schema_extra = {  # Contoh data untuk dokumentasi
            "example": {  # Object contoh request
                "locations": [  # Array lokasi contoh
                    {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},  # Lokasi pertama
                    {"lat": -6.2297, "lon": 106.8456, "label": "Point B"},  # Lokasi kedua
                    {"lat": -6.2297, "lon": 106.8206, "label": "Point C"}  # Lokasi ketiga
                ],
                "pop_size": 200,  # Ukuran populasi GA
                "generations": 300,  # Jumlah generasi GA
                "start_index": 0,  # Mulai dari index 0 (Point A)
                "end_index": 2  # Akhiri di index 2 (Point C)
            }
        }

class SolveResponse(BaseModel):  # Model untuk response endpoint /solve
    ordered: List[dict] = Field(..., description="Ordered list of locations")  # List lokasi yang sudah diurutkan secara optimal
    total_distance_m: float = Field(..., description="Total distance in meters")  # Total jarak dalam meter
    total_duration_s: Optional[float] = Field(None, description="Total duration in seconds")  # Total durasi dalam detik (optional, hanya ada jika use_duration=True)
    generations_run: int = Field(..., description="Number of GA generations executed")  # Jumlah generasi GA yang dijalankan (bisa lebih kecil dari generations jika early stopping)
    computation_time_s: float = Field(..., description="Computation time in seconds")  # Waktu komputasi total dalam detik
    polyline: Optional[str] = None  # Encoded polyline untuk visualisasi rute di map (format Google Polyline)
    
    class Config:  # Konfigurasi model
        json_schema_extra = {  # Contoh data untuk dokumentasi
            "example": {  # Contoh response
                "ordered": [  # List lokasi yang sudah diurutkan
                    {"index": 0, "label": "Point A", "lat": -6.2088, "lon": 106.8456},  # Lokasi pertama dalam urutan optimal
                    {"index": 2, "label": "Point C", "lat": -6.2297, "lon": 106.8206},  # Lokasi kedua
                    {"index": 1, "label": "Point B", "lat": -6.2297, "lon": 106.8456}  # Lokasi ketiga
                ],
                "total_distance_m": 5234.56,  # Total jarak dalam meter
                "total_duration_s": 720.5,  # Total durasi dalam detik
                "generations_run": 300,  # Jumlah generasi yang dijalankan
                "computation_time_s": 1.23  # Waktu komputasi
            }
        }

@app.get("/")  # Decorator untuk mendefinisikan endpoint HTTP GET di path "/"
def root():  # Fungsi handler untuk endpoint root
    """API health check endpoint"""  # Docstring menjelaskan fungsi endpoint
    return {  # Mengembalikan dictionary (akan dikonversi ke JSON)
        "message": "Route Optimizer API is running",  # Pesan status API
        "version": "1.0.0",  # Versi API
        "endpoints": {  # Dictionary berisi daftar endpoint yang tersedia
            "solve": "/solve (POST)",  # Endpoint utama untuk optimasi rute
            "docs": "/docs",  # Dokumentasi Swagger UI
            "redoc": "/redoc"  # Dokumentasi ReDoc
        }
    }

@app.get("/health")  # Endpoint GET untuk health check
def health_check():  # Fungsi handler
    """Health check for container orchestration"""  # Digunakan oleh Docker/Kubernetes untuk cek status container
    return {"status": "healthy", "service": "route-optimizer"}  # Return status healthy jika API berjalan normal

@app.post("/solve", response_model=SolveResponse)  # Decorator untuk endpoint POST /solve, response_model menentukan struktur response
def solve_endpoint(req: SolveRequest):  # Fungsi handler, parameter req akan divalidasi otomatis sesuai model SolveRequest
    """
    Solve the Traveling Salesman Problem for given locations.
    
    This endpoint accepts a list of locations (as addresses or coordinates),
    geocodes them if needed, calculates distances using OSRM or haversine,
    and finds the optimal route using a Genetic Algorithm.
    """  # Docstring menjelaskan fungsi endpoint (akan muncul di dokumentasi API)
    start_time = time.time()  # Menyimpan waktu mulai eksekusi untuk menghitung computation time
    logger.info(f"Received solve request with {len(req.locations)} locations")  # Logging informasi request yang masuk, f-string untuk format string dengan variabel
    
    if not req.locations or len(req.locations) < 2:  # Validasi: cek jika locations kosong atau kurang dari 2
        raise HTTPException(  # Raise HTTP exception akan mengirim error response ke client
            status_code=400,  # HTTP status code 400 = Bad Request
            detail="Provide at least 2 locations"  # Pesan error yang dikirim ke client
        )

    # Validate start and end indices
    n_locs = len(req.locations)  # Menyimpan jumlah lokasi ke variabel untuk efisiensi
    if req.start_index is not None and (req.start_index < 0 or req.start_index >= n_locs):  # Cek jika start_index di luar range valid (0 hingga n_locs-1)
        raise HTTPException(status_code=400, detail=f"start_index must be between 0 and {n_locs-1}")  # Raise error jika start_index invalid
    if req.end_index is not None and (req.end_index < 0 or req.end_index >= n_locs):  # Cek jika end_index di luar range valid
        raise HTTPException(status_code=400, detail=f"end_index must be between 0 and {n_locs-1}")  # Raise error jika end_index invalid
    if req.start_index is not None and req.end_index is not None and req.start_index == req.end_index:  # Cek jika start dan end sama
        raise HTTPException(status_code=400, detail="start_index and end_index cannot be the same")  # Start dan end harus berbeda

    # Parse and geocode locations
    try:  # Try-except untuk handle error saat parsing/geocoding
        locs = parse_input_locations([  # Memanggil fungsi parse_input_locations dari service geocode
            loc.dict(exclude_none=True) for loc in req.locations  # List comprehension: convert setiap InputLocation object ke dict, exclude_none=True menghapus field yang None
        ])
        logger.info(f"Successfully parsed {len(locs)} locations")  # Log sukses parsing
    except ValueError as e:  # Catch ValueError (error validasi dari parse_input_locations)
        logger.error(f"Geocoding error: {str(e)}")  # Log error geocoding
        raise HTTPException(status_code=400, detail=str(e))  # Return error 400 ke client dengan detail error
    except Exception as e:  # Catch semua exception lainnya
        logger.error(f"Unexpected error during geocoding: {str(e)}")  # Log unexpected error
        raise HTTPException(  # Return error 500 (Internal Server Error)
            status_code=500, 
            detail=f"Error processing locations: {str(e)}"  # Detail error untuk client
        )

    # Build distance matrix
    osrm_url = req.osrm_url or os.getenv("OSRM_URL") or DEFAULT_OSRM_URL  # Menentukan OSRM URL: prioritas req.osrm_url, lalu env var OSRM_URL, lalu default. Operator 'or' akan pilih nilai pertama yang truthy (tidak None/empty)
    try:  # Try-except untuk handle error saat build matrix
        distances, durations, polyline = build_distance_matrix(  # Memanggil fungsi build_distance_matrix, returns 3 values (tuple unpacking)
            locs,  # List lokasi yang sudah diparsing
            osrm_url,  # URL OSRM server
            use_duration=req.use_duration  # Boolean apakah optimasi pakai duration atau distance
        )
        logger.info(f"Built distance matrix ({len(distances)}x{len(distances)})")  # Log sukses, len(distances) adalah ukuran matrix (N x N)
    except Exception as e:  # Catch semua exception
        logger.error(f"Error building distance matrix: {str(e)}")  # Log error
        raise HTTPException(  # Return error 500
            status_code=500,
            detail=f"Error calculating distances: {str(e)}"  # Detail error
        )

    # Solve TSP using Genetic Algorithm
    try:  # Try-except untuk handle error saat solving
        cfg = GAConfig(pop_size=req.pop_size, generations=req.generations)  # Membuat config object untuk GA dengan parameter dari request
        
        # Use fixed start/end if provided
        if req.start_index is not None or req.end_index is not None:  # Cek jika ada start atau end index yang di-fix
            res = solve_tsp_with_fixed_points(  # Gunakan fungsi khusus untuk fixed points
                distances,  # Distance matrix
                cfg,  # GA configuration
                start_idx=req.start_index,  # Index start yang fixed (bisa None)
                end_idx=req.end_index  # Index end yang fixed (bisa None)
            )
            logger.info(f"GA solved with fixed points in {res['generations_run']} generations")  # Log hasil dengan fixed points
        else:  # Jika tidak ada fixed points
            res = solve_tsp(distances, cfg)  # Gunakan fungsi TSP standard
            logger.info(f"GA solved in {res['generations_run']} generations")  # Log hasil
    except Exception as e:  # Catch error saat solving
        logger.error(f"Error in GA solver: {str(e)}")  # Log error
        raise HTTPException(  # Return error 500
            status_code=500,
            detail=f"Error optimizing route: {str(e)}"  # Detail error
        )
    print("POLYLINE:", polyline)  # Debug print untuk melihat polyline (untuk development/debugging)


    # Calculate total duration if available
    route_idx = res["route"]  # Mengambil route (list index) dari hasil GA. Dictionary access dengan bracket notation
    total_distance = res["distance"]  # Mengambil total distance dari hasil GA
    total_duration = None  # Inisialisasi total_duration dengan None (default jika tidak dihitung)
    
    if durations and req.use_duration:  # Cek jika durations matrix ada dan user request optimasi by duration
        try:  # Try-except untuk handle error saat kalkulasi duration
            d = 0.0  # Inisialisasi counter duration dengan 0.0 (float)
            for i in range(len(route_idx) - 1):  # Loop dari index 0 hingga n-2 (karena kita akses i dan i+1). range(5) menghasilkan [0,1,2,3,4]
                d += durations[route_idx[i]][route_idx[i+1]]  # Akses duration dari matrix, tambahkan ke total. durations[from_idx][to_idx] memberikan waktu tempuh
            total_duration = d  # Set total_duration dengan hasil kalkulasi
            logger.info(f"Total duration: {total_duration:.2f}s")  # Log total duration, .2f format float dengan 2 desimal
        except Exception as e:  # Catch error saat kalkulasi
            logger.warning(f"Could not calculate total duration: {str(e)}")  # Log warning (bukan error karena tidak critical)

    # Build ordered response
    ordered = []  # Inisialisasi list kosong untuk menyimpan lokasi yang sudah diurutkan
    for idx in route_idx:  # Loop setiap index dalam route optimal. route_idx adalah list seperti [2, 0, 1] yang artinya urutan optimal adalah lokasi index 2, lalu 0, lalu 1
        ordered.append({  # Append dictionary ke list ordered. append() menambahkan elemen ke akhir list
            "index": idx,  # Index lokasi di input array original
            "label": locs[idx]["label"],  # Ambil label lokasi dari locs array menggunakan index. locs[idx] mengambil dict lokasi ke-idx, lalu ["label"] mengambil value label
            "lat": locs[idx]["lat"],  # Ambil latitude lokasi
            "lon": locs[idx]["lon"]  # Ambil longitude lokasi
        })

    computation_time = time.time() - start_time  # Hitung waktu komputasi dengan mengurangi waktu sekarang dengan start_time. time.time() return timestamp dalam detik
    logger.info(f"Request completed in {computation_time:.2f}s")  # Log waktu komputasi

    return SolveResponse(  # Return response object (Pydantic akan validasi dan serialize ke JSON)
        ordered=ordered,  # List lokasi terurut
        total_distance_m=total_distance,  # Total jarak
        total_duration_s=total_duration,  # Total duration (bisa None)
        generations_run=res["generations_run"],  # Jumlah generasi GA yang dijalankan
        computation_time_s=computation_time,  # Waktu komputasi
        polyline=polyline  # Encoded polyline untuk map
    )

# Mount static files for UI
static_dir = os.path.join(os.path.dirname(BASE_DIR), "static")  # Membuat path ke folder static. os.path.dirname(BASE_DIR) naik 1 level dari BASE_DIR, lalu join dengan "static"
app.mount(  # Mount static files agar bisa diakses via HTTP
    "/static",  # URL prefix untuk static files (contoh: /static/index.html)
    StaticFiles(directory=static_dir),  # StaticFiles middleware yang serve files dari directory static_dir
    name="static"  # Nama untuk internal reference
)


@app.get("/ui")  # Endpoint GET /ui untuk serve halaman web UI
def serve_ui():  # Fungsi handler
    """Serve the web UI"""  # Docstring
    ui_path = os.path.join(os.path.dirname(BASE_DIR), "static", "index.html")  # Membuat absolute path ke file index.html
    return FileResponse(ui_path)  # Return file HTML sebagai response. FileResponse otomatis set correct content-type

if __name__ == "__main__":  # Cek jika file ini dijalankan langsung (bukan di-import). __name__ adalah variabel special Python
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)  # Jalankan uvicorn server. "app:app" artinya module app, object app. host="0.0.0.0" agar bisa diakses dari luar. port dari env var atau default 8000. reload=True untuk auto-restart saat code berubah (development mode)
