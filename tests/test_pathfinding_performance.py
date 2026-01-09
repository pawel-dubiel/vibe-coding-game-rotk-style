import pytest
import time
import random
from unittest.mock import MagicMock
from game.pathfinding import AStarPathFinder
from game.terrain import TerrainMap, TerrainType, TerrainFeature
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.config import USE_C_EXTENSIONS

class MockGameState:
    def __init__(self, width, height, terrain_map):
        self.board_width = width
        self.board_height = height
        self.terrain_map = terrain_map
        self.knights = []
        self.castles = []
        self.current_player = 0

    def get_knight_at(self, x, y):
        return None

def create_performance_map(width, height):
    """Create a large map with random obstacles for stress testing"""
    terrain_map = TerrainMap(width, height)
    random.seed(42) # Deterministic seed
    
    for y in range(height):
        for x in range(width):
            # 20% random obstacles (Mountains/Water)
            r = random.random()
            if r < 0.1:
                terrain_map.set_terrain(x, y, TerrainType.MOUNTAINS)
            elif r < 0.2:
                terrain_map.set_terrain(x, y, TerrainType.WATER)
            else:
                terrain_map.set_terrain(x, y, TerrainType.PLAINS)
                
    return terrain_map

def test_pathfinding_performance_comparison():
    """Benchmark C extension vs Python implementation"""
    
    # Setup large map
    width, height = 50, 50
    terrain_map = create_performance_map(width, height)
    game_state = MockGameState(width, height, terrain_map)
    
    unit = MagicMock(spec=Unit)
    unit.unit_class = KnightClass.WARRIOR
    unit.player_id = 1
    unit.get_behavior.return_value = None
    
    # Generate random paths to find
    num_paths = 50
    paths_to_find = []
    random.seed(123)
    
    for _ in range(num_paths):
        start = (random.randint(0, width//3), random.randint(0, height-1))
        end = (random.randint(2*width//3, width-1), random.randint(0, height-1))
        paths_to_find.append((start, end))
        
    # --- Benchmark Python Implementation ---
    pf_py = AStarPathFinder()
    pf_py._c_pathfinder = None # Force Python
    
    start_time = time.perf_counter()
    found_py = 0
    for start, end in paths_to_find:
        path = pf_py.find_path(start, end, game_state, unit=unit)
        if path: found_py += 1
    py_duration = time.perf_counter() - start_time
    
    # --- Benchmark C Implementation ---
    pf_c = AStarPathFinder()
    # Check if C extension is actually loaded
    if not pf_c._c_pathfinder:
        print("\nC extension not available, skipping comparison.")
        return

    start_time = time.perf_counter()
    found_c = 0
    for start, end in paths_to_find:
        path = pf_c.find_path(start, end, game_state, unit=unit)
        if path: found_c += 1
    c_duration = time.perf_counter() - start_time
    
    print(f"\n--- Pathfinding Performance (50x50 Map, {num_paths} paths) ---")
    print(f"Python: {py_duration:.4f}s ({found_py} paths found)")
    print(f"C Ext : {c_duration:.4f}s ({found_c} paths found)")
    
    if c_duration > 0:
        speedup = py_duration / c_duration
        print(f"Speedup: {speedup:.2f}x")
        
        # We expect significant speedup
        # Note: If C is slower, something is wrong, but we won't fail the test
        # strictly unless it's egregious or incorrect.
    
    # Functional parity check
    assert found_py == found_c, "Implementations found different number of paths!"

if __name__ == "__main__":
    test_pathfinding_performance_comparison()
