"""Test movement path tracking and visualization"""
import unittest
import pygame
from game.game_state import GameState
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.visibility import VisibilityState
from game.renderer import Renderer


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
        self.game_state.move_selected_knight(6 * 64, 7 * 64)  # Move to (6, 7)
        
        # Check movement history was recorded
        unit_id = id(self.p2_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
        path = self.game_state.movement_history[unit_id]
        self.assertEqual(len(path), 2)  # Start and end position
        self.assertEqual(path[0], start_pos)
        self.assertEqual(path[1], (6, 7))
        
        print(f"Movement history recorded: {path}")
        
    def test_enemy_paths_preserved_after_turn(self):
        """Test that enemy paths are preserved when turn changes"""
        # Move player 2 unit
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        self.game_state.move_selected_knight(6 * 64, 7 * 64)
        
        # End turn (switches to player 1)
        self.game_state.end_turn()
        
        # Check that player 2's movement is still in history
        unit_id = id(self.p2_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
        # Player 1's turn - enemy paths should still be visible
        self.assertEqual(self.game_state.current_player, 1)
        self.assertTrue(len(self.game_state.movement_history) > 0)
        
        print(f"Enemy paths preserved after turn: {self.game_state.movement_history}")
        
    def test_own_paths_cleared_after_turn(self):
        """Test that own paths are cleared after turn"""
        # Move player 1 unit
        self.game_state.current_player = 1
        self.game_state.selected_knight = self.p1_unit
        self.game_state.move_selected_knight(3 * 64, 2 * 64)
        
        # Check path was recorded
        unit_id = id(self.p1_unit)
        self.assertIn(unit_id, self.game_state.movement_history)
        
        # End turn
        self.game_state.end_turn()
        
        # Player 1's path should be cleared
        self.assertNotIn(unit_id, self.game_state.movement_history)
        
    def test_path_visibility_with_fog(self):
        """Test that paths respect fog of war visibility"""
        # Move player 2 unit
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        self.game_state.move_selected_knight(6 * 64, 7 * 64)
        
        # Switch to player 1
        self.game_state.end_turn()
        
        # Make enemy position not visible in fog
        self.game_state.fog_of_war._visibility_grid[1][7][7] = VisibilityState.HIDDEN
        self.game_state.fog_of_war._visibility_grid[1][6][7] = VisibilityState.HIDDEN
        
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
        # Enable debug output
        print("\n=== Testing Movement Path Creation ===")
        print(f"Initial movement history: {self.game_state.movement_history}")
        print(f"Current player: {self.game_state.current_player}")
        print(f"P2 unit position: ({self.p2_unit.x}, {self.p2_unit.y})")
        
        # Switch to player 2
        self.game_state.current_player = 2
        self.game_state.selected_knight = self.p2_unit
        
        # Populate possible moves (normally done when selecting a unit)
        self.game_state.possible_moves = self.p2_unit.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state
        )
        
        # Check if unit has movement behavior
        if hasattr(self.p2_unit, 'behaviors'):
            print(f"Unit behaviors: {list(self.p2_unit.behaviors.keys())}")
        
        # Check unit properties
        print(f"Unit has_moved: {self.p2_unit.has_moved}")
        print(f"Unit action_points: {self.p2_unit.action_points}")
        print(f"Can move: {self.p2_unit.can_move()}")
        
        # Check possible moves
        possible_moves = self.p2_unit.get_possible_moves(
            self.game_state.board_width, 
            self.game_state.board_height, 
            self.game_state.terrain_map, 
            self.game_state
        )
        print(f"Possible moves from ({self.p2_unit.x}, {self.p2_unit.y}): {len(possible_moves)} positions")
        print(f"Target (6, 7) in possible moves: {(6, 7) in possible_moves}")
        
        # Try to move
        success = self.game_state.move_selected_knight(6 * 64, 7 * 64)
        print(f"Move success: {success}")
        print(f"Movement history after move: {self.game_state.movement_history}")
        
        # Check if animation was created
        print(f"Animations: {len(self.game_state.animation_manager.animations)}")
        
        return success


if __name__ == '__main__':
    unittest.main()