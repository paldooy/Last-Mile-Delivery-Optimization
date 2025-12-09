# ga.py
import random
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class GAConfig:
    """Configuration for Genetic Algorithm TSP solver"""
    def __init__(
        self, 
        pop_size: int = 200, 
        generations: int = 500, 
        crossover_rate: float = 0.9, 
        mutation_rate: float = 0.02, 
        elite_size: int = 5,  # Increased for better convergence
        tournament_k: int = 5,
        early_stop_threshold: Optional[int] = 50  # Stop if no improvement for N generations
    ):
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_k = tournament_k
        self.early_stop_threshold = early_stop_threshold

def route_distance(route: List[int], distance_matrix: List[List[float]]) -> float:
    """Calculate total distance for a route through the distance matrix"""
    if not route or len(route) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i+1]]
    return total

def initial_population(n_points: int, pop_size: int) -> List[List[int]]:
    pop = []
    base = list(range(n_points))
    for _ in range(pop_size):
        indy = base.copy()
        random.shuffle(indy)
        pop.append(indy)
    return pop

def fitness(route: List[int], distmat: List[List[float]]) -> float:
    # lower distance -> higher fitness
    d = route_distance(route, distmat)
    return 1.0 / (1.0 + d)

def tournament_selection(pop: List[List[int]], distmat: List[List[float]], k: int) -> List[int]:
    selected = random.sample(pop, k)
    selected_sorted = sorted(selected, key=lambda r: route_distance(r, distmat))
    return selected_sorted[0]

def ordered_crossover(parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
    size = len(parent1)
    a, b = sorted(random.sample(range(size), 2))
    def ox(p1, p2):
        child = [-1]*size
        child[a:b+1] = p1[a:b+1]
        pos = (b+1) % size
        p2pos = (b+1) % size
        while -1 in child:
            if p2[p2pos] not in child:
                child[pos] = p2[p2pos]
                pos = (pos + 1) % size
            p2pos = (p2pos + 1) % size
        return child
    return ox(parent1, parent2), ox(parent2, parent1)

def swap_mutation(route: List[int], mutation_rate: float) -> None:
    """Perform swap mutation with given probability"""
    for i in range(len(route)):
        if random.random() < mutation_rate:
            j = random.randrange(len(route))
            route[i], route[j] = route[j], route[i]

def inversion_mutation(route: List[int], mutation_rate: float) -> None:
    """Perform inversion mutation - reverse a random segment"""
    if random.random() < mutation_rate and len(route) > 2:
        a, b = sorted(random.sample(range(len(route)), 2))
        route[a:b+1] = reversed(route[a:b+1])

def solve_tsp(distance_matrix: List[List[float]], config: GAConfig = GAConfig()) -> dict:
    """
    Solve TSP using Genetic Algorithm
    
    Args:
        distance_matrix: NxN matrix of distances between points
        config: GA configuration parameters
        
    Returns:
        dict with 'route' (optimal order), 'distance' (total distance), 
        'generations_run' (actual generations executed)
    """
    n = len(distance_matrix)
    if n < 2:
        return {"route": list(range(n)), "distance": 0.0, "generations_run": 0}
    
    # Initialize population
    pop = initial_population(n, config.pop_size)
    best_route = None
    best_dist = float("inf")
    no_improvement_count = 0

    logger.info(f"Starting GA: {n} points, pop_size={config.pop_size}, generations={config.generations}")

    for gen in range(config.generations):
        # Evaluate and sort population
        pop_sorted = sorted(pop, key=lambda r: route_distance(r, distance_matrix))
        
        # Keep elite individuals
        next_pop = [route.copy() for route in pop_sorted[:config.elite_size]]
        
        # Update best solution
        cur_best = pop_sorted[0]
        cur_best_d = route_distance(cur_best, distance_matrix)
        
        if cur_best_d < best_dist:
            best_dist = cur_best_d
            best_route = cur_best.copy()
            no_improvement_count = 0
            if gen % 50 == 0:
                logger.info(f"Gen {gen}: New best distance = {best_dist:.2f}m")
        else:
            no_improvement_count += 1
        
        # Early stopping
        if config.early_stop_threshold and no_improvement_count >= config.early_stop_threshold:
            logger.info(f"Early stopping at generation {gen} (no improvement for {no_improvement_count} gens)")
            return {"route": best_route, "distance": best_dist, "generations_run": gen + 1}
        
        # Create next generation
        while len(next_pop) < config.pop_size:
            if random.random() < config.crossover_rate:
                p1 = tournament_selection(pop, distance_matrix, config.tournament_k)
                p2 = tournament_selection(pop, distance_matrix, config.tournament_k)
                c1, c2 = ordered_crossover(p1, p2)
                
                # Apply both mutation types with probability
                swap_mutation(c1, config.mutation_rate)
                inversion_mutation(c1, config.mutation_rate / 2)
                
                swap_mutation(c2, config.mutation_rate)
                inversion_mutation(c2, config.mutation_rate / 2)
                
                next_pop.append(c1)
                if len(next_pop) < config.pop_size:
                    next_pop.append(c2)
            else:
                # Reproduce with mutation
                p = tournament_selection(pop, distance_matrix, config.tournament_k).copy()
                swap_mutation(p, config.mutation_rate)
                inversion_mutation(p, config.mutation_rate / 2)
                next_pop.append(p)
        
        pop = next_pop
    
    logger.info(f"GA completed: Best distance = {best_dist:.2f}m")
    return {"route": best_route, "distance": best_dist, "generations_run": config.generations}
