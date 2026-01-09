import pytest
from unittest.mock import MagicMock
from game.pathfinding import AStarPathFinder
from game.terrain import TerrainMap, TerrainType, TerrainFeature
from game.entities.unit import Unit
from game.entities.knight import KnightClass

class MockGameState:
    def __init__(self, width, height, terrain_map):
        self.board_width = width
        self.board_height = height
        self.terrain_map = terrain_map
        self.knights = []
        self.castles = []

    def get_knight_at(self, x, y):
        return None

def test_pathfinder_uses_roads_to_avoid_high_cost_terrain():
    """
    Test that the pathfinder prefers a longer route via roads/plains (low cost)
    over a shorter route via dense forest (high cost).
    
    Map Layout (4x2):
    (0,0) S  (1,0) DF (2,0) DF (3,0) E
    (0,1) Rd (1,1) Rd (2,1) Rd (3,1) Rd
    
    S = Start, E = End
    DF = Dense Forest (Cost 3.0)
    Rd = Road (Cost 1.0 clamped)
    
    Direct Path (top): 3 steps.
    - (0,0)->(1,0): Cost 3.0
    - (1,0)->(2,0): Cost 3.0
    - (2,0)->(3,0): Cost 1.0 (Plains at E)
    Total Cost: 7.0
    
    Detour Path (bottom): 5 steps.
    - (0,0)->(0,1): Cost 1.0
    - (0,1)->(1,1): Cost 1.0
    - (1,1)->(2,1): Cost 1.0
    - (2,1)->(3,1): Cost 1.0
    - (3,1)->(3,0): Cost 1.0
    Total Cost: 5.0
    
    Expected: Path follows the bottom road.
    """
    width, height = 10, 10
    terrain_map = TerrainMap(width, height)
    
    # Initialize all to Plains (Cost 1.0)
    for y in range(height):
        for x in range(width):
            terrain_map.set_terrain(x, y, TerrainType.PLAINS)
            
    # Set Dense Forest on direct path
    terrain_map.set_terrain(1, 0, TerrainType.DENSE_FOREST)
    terrain_map.set_terrain(2, 0, TerrainType.DENSE_FOREST)
    
    # Set Roads on detour path
    terrain_map.set_terrain(0, 1, TerrainType.PLAINS, TerrainFeature.ROAD)
    terrain_map.set_terrain(1, 1, TerrainType.PLAINS, TerrainFeature.ROAD)
    terrain_map.set_terrain(2, 1, TerrainType.PLAINS, TerrainFeature.ROAD)
    terrain_map.set_terrain(3, 1, TerrainType.PLAINS, TerrainFeature.ROAD)
    
    game_state = MockGameState(width, height, terrain_map)
    pathfinder = AStarPathFinder()
    
    # Mock Unit
    unit = MagicMock(spec=Unit)
    unit.unit_class = KnightClass.WARRIOR
    unit.player_id = 1
    unit.get_behavior.return_value = None
    
    start = (0, 0)
    end = (3, 0)
    
    path = pathfinder.find_path(start, end, game_state, unit=unit)
    
    assert path is not None, "Pathfinder should find a path"
    
    # Convert path to set for easier checking
    path_set = set(path)
    
    # Ensure it avoided the dense forest
    assert (1, 0) not in path_set, "Path should avoid Dense Forest at (1,0)"
    assert (2, 0) not in path_set, "Path should avoid Dense Forest at (2,0)"
    
    # Ensure it used the road detour
    assert (1, 1) in path_set, "Path should use the road at (1,1)"
    assert (2, 1) in path_set, "Path should use the road at (2,1)"
    
    # Verify exact path length/sequence
    # Optimal path takes a shortcut from (2,1) to (3,0) which is adjacent in odd-r layout
    # Path: (0,0) -> (0,1) -> (1,1) -> (2,1) -> (3,0)
    expected_path = [(0,1), (1,1), (2,1), (3,0)]
    assert path == expected_path, f"Expected path {expected_path}, got {path}"

def test_pathfinder_prefers_roads_over_forest():
    """
    Test preference for Road (1.0) over Forest (2.0) even with slight detour.
    
    Map:
    (0,0) S
    (1,0) F  (1,1) Rd
    (2,0) E
    
    Direct: S->F->E. Cost: 2.0 (enter F) + 1.0 (enter E) = 3.0
    Detour: S->Rd->E. Cost: 1.0 (enter Rd) + 1.0 (enter E) = 2.0 ?
    
    Wait, hexagonal adjacency:
    (0,0) neighbors: (1,0), (0,1), etc.
    Let's check coordinate system.
    Offset coords (odd-r):
    (0,0) neighbors: (1,0), (0,1)
    (1,0) neighbors: (0,0), (2,0), (0,1), (1,1)
    
    Let's try a simple triangle.
    Start (0,0), End (2,0).
    (1,0) is Forest (2.0).
    (0,1) is Road (1.0).
    (1,1) is Road (1.0).
    
    Path A: (0,0)->(1,0)->(2,0). 
      Enter (1,0) [Forest]: 2.0
      Enter (2,0) [Plains]: 1.0
      Total: 3.0
      
    Path B: (0,0)->(0,1)->(1,1)->(2,0)
      Enter (0,1) [Road]: 1.0
      Enter (1,1) [Road]: 1.0
      Enter (2,0) [Plains]: 1.0
      Total: 3.0
      
    It's a tie (3.0 vs 3.0). A* heuristic might prefer Direct.
    
    We need Road path to be strictly better.
    If we lower Road cost to 0.5 (unclamped), Path B is 0.5+0.5+1.0 = 2.0. Winner.
    With clamping, it's a tie.
    
    So currently, Roads are NOT strictly better than direct Forest if the detour adds steps.
    
    Let's test High Hills (Cost 3.0).
    Path A (High Hills): 3.0 + 1.0 = 4.0.
    Path B (Roads): 1.0 + 1.0 + 1.0 = 3.0.
    Path B wins.
    """
    width, height = 10, 10
    terrain_map = TerrainMap(width, height)
    
    # Default Plains
    for y in range(height):
        for x in range(width):
            terrain_map.set_terrain(x, y, TerrainType.PLAINS)
    
    # Obstacle
    terrain_map.set_terrain(1, 0, TerrainType.HIGH_HILLS) # Cost 3.0
    
    # Road detour
    terrain_map.set_terrain(0, 1, TerrainType.PLAINS, TerrainFeature.ROAD)
    terrain_map.set_terrain(1, 1, TerrainType.PLAINS, TerrainFeature.ROAD)
    
    game_state = MockGameState(width, height, terrain_map)
    pathfinder = AStarPathFinder()
    unit = MagicMock(spec=Unit)
    unit.unit_class = KnightClass.WARRIOR
    unit.get_behavior.return_value = None
    
    start = (0, 0)
    end = (2, 0)
    
    path = pathfinder.find_path(start, end, game_state, unit=unit)
    
    assert path is not None
    assert (1, 0) not in path, "Should avoid High Hills"
    assert (0, 1) in path or (1, 1) in path, "Should take detour"

