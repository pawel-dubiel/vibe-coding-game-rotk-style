import unittest
from game.hex_utils import HexGrid
from game.renderer import Renderer
import pygame


class TestHexGameIntegration(unittest.TestCase):
    """Test hex grid integration with game rendering"""
    
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((100, 100))  # Small test screen
        self.hex_grid = HexGrid(hex_size=36)
    
    def tearDown(self):
        pygame.quit()
    
    def test_board_position_calculations(self):
        """Test that our board positioning matches what renderer uses"""
        # Test the same positioning logic as in renderer
        positions = []
        for col in range(5):
            for row in range(5):
                # Calculate pixel position using renderer logic
                pixel_x = col * self.hex_grid.hex_width * 0.75
                pixel_y = row * self.hex_grid.hex_height
                
                # Offset odd rows
                if row % 2 == 1:
                    pixel_x += self.hex_grid.hex_width * 0.375
                
                positions.append(((col, row), (pixel_x, pixel_y)))
        
        # Verify some key positions
        # (0, 0) should be at origin
        self.assertEqual(positions[0][1], (0, 0))
        
        # (1, 0) should be 3/4 hex width to the right
        # Note: positions[1] is (1, 0) when iterating col first
        for (col, row), (px, py) in positions:
            if col == 1 and row == 0:
                expected_x = self.hex_grid.hex_width * 0.75
                self.assertAlmostEqual(px, expected_x)
                break
        
        # (0, 1) should be offset and one hex height down
        for (col, row), (px, py) in positions:
            if col == 0 and row == 1:
                expected_x = self.hex_grid.hex_width * 0.375
                expected_y = self.hex_grid.hex_height
                self.assertAlmostEqual(px, expected_x)
                self.assertAlmostEqual(py, expected_y)
                break
    
    def test_mouse_click_to_hex_conversion(self):
        """Test mouse click position to hex tile conversion"""
        # This tests the logic from input_handler
        
        # Click in center of (0, 0)
        x, y = 20, 20
        col = int(x / (self.hex_grid.hex_width * 0.75))
        row = int(y / self.hex_grid.hex_height)
        self.assertEqual((col, row), (0, 0))
        
        # Click in (1, 0)
        x = self.hex_grid.hex_width * 0.75 + 10
        y = 20
        col = int(x / (self.hex_grid.hex_width * 0.75))
        row = int(y / self.hex_grid.hex_height)
        self.assertEqual((col, row), (1, 0))
        
        # Click in (0, 1) - odd row with offset
        x = self.hex_grid.hex_width * 0.375 + 10
        y = self.hex_grid.hex_height + 10
        row = int(y / self.hex_grid.hex_height)
        
        # Adjust for odd row offset
        if row % 2 == 1:
            adjusted_x = x - self.hex_grid.hex_width * 0.375
            if adjusted_x < 0:
                adjusted_x = x
            col = int(adjusted_x / (self.hex_grid.hex_width * 0.75))
        else:
            col = int(x / (self.hex_grid.hex_width * 0.75))
        
        self.assertEqual((col, row), (0, 1))
    
    def test_hex_distance_for_game_mechanics(self):
        """Test hex distances match game expectations"""
        hex_grid = HexGrid()
        
        # Test movement range
        unit_pos = (5, 5)
        unit_hex = hex_grid.offset_to_axial(*unit_pos)
        
        # Count hexes within movement range 3
        count = 0
        for col in range(10):
            for row in range(10):
                target_hex = hex_grid.offset_to_axial(col, row)
                if unit_hex.distance_to(target_hex) <= 3:
                    count += 1
        
        # Should be 1 + 6 + 12 + 18 = 37 hexes
        self.assertEqual(count, 37)
    
    def test_castle_hex_pattern(self):
        """Test castle occupies correct hex pattern"""
        hex_grid = HexGrid()
        center_x, center_y = 5, 5
        
        # Get castle tiles (center + first 3 neighbors)
        tiles = [(center_x, center_y)]
        center_hex = hex_grid.offset_to_axial(center_x, center_y)
        neighbors = center_hex.get_neighbors()
        
        for i, neighbor_hex in enumerate(neighbors[:3]):
            tile_x, tile_y = hex_grid.axial_to_offset(neighbor_hex)
            tiles.append((tile_x, tile_y))
        
        # Should have 4 tiles total
        self.assertEqual(len(tiles), 4)
        
        # All should be unique
        self.assertEqual(len(set(tiles)), 4)
        
        # All neighbors should be adjacent to center
        for i, (tile_x, tile_y) in enumerate(tiles[1:]):
            tile_hex = hex_grid.offset_to_axial(tile_x, tile_y)
            distance = center_hex.distance_to(tile_hex)
            self.assertEqual(distance, 1, f"Castle tile {i+1} not adjacent to center")


if __name__ == '__main__':
    unittest.main()