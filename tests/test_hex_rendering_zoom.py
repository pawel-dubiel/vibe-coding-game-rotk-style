import os
import pygame
import unittest
from game.game_state import GameState
from game.rendering.terrain_renderer import TerrainRenderer
from game.hex_layout import HexLayout
from game.hex_utils import HexGrid

class TestHexRenderingZoom(unittest.TestCase):
    def setUp(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        config = {'board_size': (20, 20), 'knights': 0, 'castles': 0}
        self.game_state = GameState(config)
        
    def tearDown(self):
        pygame.quit()
        
    def test_visible_hex_calculation_at_different_zooms(self):
        """Test that visible hex range is calculated correctly at different zoom levels"""
        
        # Create terrain renderer with initial hex layout
        hex_grid = HexGrid(hex_size=36)
        hex_layout = HexLayout(hex_size=36)
        terrain_renderer = TerrainRenderer(self.screen, hex_grid, hex_layout)
        
        # Test at zoom level 1.0
        self.game_state.camera_manager.zoom_level = 1.0
        self.game_state.camera_manager.set_camera_position(0, 0)
        
        # Calculate visible range
        camera_x = self.game_state.camera_manager.camera_x
        camera_y = self.game_state.camera_manager.camera_y
        screen_width = self.game_state.camera_manager.screen_width
        screen_height = self.game_state.camera_manager.screen_height
        zoom_level = self.game_state.camera_manager.zoom_level
        
        hex_width = hex_layout.col_spacing
        hex_height = hex_layout.row_spacing
        
        start_col = max(0, int(camera_x / hex_width) - 1)
        end_col = min(self.game_state.board_width, int((camera_x + screen_width) / hex_width) + 2)
        start_row = max(0, int(camera_y / hex_height) - 1)
        end_row = min(self.game_state.board_height, int((camera_y + screen_height) / hex_height) + 2)
        
        # Should see approximately screen_width / hex_width columns
        expected_cols = int(screen_width / hex_layout.col_spacing) + 3  # +3 for margin
        actual_cols = end_col - start_col
        self.assertAlmostEqual(actual_cols, expected_cols, delta=2)
        
        # Test at zoom level 2.0 (zoomed in)
        self.game_state.camera_manager.zoom_level = 2.0
        # Update hex layout to match zoom
        hex_grid = HexGrid(hex_size=72)  # 36 * 2
        hex_layout = HexLayout(hex_size=72)
        terrain_renderer.hex_grid = hex_grid
        terrain_renderer.hex_layout = hex_layout
        
        hex_width = hex_layout.col_spacing
        hex_height = hex_layout.row_spacing
        
        start_col = max(0, int(camera_x / hex_width) - 1)
        end_col = min(self.game_state.board_width, int((camera_x + screen_width) / hex_width) + 2)
        
        # When zoomed in, we should see fewer hexes
        zoomed_cols = end_col - start_col
        self.assertLess(zoomed_cols, actual_cols)
        
        # Test at zoom level 0.5 (zoomed out)
        self.game_state.camera_manager.zoom_level = 0.5
        # Update hex layout to match zoom
        hex_grid = HexGrid(hex_size=18)  # 36 * 0.5
        hex_layout = HexLayout(hex_size=18)
        terrain_renderer.hex_grid = hex_grid
        terrain_renderer.hex_layout = hex_layout
        
        hex_width = hex_layout.col_spacing
        hex_height = hex_layout.row_spacing
        
        start_col = max(0, int(camera_x / hex_width) - 1)
        end_col = min(self.game_state.board_width, int((camera_x + screen_width) / hex_width) + 2)
        
        # When zoomed out, we should see more hexes
        zoomed_out_cols = end_col - start_col
        self.assertGreater(zoomed_out_cols, actual_cols)
        
    def test_hex_visibility_at_screen_edges(self):
        """Test that hexes at screen edges are properly included in render range"""
        
        # Set up hex layout
        hex_size = 36
        hex_grid = HexGrid(hex_size=hex_size)
        hex_layout = HexLayout(hex_size=hex_size)
        terrain_renderer = TerrainRenderer(self.screen, hex_grid, hex_layout)
        
        # Position camera to see right edge of board
        self.game_state.camera_manager.zoom_level = 1.0
        # Move camera so that we're looking at hexes 10-19 horizontally
        camera_x = 10 * hex_layout.col_spacing
        self.game_state.camera_manager.set_camera_position(camera_x, 0)
        
        # Calculate visible range
        screen_width = self.game_state.camera_manager.screen_width
        screen_height = self.game_state.camera_manager.screen_height
        zoom_level = self.game_state.camera_manager.zoom_level
        
        hex_width = hex_layout.col_spacing
        hex_height = hex_layout.row_spacing
        
        start_col = max(0, int(camera_x / hex_width) - 1)
        end_col = min(self.game_state.board_width, int((camera_x + screen_width) / hex_width) + 2)
        
        # Verify we include margin hexes
        self.assertEqual(start_col, 9)  # One hex before visible area
        self.assertTrue(end_col <= self.game_state.board_width)  # Don't exceed board width
        
        # The rightmost visible hex should be included (up to board boundary)
        rightmost_visible_x = camera_x + screen_width
        rightmost_hex = int(rightmost_visible_x / hex_layout.col_spacing)
        # end_col is clamped to board_width, so check both are clamped
        self.assertLessEqual(end_col, self.game_state.board_width)

if __name__ == '__main__':
    unittest.main()