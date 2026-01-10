
import unittest
from game.visibility import FogOfWar, VisibilityState
from game.entities.unit_factory import UnitFactory
from game.entities.castle import Castle
from game.terrain import TerrainMap, TerrainType
from game.test_utils.mock_game_state import MockGameState

class TestCastleVision(unittest.TestCase):
    def setUp(self):
        self.game_state = MockGameState(board_width=20, board_height=20)
        self.fog = FogOfWar(20, 20, 2)
        
        # Unit for player 1 at (4, 5)
        self.unit = UnitFactory.create_warrior("Watcher", 4, 5)
        self.unit.player_id = 1
        self.unit.game_state = self.game_state
        
        # Attach vision behavior with more range
        from game.behaviors.vision import VisionBehavior
        vision = VisionBehavior(base_range=6, elevated_bonus=2)
        self.unit.add_behavior(vision)
        
        self.game_state.add_knight(self.unit)
        
        # Castle at (6, 5)
        self.castle = Castle(6, 5, 2)
        self.game_state.add_castle(self.castle)
        
    def test_castle_blocks_vision(self):
        """Test that a castle blocks line of sight to hexes behind it."""
        # Update visibility for player 1
        self.fog.update_player_visibility(self.game_state, 1)
        
        # Tile (5, 5) is part of the castle and should be visible
        # Tile (8, 5) is directly behind the castle and should be hidden
        
        state_castle = self.fog.get_visibility_state(1, 5, 5)
        state_behind = self.fog.get_visibility_state(1, 8, 5)
        
        print(f"Castle tile (5,5) state: {state_castle}")
        print(f"Behind tile (8,5) state: {state_behind}")
        
        self.assertIn(state_castle, [VisibilityState.VISIBLE, VisibilityState.PARTIAL])
        self.assertEqual(state_behind, VisibilityState.HIDDEN, "Tile behind castle should be hidden")

    def test_elevated_unit_sees_over_castle(self):
        """Test that an elevated unit (e.g. cavalry or on mountains) can see over a castle."""
        # Move unit to mountains at (4, 5)
        from game.terrain import Terrain
        self.game_state.terrain_map.terrain_grid[5][4] = Terrain(TerrainType.MOUNTAINS)
        
        self.fog.update_player_visibility(self.game_state, 1)
        
        state_behind = self.fog.get_visibility_state(1, 8, 5)
        self.assertIn(state_behind, [VisibilityState.VISIBLE, VisibilityState.PARTIAL, VisibilityState.EXPLORED], 
                     "Elevated unit should see over castle")
        self.assertNotEqual(state_behind, VisibilityState.HIDDEN)

if __name__ == '__main__':
    unittest.main()
