"""Game state interface definition"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.entities.unit import Unit
    from game.entities.castle import Castle
    from game.terrain import TerrainMap

class IGameState(ABC):
    """Interface for game state implementations
    
    This interface defines the minimal contract that game state implementations
    must fulfill. Implementations should have these as instance attributes or properties:
    - board_width: int
    - board_height: int
    - knights: List[Unit]
    - castles: List[Castle]
    - terrain_map: Optional[TerrainMap]
    - current_player: int
    """
    
    # These will be checked at runtime via hasattr rather than abstract properties
    # This allows implementations to use either attributes or properties
    
    @abstractmethod
    def get_knight_at(self, x: int, y: int) -> Optional['Unit']:
        """Get knight/unit at specific position
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Unit at position or None
        """
        pass