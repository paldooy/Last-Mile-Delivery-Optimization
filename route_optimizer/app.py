# app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from geocode import parse_input_locations
from routing import build_distance_matrix, DEFAULT_OSRM_URL
from ga import solve_tsp, GAConfig
import uvicorn
import os
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Route Optimizer API",
    description="Optimize delivery routes using Genetic Algorithm, Nominatim Geocoding, and OSRM routing",
    version="1.0.0"
)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputLocation(BaseModel):
    address: Optional[str] = Field(None, description="Street address to geocode")
    lat: Optional[float] = Field(None, description="Latitude coordinate")
    lon: Optional[float] = Field(None, description="Longitude coordinate")
    label: Optional[str] = Field(None, description="Custom label for this location")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "Jl. Sudirman No. 1, Jakarta",
                "label": "Customer A"
            }
        }

class SolveRequest(BaseModel):
    locations: List[InputLocation] = Field(..., min_length=2, description="List of locations (min 2)")
    osrm_url: Optional[str] = Field(None, description="Custom OSRM server URL")
    use_duration: Optional[bool] = Field(False, description="Optimize by duration instead of distance")
    pop_size: Optional[int] = Field(200, ge=50, le=1000, description="GA population size")
    generations: Optional[int] = Field(300, ge=50, le=2000, description="GA generations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "locations": [
                    {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
                    {"lat": -6.2297, "lon": 106.8456, "label": "Point B"},
                    {"lat": -6.2297, "lon": 106.8206, "label": "Point C"}
                ],
                "pop_size": 200,
                "generations": 300
            }
        }

class SolveResponse(BaseModel):
    ordered: List[dict] = Field(..., description="Ordered list of locations")
    total_distance_m: float = Field(..., description="Total distance in meters")
    total_duration_s: Optional[float] = Field(None, description="Total duration in seconds")
    generations_run: int = Field(..., description="Number of GA generations executed")
    computation_time_s: float = Field(..., description="Computation time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ordered": [
                    {"index": 0, "label": "Point A", "lat": -6.2088, "lon": 106.8456},
                    {"index": 2, "label": "Point C", "lat": -6.2297, "lon": 106.8206},
                    {"index": 1, "label": "Point B", "lat": -6.2297, "lon": 106.8456}
                ],
                "total_distance_m": 5234.56,
                "total_duration_s": 720.5,
                "generations_run": 300,
                "computation_time_s": 1.23
            }
        }

@app.get("/")
def root():
    """API health check endpoint"""
    return {
        "message": "Route Optimizer API is running",
        "version": "1.0.0",
        "endpoints": {
            "solve": "/solve (POST)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
def health_check():
    """Health check for container orchestration"""
    return {"status": "healthy", "service": "route-optimizer"}

@app.post("/solve", response_model=SolveResponse)
def solve_endpoint(req: SolveRequest):
    """
    Solve the Traveling Salesman Problem for given locations.
    
    This endpoint accepts a list of locations (as addresses or coordinates),
    geocodes them if needed, calculates distances using OSRM or haversine,
    and finds the optimal route using a Genetic Algorithm.
    """
    start_time = time.time()
    logger.info(f"Received solve request with {len(req.locations)} locations")
    
    if not req.locations or len(req.locations) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Provide at least 2 locations"
        )

    # Parse and geocode locations
    try:
        locs = parse_input_locations([
            loc.dict(exclude_none=True) for loc in req.locations
        ])
        logger.info(f"Successfully parsed {len(locs)} locations")
    except ValueError as e:
        logger.error(f"Geocoding error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during geocoding: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing locations: {str(e)}"
        )

    # Build distance matrix
    osrm_url = req.osrm_url or os.getenv("OSRM_URL") or DEFAULT_OSRM_URL
    try:
        distances, durations = build_distance_matrix(
            locs, 
            osrm_url, 
            use_duration=req.use_duration
        )
        logger.info(f"Built distance matrix ({len(distances)}x{len(distances)})")
    except Exception as e:
        logger.error(f"Error building distance matrix: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating distances: {str(e)}"
        )

    # Solve TSP using Genetic Algorithm
    try:
        cfg = GAConfig(pop_size=req.pop_size, generations=req.generations)
        res = solve_tsp(distances, cfg)
        logger.info(f"GA solved in {res['generations_run']} generations")
    except Exception as e:
        logger.error(f"Error in GA solver: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error optimizing route: {str(e)}"
        )

    # Calculate total duration if available
    route_idx = res["route"]
    total_distance = res["distance"]
    total_duration = None
    
    if durations and req.use_duration:
        try:
            d = 0.0
            for i in range(len(route_idx) - 1):
                d += durations[route_idx[i]][route_idx[i+1]]
            total_duration = d
            logger.info(f"Total duration: {total_duration:.2f}s")
        except Exception as e:
            logger.warning(f"Could not calculate total duration: {str(e)}")

    # Build ordered response
    ordered = []
    for idx in route_idx:
        ordered.append({
            "index": idx,
            "label": locs[idx]["label"],
            "lat": locs[idx]["lat"],
            "lon": locs[idx]["lon"]
        })

    computation_time = time.time() - start_time
    logger.info(f"Request completed in {computation_time:.2f}s")

    return SolveResponse(
        ordered=ordered,
        total_distance_m=total_distance,
        total_duration_s=total_duration,
        generations_run=res["generations_run"],
        computation_time_s=computation_time
    )

# Mount static files for UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
def serve_ui():
    """Serve the web UI"""
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
