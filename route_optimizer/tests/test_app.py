# tests/test_app.py
from fastapi.testclient import TestClient
from app import app
from unittest.mock import patch

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_solve_insufficient_locations():
    """Test solve endpoint with insufficient locations"""
    payload = {
        "locations": [
            {"lat": -6.2088, "lon": 106.8456, "label": "Point A"}
        ]
    }
    
    response = client.post("/solve", json=payload)
    assert response.status_code == 400
    assert "at least 2 locations" in response.json()["detail"]

@patch('app.parse_input_locations')
@patch('app.build_distance_matrix')
@patch('app.solve_tsp')
def test_solve_success(mock_solve, mock_distance, mock_parse):
    """Test successful solve request"""
    # Mock geocoding
    mock_parse.return_value = [
        {"lat": -6.2088, "lon": 106.8456, "label": "A"},
        {"lat": -6.2297, "lon": 106.8206, "label": "B"},
        {"lat": -6.1751, "lon": 106.8650, "label": "C"}
    ]
    
    # Mock distance matrix
    mock_distance.return_value = (
        [[0, 100, 200], [100, 0, 150], [200, 150, 0]],
        None
    )
    
    # Mock GA solver
    mock_solve.return_value = {
        "route": [0, 2, 1],
        "distance": 350.0,
        "generations_run": 300
    }
    
    payload = {
        "locations": [
            {"lat": -6.2088, "lon": 106.8456, "label": "A"},
            {"lat": -6.2297, "lon": 106.8206, "label": "B"},
            {"lat": -6.1751, "lon": 106.8650, "label": "C"}
        ],
        "pop_size": 200,
        "generations": 300
    }
    
    response = client.post("/solve", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "ordered" in data
    assert "total_distance_m" in data
    assert "generations_run" in data
    assert "computation_time_s" in data
    assert len(data["ordered"]) == 3
    assert data["total_distance_m"] == 350.0

@patch('app.parse_input_locations')
def test_solve_geocoding_error(mock_parse):
    """Test solve with geocoding error"""
    mock_parse.side_effect = ValueError("Geocoding failed for address: Invalid")
    
    payload = {
        "locations": [
            {"address": "Invalid Address XYZ", "label": "Invalid"}
        ]
    }
    
    response = client.post("/solve", json=payload)
    assert response.status_code == 400
    assert "Geocoding failed" in response.json()["detail"]

def test_solve_validation_error():
    """Test solve with invalid parameters"""
    payload = {
        "locations": [
            {"lat": -6.2088, "lon": 106.8456},
            {"lat": -6.2297, "lon": 106.8206}
        ],
        "pop_size": 10,  # Too small (min 50)
        "generations": 300
    }
    
    response = client.post("/solve", json=payload)
    assert response.status_code == 422  # Validation error
