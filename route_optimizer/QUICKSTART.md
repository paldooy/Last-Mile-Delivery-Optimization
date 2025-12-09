# 🚀 Quick Start Guide

## Installation

```bash
# Clone or navigate to project
cd route_optimizer

# Install dependencies
pip install -r requirements.txt
```

## Running Locally

```bash
# Option 1: Using Python directly
python app.py

# Option 2: Using uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t route-optimizer .
docker run -d -p 8000:8000 route-optimizer
```

## Testing the API

```bash
# Check if server is running
curl http://localhost:8000/health

# Test with sample data
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"lat": -6.2088, "lon": 106.8456, "label": "A"},
      {"lat": -6.2297, "lon": 106.8206, "label": "B"},
      {"lat": -6.1751, "lon": 106.8650, "label": "C"}
    ],
    "pop_size": 200,
    "generations": 300
  }'
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ga.py -v
```

## Access Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:
- `OSRM_URL`: OSRM server URL (default: http://localhost:5000)
- `PORT`: Server port (default: 8000)
- `ROUTE_CACHE_DIR`: Cache directory (default: ./.cache)

## Next Steps

1. See `README.md` for detailed documentation
2. Check `examples/API_EXAMPLES.md` for usage examples
3. Modify GA parameters in requests to optimize for your use case
