"""
Hex layout calculations for proper hexagon positioning.
Handles the conversion between hex grid coordinates and pixel positions.
"""

import math
from typing import Tuple
from game.hex_utils import HexCoord, HexGrid


class HexLayout:
    """Manages hex positioning and layout calculations for a flat-top grid."""

    def __init__(self, hex_size: float = 36):
        """Initialize hex layout for a flat-top hex grid.

        Args:
            hex_size: Distance from center to any corner.
        """
        self.hex_size = hex_size

        # Flat-top hexagon measurements
        # Width is the distance between flat sides (horizontal)
        self.hex_width = math.sqrt(3) * hex_size
        # Height is the distance between points (vertical)
        self.hex_height = 2 * hex_size

        # For proper interlocking:
        # - Horizontal spacing between hex centers in same row = sqrt(3) * hex_size
        # - Vertical spacing between rows = 3/2 * hex_size
        # - Odd rows offset by half the column spacing
        self.col_spacing = math.sqrt(3) * hex_size  # Distance between centers
        self.row_spacing = 1.5 * hex_size  # 3/4 of height
        self.row_offset = self.col_spacing / 2  # Half column spacing for odd rows
    
    def hex_to_pixel(self, col: int, row: int) -> Tuple[float, float]:
        """
        Convert hex grid coordinates to pixel position (center of hex).
        Uses odd-r offset coordinates for a flat-top grid.
        
        Args:
            col: Column in hex grid
            row: Row in hex grid
            
        Returns:
            (x, y) pixel coordinates of hex center
        """
        # Flat-top with odd-r offset
        x = col * self.col_spacing
        y = row * self.row_spacing

        # Offset odd rows to the right
        if row % 2 == 1:
            x += self.row_offset
        
        return (x, y)
    
    def pixel_to_hex(self, x: float, y: float) -> Tuple[int, int]:
        """
        Convert pixel position to hex grid coordinates.
        
        Args:
            x: X pixel coordinate
            y: Y pixel coordinate
            
        Returns:
            (col, row) in hex grid
        """
        # For flat-top hexes
        # First approximation
        row = int(round(y / self.row_spacing))

        # Adjust x based on row offset
        adjusted_x = x
        if row % 2 == 1:
            adjusted_x -= self.row_offset

        col = int(round(adjusted_x / self.col_spacing))

        # Fine-tune using hex distance
        # Check the 4 nearest hex centers and pick closest
        candidates = [
            (col, row),
            (col - 1, row), (col + 1, row),
            (col, row - 1), (col, row + 1)
        ]

        best_col, best_row = col, row
        best_dist = float('inf')

        for c, r in candidates:
            if c >= 0 and r >= 0:  # Only positive coordinates
                hx, hy = self.hex_to_pixel(c, r)
                dist = math.sqrt((x - hx)**2 + (y - hy)**2)
                if dist < best_dist:
                    best_dist = dist
                    best_col, best_row = c, r

        return (best_col, best_row)
    
    def get_hex_corners(self, center_x: float, center_y: float) -> list:
        """
        Get the 6 corner points of a hex at given center position.
        
        Args:
            center_x: X coordinate of hex center
            center_y: Y coordinate of hex center
            
        Returns:
            List of (x, y) tuples for each corner
        """
        corners = []

        # Flat-top hex, first corner at 30 degrees
        angle_offset = 30
        
        for i in range(6):
            angle_deg = 60 * i + angle_offset
            angle_rad = math.radians(angle_deg)
            
            corner_x = center_x + self.hex_size * math.cos(angle_rad)
            corner_y = center_y + self.hex_size * math.sin(angle_rad)
            corners.append((corner_x, corner_y))
        
        return corners
    
    def get_neighbor_offsets(self) -> list:
        """
        Get the offset coordinate differences to reach each neighbor.
        
        Returns:
            List of (col_diff, row_diff) for each of the 6 neighbors
        """
        # For flat-top hex with odd-r offset
        # Even row neighbors
        even_row = [
            (1, 0),   # East
            (0, -1),  # Northeast
            (-1, -1), # Northwest
            (-1, 0),  # West
            (-1, 1),  # Southwest
            (0, 1)    # Southeast
        ]
        # Odd row neighbors (shifted due to offset)
        odd_row = [
            (1, 0),   # East
            (1, -1),  # Northeast
            (0, -1),  # Northwest
            (-1, 0),  # West
            (0, 1),   # Southwest
            (1, 1)    # Southeast
        ]
        return (even_row, odd_row)
