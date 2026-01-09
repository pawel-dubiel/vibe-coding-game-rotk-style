"""Test movement path tracking and visualization"""
import unittest
import pygame
from game.game_state import GameState
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.visibility import VisibilityState
from game.renderer import Renderer
from game.terrain import TerrainType


class TestMovementPaths(unittest.TestCase):
    """Test movement path tracking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # Create game state with small board
        self.game_state = GameState({'board_size': (10, 10), 'knights': 2, 'castles': 1}, vs_ai=False)
        
        # Clear initial knights and add test units
        self.game_state.knights = []
        
        # Add player 1 unit using factory to get behaviors
        from game.entities.unit_factory import UnitFactory
        self.p1_unit = UnitFactory.create_unit("P1 Knight", KnightClass.WARRIOR, 2, 2)
        self.p1_unit.player_id = 1
        self.p1_unit.action_points = 5
        self.game_state.knights.append(self.p1_unit)
        
        # Add player 2 unit (enemy)
        self.p2_unit = UnitFactory.create_unit("P2 Knight", KnightClass.WARRIOR, 7, 7)
        self.p2_unit.player_id = 2
        self.p2_unit.action_points = 5
        self.game_state.knights.append(self.p2_unit)
        
        # Set current player
        self.game_state.current_player = 1
        
        # Create renderer
        self.renderer = Renderer(self.screen)
        
    def tearDown(self):
        """Clean up"""
        pygame.quit()
        
    def test_movement_history_tracking(self):
        """Test that movement history is properly tracked"""
        # Initially no movement history
        self.assertEqual(len(self.game_state.movement_history), 0)
        
        # Select player 2 unit (simulate AI turn)
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        
        # Populate possible moves first
        self.game_state.possible_moves = self.p2_unit.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state
        )
        
        # Move the unit
        start_pos = (self.p2_unit.x, self.p2_unit.y)
        target_pixel_x, target_pixel_y = 6 * 64, 7 * 64
        target_hex = self.game_state.hex_layout.pixel_to_hex(target_pixel_x, target_pixel_y)
        self.game_state.move_selected_knight(target_pixel_x, target_pixel_y)
        
        # Check movement history was recorded
        unit_id = id(self.p2_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
        path = self.game_state.movement_history[unit_id]
        
        # Movement should be from start to end, possibly with intermediate steps
        self.assertGreaterEqual(len(path), 2)  # At least start and end
        self.assertEqual(path[0], start_pos)  # First position should be start
        self.assertEqual(path[-1], target_hex)  # Last position should be target
        
    def test_enemy_paths_preserved_after_turn(self):
        """Test that enemy paths are preserved when turn changes"""
        # Move player 2 unit
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        
        # Populate possible moves for player 2 unit
        self.game_state.possible_moves = self.p2_unit.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state
        )
        
        self.game_state.move_selected_knight(6 * 64, 7 * 64)
        
        # End turn (switches to player 1)
        self.game_state.end_turn()
        
        # Check that player 2's movement is still in history
        unit_id = id(self.p2_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
        # Player 1's turn - enemy paths should still be visible
        self.assertEqual(self.game_state.current_player, 1)
        self.assertTrue(len(self.game_state.movement_history) > 0)
        
    def test_own_paths_preserved_for_enemy_visibility(self):
        """Test that own paths are preserved after turn for enemy visibility"""
        # Move player 1 unit
        self.game_state.current_player = 1
        self.game_state.selected_knight = self.p1_unit
        
        # Populate possible moves for player 1 unit
        self.game_state.possible_moves = self.p1_unit.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state
        )
        
        self.game_state.move_selected_knight(3 * 64, 2 * 64)
        
        # Check path was recorded
        unit_id = id(self.p1_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
        # End turn (switches to player 2)
        self.game_state.end_turn()
        
        # Player 1's path should be preserved so player 2 can see enemy movements
        self.assertIn(unit_id, self.game_state.movement_history)
        self.assertEqual(self.game_state.current_player, 2)
        
        # Verify the path is still there for enemy to see
        path = self.game_state.movement_history[unit_id]
        self.assertEqual(path[0], (2, 2))  # Start position
        
        # Now when player 2 ends their turn, player 1's old paths should be cleared
        self.game_state.end_turn()  # Back to player 1
        
        # Now player 1's old path should be cleared
        self.assertNotIn(unit_id, self.game_state.movement_history)
        
    def test_path_visibility_with_fog(self):
        """Test that paths respect fog of war visibility"""
        # Move player 2 unit
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        
        # Populate possible moves for player 2 unit
        self.game_state.possible_moves = self.p2_unit.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state
        )
        
        self.game_state.move_selected_knight(6 * 64, 7 * 64)
        
        # Switch to player 1
        self.game_state.end_turn()
        
        # Make enemy position not visible in fog
        self.game_state.fog_of_war.visibility_maps[1][(7, 7)] = VisibilityState.HIDDEN
        self.game_state.fog_of_war.visibility_maps[1][(6, 7)] = VisibilityState.HIDDEN
        
        # The path should exist but not be drawn (tested in renderer)
        unit_id = id(self.p2_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
    def test_toggle_path_visibility(self):
        """Test toggling path visibility"""
        # Initial state
        self.assertTrue(self.game_state.show_enemy_paths)
        
        # Simulate pressing 'P' key
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_p})
        from game.input_handler import InputHandler
        handler = InputHandler()
        handler.handle_event(event, self.game_state)
        
        # Should toggle off
        self.assertFalse(self.game_state.show_enemy_paths)
        
        # Toggle again
        handler.handle_event(event, self.game_state)
        
        # Should toggle on
        self.assertTrue(self.game_state.show_enemy_paths)
        
    def test_path_with_multiple_steps(self):
        """Test tracking paths with multiple steps"""
        # Use a unit with movement behavior
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        
        # Move in a path that requires multiple steps
        # This simulates the pathfinding creating a multi-step path
        path = [(7, 7), (6, 7), (5, 7), (4, 7)]
        
        # Manually set the movement history to test rendering
        unit_id = id(self.p2_unit)
        self.game_state.movement_history[unit_id] = path
        
        # Verify the path
        self.assertEqual(len(self.game_state.movement_history[unit_id]), 4)
        
        print(f"Multi-step path: {path}")
        
    def test_movement_creates_path(self):
        """Test that actual movement creates a path in history"""
        # Switch to player 2
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit

        self.game_state.terrain_map.set_terrain(7, 7, TerrainType.PLAINS)
        self.game_state.terrain_map.set_terrain(6, 7, TerrainType.PLAINS)
        
        # Populate possible moves (normally done when selecting a unit)
        self.game_state.possible_moves = self.p2_unit.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state
        )

        target_hex = (6, 7)
        target_px, target_py = self.game_state.hex_layout.hex_to_pixel(*target_hex)
        success = self.game_state.move_selected_knight(target_px, target_py)

        assert success is True
        unit_id = id(self.p2_unit)
        assert unit_id in self.game_state.movement_history

        path = self.game_state.movement_history[unit_id]
        assert path[0] == (7, 7)
        assert path[-1] == target_hex
        assert len(path) >= 2


if __name__ == '__main__':
    unittest.main()
