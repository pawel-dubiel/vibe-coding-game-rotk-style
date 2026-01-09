import unittest
from unittest.mock import MagicMock
from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.facing import FacingDirection
from game.visibility import VisibilityState

class TestAutoFacingEdgeCases(unittest.TestCase):
    def setUp(self):
        import pygame
        pygame.init()
        if not pygame.display.get_surface():
            pygame.display.set_mode((1, 1), pygame.NOFRAME)
            
        self.game_state = GameState({'board_size': (10, 10), 'knights': 0, 'castles': 0}, vs_ai=False)
        self.game_state.knights = []
        self.factory = UnitFactory()

    def _add_unit(self, unit_class, x, y, player_id, name="Unit"):
        unit = UnitFactory.create_unit(name, unit_class, x, y)
        unit.player_id = player_id
        if hasattr(unit, 'facing'):
            unit.facing.facing = FacingDirection.EAST
        self.game_state.knights.append(unit)
        self.game_state._update_all_fog_of_war()
        return unit

    def _get_screen_pos(self, hex_x, hex_y):
        return self.game_state.hex_layout.hex_to_pixel(hex_x, hex_y)

    def _move_unit(self, unit, target_x, target_y):
        self.game_state.selected_knight = unit
        # Populate possible moves
        self.game_state.possible_moves = unit.get_possible_moves(
            self.game_state.board_width, 
            self.game_state.board_height, 
            self.game_state.terrain_map, 
            self.game_state
        )
        
        px, py = self._get_screen_pos(target_x, target_y)
        success = self.game_state.move_selected_knight(px, py)
        print(f"DEBUG: _move_unit {unit.name} to ({target_x}, {target_y}) success={success}")
        
        # Flush animations
        self.game_state.animation_coordinator.update(10.0)
        self.game_state.update(0.1)

    def test_ignore_invisible_enemy(self):
        """Test that unit does NOT auto-face an enemy hidden by Fog of War"""
        # Scenario: Player moves adjacent to an invisible enemy.
        # Should NOT face them (prevents detecting hidden units via UI cues).
        
        # Enemy at (5, 5)
        enemy = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Hidden Enemy")
        
        # Player at (3, 5), moves to (4, 5) -> Adjacent to enemy
        player = self._add_unit(KnightClass.WARRIOR, 3, 5, 1, "Player")
        player.facing.facing = FacingDirection.EAST
        
        # Mock Fog of War to hide the enemy
        # We need to mock the visibility system or manually set visibility
        if hasattr(self.game_state, 'fog_of_war'):
            # Force visibility map to hide enemy
            self.game_state.fog_of_war.visibility_maps[1][(5, 5)] = VisibilityState.HIDDEN
            
            # Verify mockery
            vis = self.game_state.fog_of_war.get_visibility_state(1, 5, 5)
            self.assertEqual(vis, VisibilityState.HIDDEN)
            
        # Move adjacent
        self._move_unit(player, 4, 5)
        
        # Expectation: 
        # If auto-face works on hidden units, it would face EAST (towards enemy).
        # If it ignores hidden units, it should face movement direction (EAST).
        # Wait, movement (3,5)->(4,5) is EAST.
        # So facing EAST is ambiguous.
        
        # Let's change setup.
        # Player moves from (4, 4) to (4, 5). Movement is SOUTH.
        # Enemy is at (5, 5) (EAST of target).
        # If auto-face sees enemy, unit turns EAST.
        # If auto-face ignores enemy, unit stays SOUTH (movement dir).
        
        player.x, player.y = 4, 4
        player.has_moved = False # Reset move flag
        
        # Move to (4, 5)
        self._move_unit(player, 4, 5)
        
        # Check facing
        # If it faced the enemy, it would be EAST (or SE? (4,5) is Even. (5,5) is SE)
        # Even row (4,5). (5,5) is Odd row. (4,5) neighbors: SE is (4,6)? No.
        # Even row (4,5) neighbors: E is (5,5).
        # So facing should be EAST if it sees enemy.
        # Movement (4,4)->(4,5) is SOUTH (SE or SW depending on parity).
        # (4,4) Even -> (4,5) Even? No, y increases.
        # (4,4) Even. (4,5) Odd.
        # (4,4) -> (4,5). dy=1, dx=0.
        # From Even row: SOUTH_EAST.
        
        # So Movement = SOUTH_EAST.
        # Enemy at (5,5).
        # (4,5) Odd -> (5,5) Odd. dx=1, dy=0. EAST.
        
        # So:
        # If auto-face triggers: EAST.
        # If NO auto-face: SOUTH_EAST.
        
        # We want it to be SOUTH_EAST (ignoring invisible enemy).
        self.assertEqual(player.facing.facing, FacingDirection.SOUTH_EAST, 
                         "Should ignore invisible enemy and face movement direction (SE)")

    def test_face_biggest_threat(self):
        """Test that unit faces the most dangerous enemy when between two"""
        # Scenario: Player moves between an Archer and a Warrior.
        # Should face Warrior (Melee threat) over Archer (Ranged/Weaker threat).
        
        # Archer at (3, 5) [West of target]
        archer = self._add_unit(KnightClass.ARCHER, 3, 5, 2, "Enemy Archer")
        
        # Warrior at (5, 5) [East of target]
        warrior = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Enemy Warrior")
        
        # Player moves to (4, 5) [Between them]
        # Start at (4, 4)
        player = self._add_unit(KnightClass.WARRIOR, 4, 4, 1, "Player")
        
        self._move_unit(player, 4, 5)
        
        # Both are dist 1.
        # Current logic picks 'first found'.
        # We want it to pick Warrior (EAST).
        self.assertEqual(player.facing.facing, FacingDirection.EAST, 
                         "Should face Warrior (East) over Archer (West)")

if __name__ == '__main__':
    unittest.main()
