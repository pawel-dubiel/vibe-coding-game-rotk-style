"""
Hex layout calculations for proper hexagon positioning.
Handles the conversion between hex grid coordinates and pixel positions.
"""

import math
from typing import Tuple
from game.hex_utils import HexCoord, HexGrid


class HexLayout:
    """Manages hex positioning and layout calculations"""
    
    def __init__(self, hex_size: float = 36, orientation: str = 'flat'):
        """
        Initialize hex layout.
        
        Args:
            hex_size: Distance from center to any corner
            orientation: 'flat' for flat-top or 'pointy' for pointy-top
        """
        self.hex_size = hex_size
        self.orientation = orientation
        
        if orientation == 'flat':
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
        else:
            # Pointy-top hexagon measurements
            self.hex_width = math.sqrt(3) * hex_size
            self.hex_height = 2 * hex_size
            
            # For pointy-top:
            # - Horizontal spacing = hex_width
            # - Vertical spacing = 3/2 * hex_size
            # - Odd columns offset by hex_height / 2
            self.col_spacing = self.hex_width
            self.row_spacing = 1.5 * hex_size
            self.row_offset = self.hex_height / 2
    
    def hex_to_pixel(self, col: int, row: int) -> Tuple[float, float]:
        """
        Convert hex grid coordinates to pixel position (center of hex).
        Uses offset coordinates (odd-r for flat-top, odd-q for pointy-top).
        
        Args:
            col: Column in hex grid
            row: Row in hex grid
            
        Returns:
            (x, y) pixel coordinates of hex center
        """
        if self.orientation == 'flat':
            # Flat-top with odd-r offset
            x = col * self.col_spacing
            y = row * self.row_spacing
            
            # Offset odd rows to the right
            if row % 2 == 1:
                x += self.row_offset
        else:
            # Pointy-top with odd-q offset
            x = col * self.col_spacing
            y = row * self.row_spacing
            
            # Offset odd columns down
            if col % 2 == 1:
                y += self.row_offset
        
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
        if self.orientation == 'flat':
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
        else:
            # For pointy-top hexes
            col = int(round(x / self.col_spacing))
            
            # Adjust y based on column offset
            adjusted_y = y
            if col % 2 == 1:
                adjusted_y -= self.row_offset
            
            row = int(round(adjusted_y / self.row_spacing))
            
            return (col, row)
    
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
        
        if self.orientation == 'flat':
            # Flat-top hex, first corner at 30 degrees
            angle_offset = 30
        else:
            # Pointy-top hex, first corner at 0 degrees
            angle_offset = 0
        
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
        if self.orientation == 'flat':
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
        else:
            # For pointy-top hex with odd-q offset
            # Even column neighbors
            even_col = [
                (0, -1),  # North
                (1, -1),  # Northeast
                (1, 0),   # Southeast
                (0, 1),   # South
                (-1, 0),  # Southwest
                (-1, -1)  # Northwest
            ]
            # Odd column neighbors
            odd_col = [
                (0, -1),  # North
                (1, 0),   # Northeast
                (1, 1),   # Southeast
                (0, 1),   # South
                (-1, 1),  # Southwest
                (-1, 0)   # Northwest
            ]
            return (even_col, odd_col)