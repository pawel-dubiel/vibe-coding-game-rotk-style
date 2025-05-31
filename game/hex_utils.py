import math
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class HexCoord:
    """Hexagonal coordinate using axial coordinates (q, r)"""
    q: int  # Column
    r: int  # Row
    
    def __eq__(self, other):
        return self.q == other.q and self.r == other.r
    
    def __hash__(self):
        return hash((self.q, self.r))
    
    def to_cube(self) -> Tuple[int, int, int]:
        """Convert axial to cube coordinates"""
        x = self.q
        z = self.r
        y = -x - z
        return (x, y, z)
    
    def distance_to(self, other: 'HexCoord') -> int:
        """Calculate hex distance between two coordinates"""
        return (abs(self.q - other.q) + 
                abs(self.q + self.r - other.q - other.r) + 
                abs(self.r - other.r)) // 2
    
    def get_neighbors(self) -> List['HexCoord']:
        """Get all 6 neighboring hex coordinates"""
        directions = [
            HexCoord(1, 0), HexCoord(1, -1), HexCoord(0, -1),
            HexCoord(-1, 0), HexCoord(-1, 1), HexCoord(0, 1)
        ]
        return [HexCoord(self.q + d.q, self.r + d.r) for d in directions]
    
    def get_neighbors_within_range(self, distance: int) -> List['HexCoord']:
        """Get all hex coordinates within given distance"""
        results = []
        for q in range(-distance, distance + 1):
            for r in range(max(-distance, -q - distance), min(distance, -q + distance) + 1):
                results.append(HexCoord(self.q + q, self.r + r))
        return results


class HexGrid:
    """Hexagonal grid with flat-top orientation using odd-r offset coordinates"""
    
    def __init__(self, hex_size: float = 32):
        self.hex_size = hex_size
        self.hex_width = 2 * hex_size
        self.hex_height = math.sqrt(3) * hex_size
        
    def hex_to_pixel(self, hex_coord: HexCoord, offset_coords: bool = False) -> Tuple[float, float]:
        """Convert hex coordinates to pixel coordinates
        
        Args:
            hex_coord: The hex coordinate to convert
            offset_coords: If True, apply offset for odd columns (for offset coordinate system)
        """
        x = self.hex_size * (math.sqrt(3) * hex_coord.q + math.sqrt(3)/2 * hex_coord.r)
        y = self.hex_size * (3/2 * hex_coord.r)
        return (x, y)
    
    def pixel_to_hex(self, x: float, y: float) -> HexCoord:
        """Convert pixel coordinates to hex coordinates"""
        q = (2/3 * x) / self.hex_size
        r = (-1/3 * x + math.sqrt(3)/3 * y) / self.hex_size
        return self._round_hex(q, r)
    
    def _round_hex(self, q: float, r: float) -> HexCoord:
        """Round fractional hex coordinates to nearest hex"""
        s = -q - r
        rq = round(q)
        rr = round(r)
        rs = round(s)
        
        q_diff = abs(rq - q)
        r_diff = abs(rr - r)
        s_diff = abs(rs - s)
        
        if q_diff > r_diff and q_diff > s_diff:
            rq = -rr - rs
        elif r_diff > s_diff:
            rr = -rq - rs
            
        return HexCoord(int(rq), int(rr))
    
    def get_hex_corners(self, center_x: float, center_y: float) -> List[Tuple[float, float]]:
        """Get the 6 corner points of a hex at given pixel position"""
        corners = []
        for i in range(6):
            angle_deg = 60 * i  # Start at right point for flat-top
            angle_rad = math.pi / 180 * angle_deg
            corner_x = center_x + self.hex_size * math.cos(angle_rad)
            corner_y = center_y + self.hex_size * math.sin(angle_rad)
            corners.append((corner_x, corner_y))
        return corners
    
    def is_valid_coord(self, hex_coord: HexCoord, width: int, height: int) -> bool:
        """Check if hex coordinate is within rectangular bounds"""
        # Convert to offset coordinates for bounds checking
        col = hex_coord.q
        row = hex_coord.r + (hex_coord.q - (hex_coord.q & 1)) // 2
        return 0 <= col < width and 0 <= row < height
    
    def offset_to_axial(self, col: int, row: int) -> HexCoord:
        """Convert offset coordinates to axial hex coordinates (odd-r offset)"""
        q = col - (row - (row & 1)) // 2
        r = row
        return HexCoord(q, r)
    
    def axial_to_offset(self, hex_coord: HexCoord) -> Tuple[int, int]:
        """Convert axial hex coordinates to offset coordinates (odd-r offset)"""
        col = hex_coord.q + (hex_coord.r - (hex_coord.r & 1)) // 2
        row = hex_coord.r
        return (col, row)
    
    @staticmethod
    def get_line(start: HexCoord, end: HexCoord) -> List[HexCoord]:
        """Get a line of hexes between two points (from Red Blob Games)"""
        distance = start.distance_to(end)
        results = []
        
        if distance == 0:
            return [start]
            
        # Linear interpolation in cube coordinates
        for i in range(distance + 1):
            t = i / distance
            
            # Convert to cube coordinates
            start_cube = start.to_cube()
            end_cube = end.to_cube()
            
            # Interpolate
            x = start_cube[0] + (end_cube[0] - start_cube[0]) * t
            y = start_cube[1] + (end_cube[1] - start_cube[1]) * t
            z = start_cube[2] + (end_cube[2] - start_cube[2]) * t
            
            # Round to nearest hex
            rx = round(x)
            ry = round(y)
            rz = round(z)
            
            # Fix rounding errors
            x_diff = abs(rx - x)
            y_diff = abs(ry - y)
            z_diff = abs(rz - z)
            
            if x_diff > y_diff and x_diff > z_diff:
                rx = -ry - rz
            elif y_diff > z_diff:
                ry = -rx - rz
            else:
                rz = -rx - ry
                
            # Convert back to axial
            results.append(HexCoord(rx, rz))
            
        return results