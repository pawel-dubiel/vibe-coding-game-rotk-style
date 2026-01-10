
import unittest
from unittest.mock import Mock, patch
from game.entities.unit_factory import UnitFactory
from game.entities.castle import Castle
from game.terrain import TerrainType
from game.behaviors.movement import MovementBehavior
from game.behaviors.movement_service import MovementService
from game.hex_utils import HexGrid

# Reusing mocks from test_movement.py for consistency
class MockTerrain:
    def __init__(self, terrain_type):
        self.type = terrain_type
        self.movement_cost = 1
        self.defense_bonus = 0
        self.passable = True
        
    def get_movement_cost_for_unit(self, knight_class):
        return 1

class MockTerrainMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.terrain_grid = {}
        for y in range(height):
            for x in range(width):
                self.terrain_grid[(x, y)] = MockTerrain(TerrainType.PLAINS)
                
    def get_movement_cost(self, x, y, unit):
        return 1

    def is_passable(self, x, y, unit=None):
        return True

class MockGameState:
    def __init__(self):
        self.board_width = 20
        self.board_height = 20
        self.knights = []
        self.castles = []
        self.terrain_map = MockTerrainMap(20, 20)
        self.pending_positions = {}

class TestCastleMovementBug(unittest.TestCase):
    
    def setUp(self):
        self.game_state = MockGameState()
        self.movement_service = MovementService()
        
        # Create a unit for player 1
        self.unit = UnitFactory.create_warrior("Test Warrior", 2, 5)
        self.unit.player_id = 1
        self.unit.action_points = 10 # Give plenty of AP
        self.game_state.knights = [self.unit]
        
        # Create an ENEMY castle (player 2) at (5, 5)
        # Castle occupies (5,5) and adjacent tiles (diamond shape)
        # (4,5), (6,5), (5,4), (5,6) are also castle tiles
        self.enemy_castle = Castle(5, 5, player_id=2)
        self.game_state.castles = [self.enemy_castle]
        
    def test_cannot_move_through_enemy_castle(self):
        """Test that a unit cannot move through tiles occupied by an enemy castle"""
        
        # Unit is at (2, 5). Castle starts at (4, 5).
        # We want to try to move to (7, 5) which is on the other side.
        # Direct path: (2,5) -> (3,5) -> (4,5)[Castle] -> (5,5)[Castle] -> (6,5)[Castle] -> (7,5)
        
        target_x, target_y = 7, 5
        
        # Ensure we have enough AP to cover the distance if there were no obstacles
        dist = abs(target_x - self.unit.x) + abs(target_y - self.unit.y)
        self.unit.action_points = 20
        
        # Get path using MovementService (which uses MovementBehavior internally)
        path = self.movement_service.get_movement_path(self.unit, target_x, target_y, self.game_state)
        
        # If path is found, verify it doesn't go through castle tiles
        castle_tiles = self.enemy_castle.occupied_tiles
        
        if path:
            print(f"Path found: {path}")
            for x, y in path:
                if (x, y) in castle_tiles:
                    self.fail(f"Path goes through enemy castle tile at ({x}, {y})")
        
        # Also check if we can simply move to a castle tile directly
        # (4, 5) is a castle tile
        can_move_into_castle = self.movement_service.can_move_to_position(self.unit, 4, 5, self.game_state)
        self.assertFalse(can_move_into_castle, "Should not be able to move directly into enemy castle tile")
        
    def test_pathfinding_avoids_castle(self):
        """Test that pathfinding finds a way AROUND the castle, not through it"""
        
        # Unit at (2, 5)
        # Castle at (5, 5) -> covers x=4 to 6
        # Target at (8, 5)
        
        # To force the issue, let's make the unit have just enough AP to go around, 
        # or check that the cost is high.
        
        target_x, target_y = 8, 5
        self.unit.action_points = 20
        
        path = self.movement_service.get_movement_path(self.unit, target_x, target_y, self.game_state)
        
        self.assertIsNotNone(path, "Should find a path around the castle")
        
        castle_tiles = self.enemy_castle.occupied_tiles
        for x, y in path:
            self.assertNotIn((x, y), castle_tiles, f"Path step ({x}, {y}) is inside enemy castle")

if __name__ == '__main__':
    unittest.main()
