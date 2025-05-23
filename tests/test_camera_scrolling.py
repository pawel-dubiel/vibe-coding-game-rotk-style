import unittest
import pygame
from game.game_state import GameState
from game.input_handler import InputHandler


class TestCameraScrolling(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        # Use a large battle config to ensure scrolling is possible
        large_config = {'board_size': (25, 25), 'knights': 8, 'castles': 3}
        self.game_state = GameState(large_config)
        self.input_handler = InputHandler()
    
    def tearDown(self):
        pygame.quit()
    
    def test_initial_camera_position(self):
        """Test that camera starts centered on player 1's units"""
        # Camera should be centered on player 1's starting area
        # For a 25x25 board, camera should be offset from origin
        self.assertGreaterEqual(self.game_state.camera_x, 0)
        self.assertGreaterEqual(self.game_state.camera_y, 0)
        # Camera should not be at max position (should be near player 1 start)
        max_x = self.game_state.board_width * self.game_state.tile_size - self.game_state.screen_width
        self.assertLess(self.game_state.camera_x, max_x // 2)
    
    def test_set_camera_position_bounds(self):
        """Test camera bounds checking"""
        # Test setting camera within bounds
        self.game_state.set_camera_position(100, 100)
        self.assertEqual(self.game_state.camera_x, 100)
        self.assertEqual(self.game_state.camera_y, 100)
        
        # Test negative bounds
        self.game_state.set_camera_position(-100, -100)
        self.assertEqual(self.game_state.camera_x, 0)
        self.assertEqual(self.game_state.camera_y, 0)
        
        # Test maximum bounds
        max_x = self.game_state.board_width * self.game_state.tile_size - self.game_state.screen_width
        max_y = self.game_state.board_height * self.game_state.tile_size - self.game_state.screen_height
        
        self.game_state.set_camera_position(9999, 9999)
        self.assertEqual(self.game_state.camera_x, max(0, max_x))
        self.assertEqual(self.game_state.camera_y, max(0, max_y))
    
    def test_move_camera(self):
        """Test relative camera movement"""
        initial_x = self.game_state.camera_x
        initial_y = self.game_state.camera_y
        
        # Move camera right and down
        self.game_state.move_camera(50, 30)
        self.assertEqual(self.game_state.camera_x, initial_x + 50)
        self.assertEqual(self.game_state.camera_y, initial_y + 30)
        
        # Move camera left and up
        self.game_state.move_camera(-20, -10)
        self.assertEqual(self.game_state.camera_x, initial_x + 30)
        self.assertEqual(self.game_state.camera_y, initial_y + 20)
    
    def test_center_camera_on_tile(self):
        """Test centering camera on a specific tile"""
        # Center on tile (5, 5)
        self.game_state.center_camera_on_tile(5, 5)
        
        # Calculate expected camera position
        tile_center_x = 5 * self.game_state.tile_size + self.game_state.tile_size // 2
        tile_center_y = 5 * self.game_state.tile_size + self.game_state.tile_size // 2
        expected_x = tile_center_x - self.game_state.screen_width // 2
        expected_y = tile_center_y - self.game_state.screen_height // 2
        
        # Camera should be positioned to center the tile
        max_x = self.game_state.board_width * self.game_state.tile_size - self.game_state.screen_width
        max_y = self.game_state.board_height * self.game_state.tile_size - self.game_state.screen_height
        
        self.assertEqual(self.game_state.camera_x, max(0, min(expected_x, max_x)))
        self.assertEqual(self.game_state.camera_y, max(0, min(expected_y, max_y)))
    
    def test_screen_to_world_conversion(self):
        """Test coordinate conversion from screen to world"""
        self.game_state.set_camera_position(100, 50)
        
        # Test conversion
        screen_x, screen_y = 200, 150
        world_x, world_y = self.game_state.screen_to_world(screen_x, screen_y)
        
        self.assertEqual(world_x, 300)  # 200 + 100
        self.assertEqual(world_y, 200)  # 150 + 50
    
    def test_world_to_screen_conversion(self):
        """Test coordinate conversion from world to screen"""
        self.game_state.set_camera_position(100, 50)
        
        # Test conversion
        world_x, world_y = 300, 200
        screen_x, screen_y = self.game_state.world_to_screen(world_x, world_y)
        
        self.assertEqual(screen_x, 200)  # 300 - 100
        self.assertEqual(screen_y, 150)  # 200 - 50
    
    def test_keyboard_scrolling(self):
        """Test camera movement with keyboard keys"""
        initial_x = self.game_state.camera_x
        initial_y = self.game_state.camera_y
        
        # Test arrow keys
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT})
        self.input_handler.handle_event(event, self.game_state)
        self.assertEqual(self.game_state.camera_x, initial_x + 100)
        
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT})
        self.input_handler.handle_event(event, self.game_state)
        self.assertEqual(self.game_state.camera_x, initial_x)
        
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN})
        self.input_handler.handle_event(event, self.game_state)
        self.assertEqual(self.game_state.camera_y, initial_y + 100)
        
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP})
        self.input_handler.handle_event(event, self.game_state)
        self.assertEqual(self.game_state.camera_y, initial_y)
        
        # Test WASD keys
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_d})
        self.input_handler.handle_event(event, self.game_state)
        self.assertEqual(self.game_state.camera_x, initial_x + 100)
        
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a})
        self.input_handler.handle_event(event, self.game_state)
        self.assertEqual(self.game_state.camera_x, initial_x)
    
    def test_mouse_drag_scrolling(self):
        """Test camera movement with right mouse drag"""
        # Test the core drag functionality by simulating the drag state directly
        initial_x = self.game_state.camera_x
        initial_y = self.game_state.camera_y
        
        # Set up drag state as if right button was pressed at (400, 300)
        self.input_handler.right_click_held = True
        self.input_handler.drag_start_x = 400
        self.input_handler.drag_start_y = 300
        self.input_handler.camera_drag_start_x = initial_x
        self.input_handler.camera_drag_start_y = initial_y
        
        # Simulate mouse motion event
        event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (350, 250)})
        # Mock pygame.mouse.get_pos to return our desired position
        original_get_pos = pygame.mouse.get_pos
        pygame.mouse.get_pos = lambda: (350, 250)
        
        try:
            self.input_handler.handle_event(event, self.game_state)
            
            # Camera should move in opposite direction (drag effect)
            # Moving mouse left 50 and up 50 should move camera right 50 and down 50
            self.assertEqual(self.game_state.camera_x, initial_x + 50)
            self.assertEqual(self.game_state.camera_y, initial_y + 50)
        finally:
            # Restore original function
            pygame.mouse.get_pos = original_get_pos
        
        # Test release
        event = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 3})
        self.input_handler.handle_event(event, self.game_state)
        self.assertFalse(self.input_handler.right_click_held)
    
    def test_battle_size_camera_bounds(self):
        """Test camera bounds for different battle sizes"""
        # Test small battle
        small_config = {'board_size': (15, 15), 'knights': 3, 'castles': 1}
        small_game = GameState(small_config)
        
        # Try to set camera beyond bounds
        small_game.set_camera_position(9999, 9999)
        max_x = 15 * 64 - 1024  # board_width * tile_size - screen_width
        max_y = 15 * 64 - 768   # board_height * tile_size - screen_height
        
        # Since board might be smaller than screen, camera should stay at 0
        if max_x < 0:
            self.assertEqual(small_game.camera_x, 0)
        if max_y < 0:
            self.assertEqual(small_game.camera_y, 0)
        
        # Test large battle
        large_config = {'board_size': (25, 25), 'knights': 8, 'castles': 3}
        large_game = GameState(large_config)
        
        large_game.set_camera_position(9999, 9999)
        max_x = 25 * 64 - 1024
        max_y = 25 * 64 - 768
        
        self.assertEqual(large_game.camera_x, max_x)
        self.assertEqual(large_game.camera_y, max_y)


if __name__ == '__main__':
    unittest.main()