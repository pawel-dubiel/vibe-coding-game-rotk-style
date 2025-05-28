"""Simple tests for pathfinding implementations"""
import unittest
from game.pathfinding import AStarPathFinder, DijkstraPathFinder
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.terrain import TerrainType, TerrainMap


class TestPathfindingSimple(unittest.TestCase):
    """Simple test cases for pathfinding algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_state = MockGameState(board_width=10, board_height=10)
        
        # Create test unit at center of board
        self.unit = Unit(name="Test Warrior", unit_class=KnightClass.WARRIOR, x=5, y=5)
        self.unit.player_id = 1
        self.unit.action_points = 10
        
    def test_astar_basic_path(self):
        """Test A* finds basic path"""
        pathfinder = AStarPathFinder()
        
        # Find path from (5,5) to (7,5)
        path = pathfinder.find_path(
            start=(5, 5),
            end=(7, 5),
            game_state=self.game_state,
            unit=self.unit
        )
        
        self.assertIsNotNone(path)
        self.assertGreater(len(path), 0)
        self.assertEqual(path[-1], (7, 5))
        
    def test_dijkstra_basic_path(self):
        """Test Dijkstra finds basic path"""
        pathfinder = DijkstraPathFinder()
        
        # Find path from (5,5) to (7,5)
        path = pathfinder.find_path(
            start=(5, 5),
            end=(7, 5),
            game_state=self.game_state,
            unit=self.unit
        )
        
        self.assertIsNotNone(path)
        self.assertGreater(len(path), 0)
        self.assertEqual(path[-1], (7, 5))
        
    def test_dijkstra_find_all_reachable(self):
        """Test Dijkstra finds reachable positions"""
        pathfinder = DijkstraPathFinder()
        
        # Find all positions reachable with cost 2
        reachable = pathfinder.find_all_reachable(
            start=(5, 5),
            game_state=self.game_state,
            unit=self.unit,
            max_cost=2
        )
        
        self.assertIn((5, 5), reachable)  # Start position
        self.assertEqual(reachable[(5, 5)], 0)  # Zero cost to start
        
        # Should have multiple reachable positions
        self.assertGreater(len(reachable), 1)
        
        
if __name__ == '__main__':
    unittest.main()