# tests/test_utils.py
from utils import haversine
import math

def test_haversine_same_point():
    """Test haversine distance for same point"""
    coord = (-6.2088, 106.8456)
    distance = haversine(coord, coord)
    assert distance == 0.0

def test_haversine_known_distance():
    """Test haversine with known approximate distance"""
    # Jakarta to Bandung (approximately 150km)
    jakarta = (-6.2088, 106.8456)
    bandung = (-6.9175, 107.6191)
    
    distance = haversine(jakarta, bandung)
    
    # Should be roughly 120-180 km
    assert 120_000 < distance < 180_000

def test_haversine_small_distance():
    """Test haversine with small distance"""
    point1 = (-6.2088, 106.8456)
    point2 = (-6.2089, 106.8457)
    
    distance = haversine(point1, point2)
    
    # Should be very small (< 200m)
    assert 0 < distance < 200

def test_haversine_symmetry():
    """Test haversine distance symmetry"""
    point1 = (-6.2088, 106.8456)
    point2 = (-6.2297, 106.8206)
    
    d1 = haversine(point1, point2)
    d2 = haversine(point2, point1)
    
    assert abs(d1 - d2) < 0.001  # Should be equal (within floating point error)

def test_haversine_equator():
    """Test haversine along equator"""
    # 1 degree longitude at equator ≈ 111 km
    point1 = (0.0, 0.0)
    point2 = (0.0, 1.0)
    
    distance = haversine(point1, point2)
    
    # Should be approximately 111 km
    assert 110_000 < distance < 112_000
