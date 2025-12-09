# tests/test_ga.py
from ga import (
    solve_tsp, 
    GAConfig, 
    route_distance, 
    initial_population,
    tournament_selection,
    ordered_crossover,
    swap_mutation,
    inversion_mutation
)
import pytest

def make_simple_matrix(n):
    """Create a simple linear distance matrix for testing"""
    mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            mat[i][j] = abs(i - j) * 100.0
    return mat

def test_route_distance():
    """Test route distance calculation"""
    matrix = make_simple_matrix(4)
    route = [0, 1, 2, 3]
    # Distance should be 0->1 (100) + 1->2 (100) + 2->3 (100) = 300
    assert route_distance(route, matrix) == 300.0
    
def test_route_distance_empty():
    """Test route distance with empty route"""
    matrix = make_simple_matrix(4)
    assert route_distance([], matrix) == 0.0
    assert route_distance([1], matrix) == 0.0

def test_initial_population():
    """Test initial population generation"""
    n_points = 5
    pop_size = 10
    pop = initial_population(n_points, pop_size)
    
    assert len(pop) == pop_size
    assert all(len(route) == n_points for route in pop)
    assert all(set(route) == set(range(n_points)) for route in pop)

def test_tournament_selection():
    """Test tournament selection"""
    matrix = make_simple_matrix(5)
    pop = initial_population(5, 20)
    
    selected = tournament_selection(pop, matrix, k=5)
    assert len(selected) == 5
    assert set(selected) == set(range(5))

def test_ordered_crossover():
    """Test ordered crossover operation"""
    parent1 = [0, 1, 2, 3, 4]
    parent2 = [4, 3, 2, 1, 0]
    
    child1, child2 = ordered_crossover(parent1, parent2)
    
    # Children should be valid permutations
    assert set(child1) == set(range(5))
    assert set(child2) == set(range(5))
    assert len(child1) == 5
    assert len(child2) == 5

def test_swap_mutation():
    """Test swap mutation"""
    route = [0, 1, 2, 3, 4]
    original = route.copy()
    
    # With mutation rate 0, should not change
    swap_mutation(route, 0.0)
    assert route == original
    
    # With mutation rate 1.0, should likely change
    route = [0, 1, 2, 3, 4]
    swap_mutation(route, 1.0)
    assert set(route) == set(original)  # Still valid permutation

def test_inversion_mutation():
    """Test inversion mutation"""
    route = [0, 1, 2, 3, 4]
    original = route.copy()
    
    # Should maintain valid permutation
    inversion_mutation(route, 1.0)
    assert set(route) == set(original)

def test_ga_small():
    """Test GA with small problem"""
    mat = make_simple_matrix(5)
    cfg = GAConfig(pop_size=50, generations=100, mutation_rate=0.05)
    res = solve_tsp(mat, cfg)
    
    # Check result structure
    assert "route" in res
    assert "distance" in res
    assert "generations_run" in res
    
    # For linear metric, optimal is sequential order
    # Total distance should be close to 400 (0->1->2->3->4)
    assert res["distance"] <= 400.0 + 1e-6
    assert len(res["route"]) == 5
    assert set(res["route"]) == set(range(5))

def test_ga_medium():
    """Test GA with medium problem"""
    mat = make_simple_matrix(10)
    cfg = GAConfig(pop_size=100, generations=200)
    res = solve_tsp(mat, cfg)
    
    assert res["distance"] <= 900.0 + 1e-6  # 0->9 in sequence
    assert len(res["route"]) == 10

def test_ga_early_stopping():
    """Test GA early stopping mechanism"""
    mat = make_simple_matrix(5)
    cfg = GAConfig(
        pop_size=50, 
        generations=1000,
        early_stop_threshold=20
    )
    res = solve_tsp(mat, cfg)
    
    # Should stop before 1000 generations
    assert res["generations_run"] < 1000
    assert res["distance"] <= 400.0 + 1e-6

def test_ga_no_early_stopping():
    """Test GA without early stopping"""
    mat = make_simple_matrix(4)
    cfg = GAConfig(
        pop_size=30, 
        generations=50,
        early_stop_threshold=None
    )
    res = solve_tsp(mat, cfg)
    
    # Should run all generations
    assert res["generations_run"] == 50

def test_ga_single_point():
    """Test GA with single point (edge case)"""
    mat = [[0.0]]
    res = solve_tsp(mat)
    
    assert res["route"] == [0]
    assert res["distance"] == 0.0
    assert res["generations_run"] == 0

