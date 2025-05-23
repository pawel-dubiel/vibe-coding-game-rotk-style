"""Tests for pathfinding implementations"""
import unittest
from game.pathfinding import PathFinder, AStarPathFinder, DijkstraPathFinder
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit import Unit, UnitClass
from game.terrain import TerrainType, TerrainMap


class TestPathfinding(unittest.TestCase):
    """Test pathfinding algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_state = MockGameState()
        self.game_state.board_width = 10
        self.game_state.board_height = 10
        
        # Create terrain map
        self.game_state.terrain_map = TerrainMap(10, 10)
        
        # Create test unit
        self.unit = Unit(x=0, y=0, player_id=1, unit_class=UnitClass.WARRIOR, soldiers=100)
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
        self.game_state.terrain_map.set_terrain(1, 0, TerrainType.MOUNTAIN)
        
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
        for x in range(10):
            for y in range(10):
                self.game_state.terrain_map.set_terrain(x, y, TerrainType.FOREST)
        
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
        enemy = Unit(x=1, y=0, player_id=2, unit_class=UnitClass.WARRIOR, soldiers=100)
        self.game_state.knights = [self.unit, enemy]
        
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
        
        # Check some adjacent positions are reachable
        assert (4, 5) in reachable
        assert (6, 5) in reachable
        assert (5, 4) in reachable
        assert (5, 6) in reachable
        
        # Check costs are correct
        for pos, cost in reachable.items():
            assert cost <= 3  # All within max cost
            
    def test_dijkstra_path_same_as_astar(self):
        """Test Dijkstra and A* find same optimal path"""
        astar = AStarPathFinder()
        dijkstra = DijkstraPathFinder()
        
        # Add some varied terrain
        self.game_state.terrain_map.set_terrain(2, 1, TerrainType.FOREST)
        self.game_state.terrain_map.set_terrain(3, 2, TerrainType.FOREST)
        
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
        assert len(path) == 2  # Should be 2 hex moves
        
    def test_no_path_to_blocked_destination(self):
        """Test returns None when destination is blocked"""
        pathfinder = AStarPathFinder()
        
        # Place enemy unit at destination
        enemy = Unit(x=3, y=3, player_id=2, unit_class=UnitClass.WARRIOR, soldiers=100)
        self.game_state.knights = [self.unit, enemy]
        
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
        self.game_state.terrain_map.set_terrain(3, 3, TerrainType.MOUNTAIN)
        
        path = pathfinder.find_path(
            start=(0, 0),
            end=(3, 3),
            game_state=self.game_state,
            unit=self.unit
        )
        
        assert path is None  # Can't reach mountain square