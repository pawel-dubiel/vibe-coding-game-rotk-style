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

