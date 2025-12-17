# tests/test_geocode.py
from last_mile.services.geocode import geocode_address, parse_input_locations
from unittest.mock import patch, MagicMock
import pytest

def test_parse_input_locations_with_coords():
    """Test parsing locations with coordinates"""
    items = [
        {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
        {"lat": -6.2297, "lon": 106.8206, "label": "Point B"}
    ]
    
    result = parse_input_locations(items)
    
    assert len(result) == 2
    assert result[0]["lat"] == -6.2088
    assert result[0]["lon"] == 106.8456
    assert result[0]["label"] == "Point A"

def test_parse_input_locations_without_label():
    """Test parsing locations without labels"""
    items = [
        {"lat": -6.2088, "lon": 106.8456},
        {"lat": -6.2297, "lon": 106.8206}
    ]
    
    result = parse_input_locations(items)
    
    assert len(result) == 2
    assert result[0]["label"] == "pt_0"
    assert result[1]["label"] == "pt_1"

def test_parse_input_locations_invalid():
    """Test parsing invalid locations"""
    items = [{"invalid": "data"}]
    
    with pytest.raises(ValueError, match="must contain 'address' or 'lat' & 'lon'"):
        parse_input_locations(items)

def test_parse_input_locations_mixed():
    """Test parsing mixed address and coordinates"""
    with patch('last_mile.services.geocode.geocode_address') as mock_geocode:
        mock_geocode.return_value = (-6.175, 106.827)
        
        items = [
            {"lat": -6.2088, "lon": 106.8456, "label": "Point A"},
            {"address": "Jakarta", "label": "Jakarta Center"}
        ]
        
        result = parse_input_locations(items)
        
        assert len(result) == 2
        assert result[0]["label"] == "Point A"
        assert result[1]["label"] == "Jakarta Center"
        assert result[1]["lat"] == -6.175

@patch('geocode.requests.get')
@patch('geocode.cache_get')
@patch('geocode.cache_set')
def test_geocode_address_success(mock_cache_set, mock_cache_get, mock_requests):
    """Test successful geocoding"""
    mock_cache_get.return_value = None
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "lat": "-6.2088",
        "lon": "106.8456"
    }]
    mock_requests.return_value = mock_response
    
    result = geocode_address("Jakarta", rate_limit_sleep=0)
    
    assert result == (-6.2088, 106.8456)
    mock_cache_set.assert_called_once()

@patch('geocode.requests.get')
@patch('geocode.cache_get')
def test_geocode_address_cache_hit(mock_cache_get, mock_requests):
    """Test geocoding with cache hit"""
    mock_cache_get.return_value = {"lat": -6.2088, "lon": 106.8456}
    
    result = geocode_address("Jakarta")
    
    assert result == (-6.2088, 106.8456)
    mock_requests.assert_not_called()

@patch('geocode.requests.get')
@patch('geocode.cache_get')
def test_geocode_address_not_found(mock_cache_get, mock_requests):
    """Test geocoding with no results"""
    mock_cache_get.return_value = None
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_requests.return_value = mock_response
    
    result = geocode_address("Invalid Address XYZ", rate_limit_sleep=0, retries=1)
    
    assert result is None

@patch('geocode.requests.get')
@patch('geocode.cache_get')
def test_geocode_address_timeout_retry(mock_cache_get, mock_requests):
    """Test geocoding with timeout and retry"""
    mock_cache_get.return_value = None
    mock_requests.side_effect = [
        Exception("Timeout"),
        MagicMock(status_code=200, json=lambda: [{"lat": "-6.2", "lon": "106.8"}])
    ]
    
    result = geocode_address("Jakarta", rate_limit_sleep=0, retries=2)
    
    assert result == (-6.2, 106.8)
    assert mock_requests.call_count == 2
