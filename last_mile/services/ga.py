# ga.py - Implementasi Genetic Algorithm untuk menyelesaikan Traveling Salesman Problem (TSP)
import random  # Library untuk random number generation (shuffle, sample, etc)
import numpy as np  # NumPy untuk operasi array (tidak digunakan di file ini, bisa dihapus)
from typing import List, Tuple, Optional  # Type hints
import logging  # Untuk logging

logger = logging.getLogger(__name__)  # Create logger instance

class GAConfig:  # Configuration class untuk menyimpan parameter Genetic Algorithm
    """Configuration for Genetic Algorithm TSP solver"""  # Docstring
    def __init__(  # Constructor method, dipanggil saat create instance GAConfig()
        self,  # self adalah reference ke instance object (required di semua instance methods)
        pop_size: int = 200,  # Ukuran populasi (jumlah individu/solusi dalam satu generasi), default 200
        generations: int = 500,  # Jumlah generasi/iterasi GA, default 500
        crossover_rate: float = 0.9,  # Probabilitas crossover (0.9 = 90% chance), default 0.9
        mutation_rate: float = 0.02,  # Probabilitas mutation per gene (0.02 = 2%), default 0.02
        elite_size: int = 5,  # Jumlah individu terbaik yang otomatis masuk generasi berikutnya (elitism), default 5
        tournament_k: int = 5,  # Ukuran tournament untuk tournament selection (ambil k individu random, pilih yang terbaik), default 5
        early_stop_threshold: Optional[int] = 50  # Stop early jika tidak ada improvement selama N generasi (None = disable early stopping), default 50
    ):
        self.pop_size = pop_size  # Set instance variable pop_size dengan parameter pop_size. self.pop_size bisa diakses dari luar class
        self.generations = generations  # Set instance variable
        self.crossover_rate = crossover_rate  # Set instance variable
        self.mutation_rate = mutation_rate  # Set instance variable
        self.elite_size = elite_size  # Set instance variable
        self.tournament_k = tournament_k  # Set instance variable
        self.early_stop_threshold = early_stop_threshold  # Set instance variable

def route_distance(route: List[int], distance_matrix: List[List[float]]) -> float:  # Fungsi untuk menghitung total jarak dari sebuah route
    """  
    Calculate total distance for a route through the distance matrix.
    
    Args:
        route: List index lokasi dalam urutan kunjungan, contoh [2, 0, 3, 1] artinya kunjungi lokasi 2 -> 0 -> 3 -> 1
        distance_matrix: 2D array jarak antar lokasi, distance_matrix[i][j] adalah jarak dari lokasi i ke j
    
    Returns:
        Total distance dalam meter
    """
    if not route or len(route) < 2:  # Validasi: jika route kosong atau hanya 1 lokasi
        return 0.0  # Return 0 karena tidak ada perjalanan
    
    total = 0.0  # Inisialisasi total distance dengan 0.0
    for i in range(len(route) - 1):  # Loop dari index 0 hingga n-2 (karena kita akses i dan i+1)
        total += distance_matrix[route[i]][route[i+1]]  # Tambahkan jarak dari lokasi route[i] ke route[i+1]
    return total  # Return total distance

def initial_population(n_points: int, pop_size: int) -> List[List[int]]:  # Fungsi untuk generate populasi awal (random solutions)
    """
    Generate populasi awal dengan permutasi random.
    
    Args:
        n_points: Jumlah lokasi/points
        pop_size: Ukuran populasi yang ingin di-generate
    
    Returns:
        List of routes (setiap route adalah list index lokasi)
    """
    pop = []  # Inisialisasi list populasi kosong
    base = list(range(n_points))  # Create list [0, 1, 2, ..., n-1]. range(5) = [0,1,2,3,4]
    for _ in range(pop_size):  # Loop sebanyak pop_size kali. Underscore _ artinya kita tidak pakai loop variable
        indy = base.copy()  # Copy base list. .copy() membuat shallow copy agar perubahan di indy tidak affect base
        random.shuffle(indy)  # Shuffle list secara random in-place (mengubah list indy langsung). Ini membuat random permutation
        pop.append(indy)  # Append individu (route) ke populasi
    return pop  # Return populasi

