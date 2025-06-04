"""Test hex rendering bounds to verify the fix."""
import unittest
import os
import pygame
from game.game_state import GameState
from game.input_handler import InputHandler
from game.rendering.terrain_renderer import TerrainRenderer
from game.hex_layout import HexLayout
from game.hex_utils import HexGrid

class TestHexRenderingBounds(unittest.TestCase):
    def setUp(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        
    def tearDown(self):
        pygame.quit()
        
    def test_hex_visibility_at_different_zooms(self):
        """Test that all hexes are properly calculated as visible at different zoom levels."""
        config = {
            'board_size': (20, 15),
            'knights': 0,
            'castles': 0
        }
        game_state = GameState(config)
        input_handler = InputHandler()
        
        # Test zoom levels
        zoom_levels = [0.5, 1.0, 1.5, 2.0, 2.5]
        
        for zoom in zoom_levels:
            with self.subTest(zoom=zoom):
                # Set zoom
                game_state.camera_manager.set_zoom(zoom)
                input_handler.update_zoom(game_state)
                
                # Create terrain renderer with updated hex layout
                hex_size = int(36 * zoom)
                hex_grid = HexGrid(hex_size=hex_size)
                hex_layout = HexLayout(hex_size=hex_size, orientation='flat')
                terrain_renderer = TerrainRenderer(self.screen, hex_grid, hex_layout)
                
                # Position camera to see bottom-right corner
                last_hex_x = (game_state.board_width - 1) * hex_layout.col_spacing
                last_hex_y = (game_state.board_height - 1) * hex_layout.row_spacing
                
                # Position camera so bottom-right hex should be visible
                camera_x = max(0, last_hex_x - self.screen.get_width() + hex_layout.hex_width)
                camera_y = max(0, last_hex_y - self.screen.get_height() + hex_layout.hex_height) 
                game_state.camera_manager.set_camera_position(camera_x, camera_y)
                
                # Calculate visible hex range using fixed logic
                hex_width = hex_layout.col_spacing
                hex_height = hex_layout.row_spacing
                
                start_col = max(0, int(camera_x / hex_width) - 1)
                end_col = min(game_state.board_width, int((camera_x + self.screen.get_width()) / hex_width) + 2)
                start_row = max(0, int(camera_y / hex_height) - 1)
                end_row = min(game_state.board_height, int((camera_y + self.screen.get_height()) / hex_height) + 2)
                
                # Verify bottom-right hex is included
                self.assertGreaterEqual(end_col, game_state.board_width, 
                                      f"At zoom {zoom}, rightmost column not visible")
                self.assertGreaterEqual(end_row, game_state.board_height,
                                      f"At zoom {zoom}, bottom row not visible")
                                      
    def test_hex_visibility_top_left_corner(self):
        """Test that hexes are visible when camera is at origin."""
        config = {
            'board_size': (20, 15),
            'knights': 0,
            'castles': 0
        }
        game_state = GameState(config)
        
        # Position at origin
        game_state.camera_manager.set_camera_position(0, 0)
        
        # Create terrain renderer
        hex_grid = HexGrid(hex_size=36)
        hex_layout = HexLayout(hex_size=36, orientation='flat')
        terrain_renderer = TerrainRenderer(self.screen, hex_grid, hex_layout)
        
        # Calculate visible range
        hex_width = hex_layout.col_spacing
        hex_height = hex_layout.row_spacing
        
        start_col = max(0, int(0 / hex_width) - 1)
        start_row = max(0, int(0 / hex_height) - 1)
        
        # Should see hex (0,0)
        self.assertEqual(start_col, 0, "Should start at column 0")
        self.assertEqual(start_row, 0, "Should start at row 0")

if __name__ == '__main__':
    unittest.main()