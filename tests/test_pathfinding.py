"""Tests for pathfinding implementations"""
import unittest
from game.pathfinding import PathFinder, AStarPathFinder, DijkstraPathFinder
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.terrain import TerrainType, TerrainMap


class TestPathfinding(unittest.TestCase):
    """Test pathfinding algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_state = MockGameState(board_width=10, board_height=10)
        
        # Create test unit
        self.unit = Unit(name="Test Unit", unit_class=KnightClass.WARRIOR, x=0, y=0)
        self.unit.player_id = 1
        self.unit.action_points = 10
        
    def test_astar_finds_direct_path(self):
        """Test A* finds direct path on clear terrain"""
        pathfinder = AStarPathFinder()
        
        # Find path from (0,0) to (3,0)
        path = pathfinder.find_path(
            start=(0, 0),
            end=(3, 0),
            game_state=self.game_state,
            unit=self.unit
        )
        
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3)  # Three steps in hex grid
        self.assertEqual(path[-1], (3, 0))
        
    def test_astar_avoids_obstacles(self):
        """Test A* pathfinding around impassable terrain"""
        pathfinder = AStarPathFinder()
        
        # Create obstacle at (1,0)
        from game.terrain import Terrain
        self.game_state.terrain_map.terrain_grid[0][1] = Terrain(TerrainType.WATER)
        
        # Find path from (0,0) to (2,0)
        path = pathfinder.find_path(
            start=(0, 0),
            end=(2, 0),
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert path is not None
        assert (1, 0) not in path  # Should avoid mountain
        assert path[-1] == (2, 0)
        
    def test_astar_respects_max_cost(self):
        """Test A* respects maximum cost limit"""
        pathfinder = AStarPathFinder()
        
        # Set all terrain to forest (cost 2)
        from game.terrain import Terrain
        for y in range(10):
            for x in range(10):
                self.game_state.terrain_map.terrain_grid[y][x] = Terrain(TerrainType.FOREST)
        
        # Try to find path with limited cost
        path = pathfinder.find_path(
            start=(0, 0),
            end=(5, 0),
            game_state=self.game_state,
            unit=self.unit,
            max_cost=5  # Not enough to reach (5,0) through forest
        )
        
        assert path is None  # Should not find path within cost limit
        
    def test_astar_avoids_enemy_units(self):
        """Test A* avoids enemy units"""
        pathfinder = AStarPathFinder()
        
        # Place enemy unit at (1,0)
        enemy = Unit(name="Enemy", unit_class=KnightClass.WARRIOR, x=1, y=0)
        enemy.player_id = 2
        self.game_state.add_knight(self.unit)
        self.game_state.add_knight(enemy)
        
        # Find path from (0,0) to (2,0)
        path = pathfinder.find_path(
            start=(0, 0),
            end=(2, 0),
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert path is not None
        assert (1, 0) not in path  # Should avoid enemy position
        
    def test_dijkstra_finds_all_reachable(self):
        """Test Dijkstra finds all reachable positions"""
        pathfinder = DijkstraPathFinder()
        
        # Find all positions reachable with cost 3
        reachable = pathfinder.find_all_reachable(
            start=(5, 5),
            game_state=self.game_state,
            unit=self.unit,
            max_cost=3
        )
        
        assert (5, 5) in reachable  # Start position
        assert reachable[(5, 5)] == 0  # Zero cost to start
        
        # Check hex neighbors are reachable
        # In hex grid, neighbors might be different than orthogonal
        from game.hex_utils import HexGrid
        hex_grid = HexGrid()
        start_hex = hex_grid.offset_to_axial(5, 5)
        
        # Check that at least some neighbors are reachable
        neighbor_count = 0
        for neighbor_hex in start_hex.get_neighbors():
            neighbor_offset = hex_grid.axial_to_offset(neighbor_hex)
            if neighbor_offset in reachable:
                neighbor_count += 1
        
        # Should have at least 4 reachable neighbors with cost 3
        assert neighbor_count >= 4
        
        # Check costs are correct
        for pos, cost in reachable.items():
            assert cost <= 3  # All within max cost
            
    def test_dijkstra_path_same_as_astar(self):
        """Test Dijkstra and A* find same optimal path"""
        astar = AStarPathFinder()
        dijkstra = DijkstraPathFinder()
        
        # Add some varied terrain
        from game.terrain import Terrain
        self.game_state.terrain_map.terrain_grid[1][2] = Terrain(TerrainType.FOREST)
        self.game_state.terrain_map.terrain_grid[2][3] = Terrain(TerrainType.FOREST)
        
        # Find paths with both algorithms
        astar_path = astar.find_path(
            start=(0, 0),
            end=(5, 3),
            game_state=self.game_state,
            unit=self.unit
        )
        
        dijkstra_path = dijkstra.find_path(
            start=(0, 0),
            end=(5, 3),
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert astar_path is not None
        assert dijkstra_path is not None
        
        # Calculate total costs for comparison
        def calc_path_cost(path):
            cost = 0
            positions = [(0, 0)] + list(path)
            for i in range(1, len(positions)):
                cost += astar._get_movement_cost(
                    positions[i-1], positions[i], 
                    self.game_state, self.unit
                )
            return cost
        
        # Both should find paths with same cost (optimal)
        assert calc_path_cost(astar_path) == calc_path_cost(dijkstra_path)
        
    def test_pathfinder_hex_movement(self):
        """Test pathfinding works correctly with hex grid movement"""
        pathfinder = AStarPathFinder()
        
        # In hex grid, diagonal moves are actually valid hex neighbors
        # Test movement in hex grid pattern
        path = pathfinder.find_path(
            start=(0, 0),
            end=(2, 1),  # This is a valid hex neighbor path
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert path is not None
        # In hex grid, the distance might be different than expected
        # Let's check the actual hex distance
        from game.hex_utils import HexGrid
        hex_grid = HexGrid()
        start_hex = hex_grid.offset_to_axial(0, 0)
        end_hex = hex_grid.offset_to_axial(2, 1)
        hex_distance = start_hex.distance_to(end_hex)
        
        # The path length should match the hex distance
        assert len(path) == hex_distance
        
    def test_no_path_to_blocked_destination(self):
        """Test returns None when destination is blocked"""
        pathfinder = AStarPathFinder()
        
        # Place enemy unit at destination
        enemy = Unit(name="Enemy", unit_class=KnightClass.WARRIOR, x=3, y=3)
        enemy.player_id = 2
        self.game_state.add_knight(self.unit)
        self.game_state.add_knight(enemy)
        
        path = pathfinder.find_path(
            start=(0, 0),
            end=(3, 3),
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert path is None  # Can't reach occupied square
        
    def test_no_path_to_impassable_terrain(self):
        """Test returns None when destination is impassable"""
        pathfinder = AStarPathFinder()
        
        # Make destination impassable
        from game.terrain import Terrain
        self.game_state.terrain_map.terrain_grid[3][3] = Terrain(TerrainType.WATER)
        
        path = pathfinder.find_path(
            start=(0, 0),
            end=(3, 3),
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert path is None  # Can't reach mountain square