def fitness(route: List[int], distmat: List[List[float]]) -> float:  # Fungsi untuk menghitung fitness value dari route
    """
    Calculate fitness value. Lower distance = higher fitness.
    Fitness digunakan untuk ranking/selection individu.
    """
    # lower distance -> higher fitness
    d = route_distance(route, distmat)  # Hitung distance route
    return 1.0 / (1.0 + d)  # Return fitness = 1/(1+distance). Semakin kecil distance, semakin besar fitness. +1 untuk avoid division by zero

def tournament_selection(pop: List[List[int]], distmat: List[List[float]], k: int) -> List[int]:  # Tournament selection: pilih k individu random, return yang terbaik
    """
    Tournament selection untuk memilih parent.
    Ambil k individu secara random, lalu return individu dengan distance terkecil.
    Metode ini balance antara exploration dan exploitation.
    
    Args:
        pop: Populasi (list of routes)
        distmat: Distance matrix
        k: Tournament size (jumlah individu yang compete)
    
    Returns:
        Route terbaik dari tournament
    """
    selected = random.sample(pop, k)  # Ambil k individu random dari populasi. random.sample(list, k) return list k elemen random tanpa duplikat
    selected_sorted = sorted(selected, key=lambda r: route_distance(r, distmat))  # Sort selected routes by distance. lambda adalah anonymous function, lambda r: route_distance(r, distmat) artinya fungsi yang terima r dan return route_distance(r, distmat). sorted() dengan key akan sort berdasarkan hasil key function
    return selected_sorted[0]  # Return individu terbaik (index 0 setelah sort ascending)

