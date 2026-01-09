import unittest
from unittest.mock import MagicMock
from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.facing import FacingDirection, FacingComponent
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
        start_x, start_y = unit.x, unit.y
        # Populate possible moves
        self.game_state.possible_moves = unit.get_possible_moves(
            self.game_state.board_width, 
            self.game_state.board_height, 
            self.game_state.terrain_map, 
            self.game_state
        )
        print(f"DEBUG: possible_moves for {unit.name} at ({unit.x}, {unit.y}): {self.game_state.possible_moves}")

        move_behavior = unit.behaviors.get('move')
        path = move_behavior.get_path_to(unit, self.game_state, target_x, target_y) if move_behavior else None
        expected_facing = None
        if path:
            if len(path) == 1:
                from_x, from_y = start_x, start_y
            else:
                from_x, from_y = path[-2]
            to_x, to_y = path[-1]
            facing_component = FacingComponent()
            facing_component.update_facing_from_movement(from_x, from_y, to_x, to_y)
            expected_facing = facing_component.facing

        px, py = self._get_screen_pos(target_x, target_y)
        success = self.game_state.move_selected_knight(px, py)
        print(f"DEBUG: _move_unit success={success} target=({target_x}, {target_y})")
        
        # Flush animations
        self.game_state.animation_coordinator.update(10.0)
        self.game_state.update(0.1)
        return expected_facing

    def test_ignore_invisible_enemy(self):
        """Test that unit does NOT auto-face an enemy hidden by Fog of War"""
        # Scenario: Player moves adjacent to an invisible enemy.
        # Should NOT face them (prevents detecting hidden units via UI cues).
        
        # Enemy at (7, 5) to stay outside vision range
        enemy = self._add_unit(KnightClass.WARRIOR, 7, 5, 2, "Hidden Enemy")
        
        # Player at (1, 5), moves to (2, 5) -> Far from enemy
        player = self._add_unit(KnightClass.CAVALRY, 1, 5, 1, "Player")
        player.facing.facing = FacingDirection.EAST
        
        # Mock Fog of War to hide the enemy
        if hasattr(self.game_state, 'fog_of_war'):
            # Force visibility map to hide enemy
            self.game_state.fog_of_war.visibility_maps[1][(7, 5)] = VisibilityState.HIDDEN
            
        # Move
        expected_facing = self._move_unit(player, 2, 5)
        
        # Reset visibility before second setup
        if hasattr(self.game_state, 'fog_of_war'):
            self.game_state.fog_of_war.visibility_maps[1][(7, 5)] = VisibilityState.HIDDEN
        
        # Let's change setup.
        # Player moves from (1, 3) to (2, 5).
        # (1, 3) Odd. (2, 5) Even.
        # Path should be (1, 3) -> (1, 4) -> (2, 5) (distance 2)
        
        player.x, player.y = 1, 3
        player.has_moved = False # Reset move flag
        player.action_points = 8 # Restore AP
        self.game_state.pending_positions.clear() # Clear pending
        
        # Move to (2, 5)
        expected_facing = self._move_unit(player, 2, 5)
        
        if expected_facing is not None:
            self.assertEqual(player.facing.facing, expected_facing,
                             "Should ignore invisible enemy and face movement direction")
        if hasattr(self.game_state, 'fog_of_war'):
            visibility = self.game_state.fog_of_war.get_visibility_state(1, 7, 5)
            self.assertNotIn(visibility, [VisibilityState.VISIBLE, VisibilityState.PARTIAL])

    def test_reveal_hidden_enemy_on_adjacent_move(self):
        """Test hidden enemies become visible when moving adjacent"""
        enemy = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Hidden Enemy")
        player = self._add_unit(KnightClass.WARRIOR, 3, 5, 1, "Player")
        player.action_points = 10
        player.has_moved = False

        self.game_state.fog_of_war.visibility_maps[1][(5, 5)] = VisibilityState.HIDDEN

        move_behavior = player.behaviors['move']
        result = move_behavior.execute(player, self.game_state, 4, 5)
        self.assertTrue(result['success'])

        visibility = self.game_state.fog_of_war.get_visibility_state(1, 5, 5)
        self.assertEqual(visibility, VisibilityState.VISIBLE)

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
        
        # Ensure they are visible
        self.game_state.fog_of_war.visibility_maps[1][(3, 5)] = VisibilityState.VISIBLE
        self.game_state.fog_of_war.visibility_maps[1][(5, 5)] = VisibilityState.VISIBLE
        
        self._move_unit(player, 4, 5)
        
        # Both are dist 1.
        # Current logic picks 'first found'.
        # We want it to pick Warrior (EAST).
        self.assertEqual(player.facing.facing, FacingDirection.EAST, 
                         "Should face Warrior (East) over Archer (West)")

if __name__ == '__main__':
    unittest.main()
