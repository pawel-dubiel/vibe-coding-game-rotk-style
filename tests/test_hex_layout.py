import unittest
import math
from game.hex_layout import HexLayout


class TestHexLayout(unittest.TestCase):
    def setUp(self):
        self.layout = HexLayout(hex_size=30, orientation='flat')
    
    def test_hex_dimensions(self):
        """Test that hex dimensions are calculated correctly"""
        # For hex_size = 30
        self.assertEqual(self.layout.hex_size, 30)
        self.assertAlmostEqual(self.layout.hex_width, 30 * math.sqrt(3))  # sqrt(3) * size
        self.assertEqual(self.layout.hex_height, 60)  # 2 * size
        
        # Spacing calculations
        self.assertAlmostEqual(self.layout.col_spacing, 30 * math.sqrt(3))  # sqrt(3) * size
        self.assertEqual(self.layout.row_spacing, 45)  # 1.5 * size
        self.assertAlmostEqual(self.layout.row_offset, 30 * math.sqrt(3) / 2)  # col_spacing / 2
    
    def test_hex_to_pixel_even_row(self):
        """Test pixel positioning for even row hexes"""
        # Hex at (0, 0)
        x, y = self.layout.hex_to_pixel(0, 0)
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)
        
        # Hex at (1, 0) - next column, same row
        x, y = self.layout.hex_to_pixel(1, 0)
        self.assertAlmostEqual(x, 30 * math.sqrt(3))  # col_spacing
        self.assertEqual(y, 0)
        
        # Hex at (2, 0)
        x, y = self.layout.hex_to_pixel(2, 0)
        self.assertAlmostEqual(x, 60 * math.sqrt(3))  # 2 * col_spacing
        self.assertEqual(y, 0)
    
    def test_hex_to_pixel_odd_row(self):
        """Test pixel positioning for odd row hexes with offset"""
        # Hex at (0, 1) - odd row, should be offset
        x, y = self.layout.hex_to_pixel(0, 1)
        self.assertAlmostEqual(x, 30 * math.sqrt(3) / 2)  # row_offset
        self.assertEqual(y, 45)  # row_spacing
        
        # Hex at (1, 1)
        x, y = self.layout.hex_to_pixel(1, 1)
        self.assertAlmostEqual(x, 30 * math.sqrt(3) * 1.5)  # col_spacing + row_offset
        self.assertEqual(y, 45)
    
    def test_neighbor_distances(self):
        """Test that all neighbors are equidistant from center hex"""
        # Get center hex position
        center_col, center_row = 5, 5
        cx, cy = self.layout.hex_to_pixel(center_col, center_row)
        
        # Get neighbor offsets
        even_offsets, odd_offsets = self.layout.get_neighbor_offsets()
        offsets = odd_offsets if center_row % 2 == 1 else even_offsets
        
        distances = []
        for dc, dr in offsets:
            neighbor_col = center_col + dc
            neighbor_row = center_row + dr
            nx, ny = self.layout.hex_to_pixel(neighbor_col, neighbor_row)
            
            # Calculate distance
            dist = math.sqrt((nx - cx)**2 + (ny - cy)**2)
            distances.append(dist)
        
        # All distances should be equal (within floating point tolerance)
        # For proper hex grid, all neighbors are at the same distance
        expected_dist = self.layout.col_spacing  # sqrt(3) * hex_size
        for i, dist in enumerate(distances):
            self.assertAlmostEqual(dist, expected_dist, places=5,
                                 msg=f"Neighbor {i} distance {dist} != expected {expected_dist}")
    
    def test_hex_corners(self):
        """Test that hex corners are positioned correctly"""
        corners = self.layout.get_hex_corners(100, 100)
        
        # Should have 6 corners
        self.assertEqual(len(corners), 6)
        
        # All corners should be hex_size distance from center
        for i, (cx, cy) in enumerate(corners):
            dist = math.sqrt((cx - 100)**2 + (cy - 100)**2)
            self.assertAlmostEqual(dist, self.layout.hex_size, places=5,
                                 msg=f"Corner {i} distance {dist} != hex_size {self.layout.hex_size}")
        
        # First corner should be at 30 degrees for flat-top
        # x = 100 + 30 * cos(30°) = 100 + 30 * sqrt(3)/2 ≈ 125.98
        # y = 100 + 30 * sin(30°) = 100 + 30 * 0.5 = 115
        self.assertAlmostEqual(corners[0][0], 100 + 30 * math.sqrt(3)/2, places=5)
        self.assertAlmostEqual(corners[0][1], 115, places=5)
    
    def test_pixel_to_hex_conversion(self):
        """Test converting pixel coordinates back to hex coordinates"""
        # Test some known positions
        test_cases = [
            ((0, 0), (0, 0)),      # Origin
            ((51.96, 0), (1, 0)),     # Next column (approximately sqrt(3)*30)
            ((25.98, 45), (0, 1)),  # First hex in odd row (approximately)
            ((103.92, 0), (2, 0)),     # Two columns over
        ]
        
        for (px, py), (expected_col, expected_row) in test_cases:
            col, row = self.layout.pixel_to_hex(px, py)
            self.assertEqual((col, row), (expected_col, expected_row),
                           f"Pixel ({px}, {py}) should map to hex ({expected_col}, {expected_row})")
    
    def test_interlocking_pattern(self):
        """Test that hexes properly interlock without gaps"""
        # In a proper hex grid, each hex should have exactly 6 neighbors
        # at the same distance, forming a honeycomb pattern
        
        # Test a 3x3 grid
        positions = {}
        for col in range(3):
            for row in range(3):
                x, y = self.layout.hex_to_pixel(col, row)
                positions[(col, row)] = (x, y)
        
        # Verify specific neighbor relationships
        # (1,1) should be surrounded by 6 hexes
        center = positions[(1, 1)]
        # For odd row (row 1), the neighbors are:
        neighbors = [
            positions.get((2, 1)),  # East
            positions.get((2, 0)),  # NE
            positions.get((1, 0)),  # NW
            positions.get((0, 1)),  # West
            positions.get((1, 2)),  # SW
            positions.get((2, 2)),  # SE
        ]
        
        # Check all neighbors exist and are at correct distance
        expected_dist = self.layout.col_spacing  # sqrt(3) * hex_size
        for neighbor in neighbors:
            if neighbor:  # Skip if out of our 3x3 grid
                dist = math.sqrt((neighbor[0] - center[0])**2 + 
                               (neighbor[1] - center[1])**2)
                self.assertAlmostEqual(dist, expected_dist, places=5)


class TestHexLayoutPointyTop(unittest.TestCase):
    """Test pointy-top orientation"""
    
    def setUp(self):
        self.layout = HexLayout(hex_size=30, orientation='pointy')
    
    def test_pointy_hex_dimensions(self):
        """Test dimensions for pointy-top hexes"""
        self.assertAlmostEqual(self.layout.hex_width, 30 * math.sqrt(3))
        self.assertEqual(self.layout.hex_height, 60)
        self.assertAlmostEqual(self.layout.col_spacing, 30 * math.sqrt(3))
        self.assertEqual(self.layout.row_spacing, 45)
        self.assertEqual(self.layout.row_offset, 30)  # hex_height / 2


if __name__ == '__main__':
    unittest.main()