def ordered_crossover(parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:  # Ordered Crossover (OX) operator untuk TSP. Return 2 children
    """
    Ordered Crossover (OX) untuk TSP.
    Metode crossover khusus untuk permutation problems yang menjaga validitas route (no duplicate cities).
    
    Cara kerja:
    1. Pilih random segment dari parent1 (index a hingga b)
    2. Copy segment tersebut ke child di posisi yang sama
    3. Fill sisa posisi dengan elemen dari parent2 secara berurutan, skip yang sudah ada
    
    Example:
    parent1 = [1,2,3,4,5], parent2 = [3,4,1,5,2], segment a=1, b=3
    child segment = [_,2,3,4,_]
    fill dari parent2 starting after b: [3,4,1,5,2] -> skip 3,4 -> fill 1,5,2 -> [1,2,3,4,5]
    
    Returns:
        Tuple of (child1, child2)
    """
    size = len(parent1)  # Ukuran route (jumlah lokasi)
    a, b = sorted(random.sample(range(size), 2))  # Pilih 2 index random lalu sort. random.sample(range(5), 2) bisa return [3,1], sorted([3,1]) = [1,3]. Ini adalah segment boundaries
    def ox(p1, p2):  # Inner function untuk melakukan OX dari p1 dan p2. Inner function bisa akses variable outer function (size, a, b)
        """
        Perform ordered crossover dari parent p1 dan p2.
        """
        child = [-1]*size  # Inisialisasi child dengan -1 (marker untuk empty slot). [-1]*5 = [-1,-1,-1,-1,-1]
        child[a:b+1] = p1[a:b+1]  # Copy segment dari parent1 ke child. Slice notation [a:b+1] ambil elemen dari index a hingga b (inclusive). +1 karena slice end is exclusive
        pos = (b+1) % size  # Posisi untuk mulai fill di child. (b+1) % size untuk wrap around (circular). % adalah modulo operator, 6 % 5 = 1
        p2pos = (b+1) % size  # Posisi untuk mulai baca dari parent2
        while -1 in child:  # Loop selama masih ada empty slot (-1) di child. 'in' operator check if value exists in list
            if p2[p2pos] not in child:  # Cek jika elemen dari parent2 belum ada di child. 'not in' adalah negasi dari 'in'
                child[pos] = p2[p2pos]  # Fill child di posisi pos dengan elemen dari parent2
                pos = (pos + 1) % size  # Move ke posisi berikutnya dengan wrap around
            p2pos = (p2pos + 1) % size  # Move ke elemen berikutnya di parent2
        return child  # Return child route
    return ox(parent1, parent2), ox(parent2, parent1)  # Return 2 children: ox(p1,p2) dan ox(p2,p1). Dengan swap parent, kita dapat 2 children berbeda

def swap_mutation(route: List[int], mutation_rate: float) -> None:  # Swap mutation: tukar posisi 2 elemen random. Modifies route in-place (return None)
    """
    Perform swap mutation dengan probabilitas mutation_rate.
    Untuk setiap posisi dalam route, dengan probabilitas mutation_rate, tukar dengan posisi random lainnya.
    
    Example: [1,2,3,4,5] -> swap index 1 dan 3 -> [1,4,3,2,5]
    
    Args:
        route: Route yang akan di-mutate (diubah in-place)
        mutation_rate: Probabilitas mutation per posisi (0.02 = 2% chance per posisi)
    """
    for i in range(len(route)):  # Loop setiap posisi dalam route
        if random.random() < mutation_rate:  # random.random() return float random antara 0.0 dan 1.0. Jika < mutation_rate, lakukan mutation
            j = random.randrange(len(route))  # Pilih posisi random j. random.randrange(5) return random int antara 0-4
            route[i], route[j] = route[j], route[i]  # Swap elemen di posisi i dan j. Python tuple unpacking: a,b = b,a untuk swap values

def inversion_mutation(route: List[int], mutation_rate: float) -> None:  # Inversion mutation: reverse segment random. Modifies in-place
    """
    Perform inversion mutation - reverse random segment dari route.
    Dengan probabilitas mutation_rate, pilih segment random dan reverse urutannya.
    
    Example: [1,2,3,4,5], segment [1:3] -> [1,4,3,2,5] (reversed segment 2,3,4)
    
    Inversion mutation sering lebih efektif untuk TSP karena mempertahankan struktur relative positions.
    
    Args:
        route: Route yang akan di-mutate (diubah in-place)
        mutation_rate: Probabilitas mutation
    """
    if random.random() < mutation_rate and len(route) > 2:  # Cek probabilitas dan minimal 3 elemen (tidak bisa inverse jika ≤2 elemen)
        a, b = sorted(random.sample(range(len(route)), 2))  # Pilih 2 index random sebagai segment boundaries
        route[a:b+1] = reversed(route[a:b+1])  # Reverse segment. reversed() return iterator, assigned ke slice akan convert ke list dan replace segment

def solve_tsp(distance_matrix: List[List[float]], config: GAConfig = GAConfig()) -> dict:  # Fungsi utama untuk solve TSP menggunakan Genetic Algorithm. GAConfig() adalah default value (create new instance jika tidak di-provide)
    """
    Solve TSP using Genetic Algorithm
    
    Args:
        distance_matrix: NxN matrix of distances between points
        config: GA configuration parameters
        
    Returns:
        dict with 'route' (optimal order), 'distance' (total distance), 
        'generations_run' (actual generations executed)
    """
    n = len(distance_matrix)  # Jumlah lokasi
    if n < 2:  # Validasi: jika kurang dari 2 lokasi
        return {"route": list(range(n)), "distance": 0.0, "generations_run": 0}  # Return trivial solution. list(range(1)) = [0]
    
    # Initialize population
    pop = initial_population(n, config.pop_size)  # Generate populasi awal dengan random permutations
    best_route = None  # Variable untuk track best route sepanjang evolusi
    best_dist = float("inf")  # Initialize best distance dengan infinity (nilai sangat besar). float("inf") adalah positive infinity
    no_improvement_count = 0  # Counter untuk track berapa generasi tanpa improvement (untuk early stopping)

    logger.info(f"Starting GA: {n} points, pop_size={config.pop_size}, generations={config.generations}")  # Log start GA dengan parameters

    for gen in range(config.generations):  # Main GA loop: iterasi untuk setiap generasi
        # Evaluate and sort population
        pop_sorted = sorted(pop, key=lambda r: route_distance(r, distance_matrix))  # Sort populasi berdasarkan distance (ascending). Lambda function untuk get distance sebagai sort key
        
        # Keep elite individuals
        next_pop = [route.copy() for route in pop_sorted[:config.elite_size]]  # Elitism: ambil elite_size individu terbaik dan copy ke generasi berikutnya. List comprehension dengan slice [:5] ambil 5 pertama. .copy() agar perubahan tidak affect original
        
        # Update best solution
        cur_best = pop_sorted[0]  # Individu terbaik generasi ini (index 0 setelah sort)
        cur_best_d = route_distance(cur_best, distance_matrix)  # Distance dari best current
        
        if cur_best_d < best_dist:  # Jika current best lebih baik dari best overall
            best_dist = cur_best_d  # Update best distance
            best_route = cur_best.copy()  # Update best route (copy agar tidak terubah)
            no_improvement_count = 0  # Reset counter karena ada improvement
            if gen % 50 == 0:  # Setiap 50 generasi (modulo operator, gen % 50 == 0 artinya gen habis dibagi 50: 0, 50, 100, 150, ...)
                logger.info(f"Gen {gen}: New best distance = {best_dist:.2f}m")  # Log improvement. :.2f format float dengan 2 desimal
        else:  # Jika tidak ada improvement
            no_improvement_count += 1  # Increment counter. += adalah shorthand untuk no_improvement_count = no_improvement_count + 1
        
        # Early stopping
        if config.early_stop_threshold and no_improvement_count >= config.early_stop_threshold:  # Cek jika early stopping enabled (not None) dan counter >= threshold
            logger.info(f"Early stopping at generation {gen} (no improvement for {no_improvement_count} gens)")  # Log early stop
            return {"route": best_route, "distance": best_dist, "generations_run": gen + 1}  # Return result. gen + 1 karena gen start dari 0
        
        # Create next generation
        while len(next_pop) < config.pop_size:  # Loop sampai next_pop penuh (ukuran = pop_size). while loop terus jalan selama kondisi True
            if random.random() < config.crossover_rate:  # Dengan probabilitas crossover_rate, lakukan crossover
                p1 = tournament_selection(pop, distance_matrix, config.tournament_k)  # Select parent 1 menggunakan tournament
                p2 = tournament_selection(pop, distance_matrix, config.tournament_k)  # Select parent 2 menggunakan tournament
                c1, c2 = ordered_crossover(p1, p2)  # Crossover untuk generate 2 children. Tuple unpacking untuk assign ke c1 dan c2
                
                # Apply both mutation types with probability
                swap_mutation(c1, config.mutation_rate)  # Apply swap mutation ke child 1 (modifies in-place)
                inversion_mutation(c1, config.mutation_rate / 2)  # Apply inversion mutation dengan rate setengah (/ 2). Inversion mutation lebih disruptive jadi rate lebih kecil
                
                swap_mutation(c2, config.mutation_rate)  # Apply mutations ke child 2
                inversion_mutation(c2, config.mutation_rate / 2)
                
                next_pop.append(c1)  # Tambahkan child 1 ke next generation
                if len(next_pop) < config.pop_size:  # Cek jika masih ada space (untuk avoid exceed pop_size)
                    next_pop.append(c2)  # Tambahkan child 2
            else:  # Jika tidak crossover (probabilitas 1 - crossover_rate)
                # Reproduce with mutation
                p = tournament_selection(pop, distance_matrix, config.tournament_k).copy()  # Select 1 parent dan copy (agar mutation tidak affect original)
                swap_mutation(p, config.mutation_rate)  # Apply mutation
                inversion_mutation(p, config.mutation_rate / 2)
                next_pop.append(p)  # Tambahkan mutated parent ke next generation
        
        pop = next_pop  # Replace populasi lama dengan next generation untuk iterasi berikutnya
    
    logger.info(f"GA completed: Best distance = {best_dist:.2f}m")
    return {"route": best_route, "distance": best_dist, "generations_run": config.generations}


def solve_tsp_with_fixed_points(  # Fungsi untuk solve TSP dengan titik start dan/atau end yang fixed
    distance_matrix: List[List[float]],  # Distance matrix
    config: GAConfig = GAConfig(),  # GA config, default new instance
    start_idx: Optional[int] = None,  # Index lokasi start yang fixed (None = any start)
    end_idx: Optional[int] = None  # Index lokasi end yang fixed (None = any end)
) -> dict:  # Return dict dengan route, distance, generations_run
    """
    Solve TSP with fixed start and/or end points using Genetic Algorithm.
    
    Strategi: Hanya optimize urutan middle points (yang bukan start/end),
    lalu construct full route dengan start/end di posisi tetap.
    
    Args:
        distance_matrix: NxN matrix of distances between points
        config: GA configuration parameters
        start_idx: Index of the fixed start point (None = any start)
        end_idx: Index of the fixed end point (None = any end)
        
    Returns:
        dict with 'route' (optimal order), 'distance' (total distance), 
        'generations_run' (actual generations executed)
    """
    n = len(distance_matrix)  # Jumlah total lokasi
    if n < 2:  # Validasi
        return {"route": list(range(n)), "distance": 0.0, "generations_run": 0}  # Return trivial solution
    
    # Get indices of points that can be shuffled
    fixed_indices = set()  # Set untuk menyimpan index yang fixed. Set adalah collection tanpa duplikat, {} untuk empty set atau set([1,2,3])
    if start_idx is not None:  # Jika start_idx di-provide
        fixed_indices.add(start_idx)  # Tambahkan ke set. set.add() menambahkan element ke set
    if end_idx is not None:  # Jika end_idx di-provide
        fixed_indices.add(end_idx)  # Tambahkan ke set
    
    middle_indices = [i for i in range(n) if i not in fixed_indices]  # List comprehension: ambil semua index yang bukan fixed. 'i not in fixed_indices' adalah filter condition
    
    # If only 2 points and both are fixed, return directly
    if len(middle_indices) == 0:  # Jika tidak ada middle points (semua fixed)
        if start_idx is not None and end_idx is not None:  # Jika ada start dan end
            return {  # Return direct route dari start ke end
                "route": [start_idx, end_idx],  # Route hanya 2 lokasi
                "distance": distance_matrix[start_idx][end_idx],  # Distance langsung dari start ke end
                "generations_run": 0  # 0 karena tidak perlu optimize
            }
        else:  # Jika hanya 1 lokasi fixed atau tidak ada middle
            return {  # Return sequential route
                "route": list(range(n)),  # Route [0,1,2,...,n-1]
                "distance": sum(distance_matrix[i][i+1] for i in range(n-1)),  # Sum distance. Generator expression dengan sum(): sum(x for x in iterable)
                "generations_run": 0  # 0 karena trivial
            }
    
    def build_route(middle_perm):  # Inner function untuk construct full route dari middle permutation
        """Build full route from middle permutation"""
        route = []  # Inisialisasi list kosong
        if start_idx is not None:  # Jika ada start fixed
            route.append(start_idx)  # Tambahkan start di awal route
        route.extend(middle_perm)  # Tambahkan middle points. list.extend() menambahkan semua elemen dari iterable. extend([1,2,3]) berbeda dengan append([1,2,3]): extend menambahkan 3 elemen, append menambahkan 1 elemen (list)
        if end_idx is not None:  # Jika ada end fixed
            route.append(end_idx)  # Tambahkan end di akhir route
        return route  # Return full route
    
    def route_distance_fixed(middle_perm):  # Inner function untuk calculate distance dari middle permutation
        """Calculate distance for a permutation of middle points"""
        route = build_route(middle_perm)  # Build full route dari middle perm
        return route_distance(route, distance_matrix)  # Calculate distance menggunakan fungsi route_distance
    
    # Initialize population with random permutations of middle points
    pop = []  # Inisialisasi populasi kosong
    for _ in range(config.pop_size):  # Loop sebanyak pop_size
        middle_perm = middle_indices.copy()  # Copy middle_indices. Ini adalah list index middle points
        random.shuffle(middle_perm)  # Shuffle untuk create random permutation
        pop.append(middle_perm)  # Tambahkan ke populasi. Note: populasi berisi permutations dari middle points saja, bukan full routes
    
    best_route = None  # Track best route (full route dengan start/end)
    best_dist = float("inf")  # Track best distance
    no_improvement_count = 0  # Counter untuk early stopping

    logger.info(f"Starting GA with fixed points: start={start_idx}, end={end_idx}, middle={len(middle_indices)} points")  # Log start dengan info fixed points

    for gen in range(config.generations):  # Main GA loop
        # Evaluate and sort population
        pop_sorted = sorted(pop, key=lambda r: route_distance_fixed(r))  # Sort populasi by distance. Key function route_distance_fixed akan build full route dan calculate distance
        
        # Keep elite individuals
        next_pop = [route.copy() for route in pop_sorted[:config.elite_size]]  # Elitism: copy best middle perms
        
        # Update best solution
        cur_best = pop_sorted[0]  # Best middle perm generasi ini
        cur_best_d = route_distance_fixed(cur_best)  # Distance dari best
        
        if cur_best_d < best_dist:  # Jika ada improvement
            best_dist = cur_best_d  # Update best distance
            best_route = build_route(cur_best.copy())  # Build dan save full route. Ini adalah best_route overall
            no_improvement_count = 0  # Reset counter
            if gen % 50 == 0:  # Log setiap 50 generasi
                logger.info(f"Gen {gen}: New best distance = {best_dist:.2f}m")
        else:  # No improvement
            no_improvement_count += 1  # Increment counter
        
        # Early stopping
        if config.early_stop_threshold and no_improvement_count >= config.early_stop_threshold:  # Cek early stopping condition
            logger.info(f"Early stopping at generation {gen} (no improvement for {no_improvement_count} gens)")  # Log early stop
            return {"route": best_route, "distance": best_dist, "generations_run": gen + 1}  # Return result dengan generations_run = gen + 1
        
        # Create next generation
        while len(next_pop) < config.pop_size:  # Loop sampai next_pop penuh
            if random.random() < config.crossover_rate and len(middle_indices) > 1:  # Crossover jika probabilitas terpenuhi dan ada >1 middle point. Tidak bisa crossover jika hanya 1 middle point
                p1_idx = random.randint(0, min(config.tournament_k, len(pop)) - 1)  # Pilih random index dari top-k sorted population. random.randint(a,b) return random int antara a dan b (inclusive). min() untuk handle case jika pop < tournament_k
                p2_idx = random.randint(0, min(config.tournament_k, len(pop)) - 1)  # Pilih index parent 2
                p1 = pop_sorted[p1_idx]  # Ambil parent 1 dari sorted population (simplified tournament)
                p2 = pop_sorted[p2_idx]  # Ambil parent 2
                c1, c2 = ordered_crossover(p1, p2)  # Crossover middle perms. ordered_crossover tetap valid untuk middle perms karena tetap permutation problem
                
                # Apply mutations
                swap_mutation(c1, config.mutation_rate)  # Mutate child 1
                inversion_mutation(c1, config.mutation_rate / 2)  # Inversion mutation dengan rate lebih rendah
                
                swap_mutation(c2, config.mutation_rate)  # Mutate child 2
                inversion_mutation(c2, config.mutation_rate / 2)
                
                next_pop.append(c1)  # Tambahkan child 1
                if len(next_pop) < config.pop_size:  # Cek space
                    next_pop.append(c2)  # Tambahkan child 2
            else:  # Jika tidak crossover
                # Reproduce with mutation
                p_idx = random.randint(0, min(config.tournament_k, len(pop)) - 1)  # Pilih random parent index dari top-k
                p = pop_sorted[p_idx].copy()  # Copy parent
                swap_mutation(p, config.mutation_rate)  # Mutate
                inversion_mutation(p, config.mutation_rate / 2)
                next_pop.append(p)  # Tambahkan ke next generation  # Tambahkan mutated parent ke next generation
        
        pop = next_pop  # Replace populasi lama dengan next generation untuk iterasi berikutnya
    
    logger.info(f"GA completed: Best distance = {best_dist:.2f}m")  # Log completion setelah semua generasi selesai
    return {"route": best_route, "distance": best_dist, "generations_run": config.generations}  # Return dict dengan best solution. generations_run = config.generations karena loop selesai tanpa early stop
