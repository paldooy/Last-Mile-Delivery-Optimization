# tests/test_routing.py
from routing import build_distance_matrix
from math import isclose

def test_haversine_fallback():
    # Two points far enough; force fallback by using invalid osrm url
    locs = [
        {"lat": -0.212, "lon": 117.139},
        {"lat": -0.220, "lon": 117.140}
    ]
    dists, durs = build_distance_matrix(locs, osrm_base_url="http://invalid-osrm:5000")
    assert len(dists) == 2
    assert len(dists[0]) == 2
    # diagonal zero
    assert dists[0][0] == 0
    assert dists[1][1] == 0
    # symmetric approximately
    assert isclose(dists[0][1], dists[1][0], rel_tol=1e-6)
    # positive distance
    assert dists[0][1] > 0
