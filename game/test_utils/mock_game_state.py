"""Mock game state for testing"""
from typing import List, Optional
from game.interfaces.game_state import IGameState
from game.terrain import TerrainMap

class MockGameState(IGameState):
    """Mock implementation of IGameState for testing"""
    
    def __init__(self, board_width: int = 20, board_height: int = 20,
                 create_terrain: bool = True):
        self._board_width = board_width
        self._board_height = board_height
        self._knights = []
        self._castles = []
        self._terrain_map = TerrainMap(board_width, board_height) if create_terrain else None
        self._current_player = 1
        
        # Additional test-specific attributes
        self.pending_positions = {}  # For tracking movement animations
        
    @property
    def board_width(self) -> int:
        return self._board_width
    
    @property
    def board_height(self) -> int:
        return self._board_height
    
    @property
    def knights(self) -> List:
        return self._knights
    
    @property
    def castles(self) -> List:
        return self._castles
    
    @property
    def terrain_map(self) -> Optional[TerrainMap]:
        return self._terrain_map
    
    @property
    def current_player(self) -> int:
        return self._current_player
    
    @current_player.setter
    def current_player(self, value: int):
        self._current_player = value
    
    def get_knight_at(self, x: int, y: int) -> Optional:
        """Get knight at specific position"""
        for knight in self._knights:
            if knight.x == x and knight.y == y and not getattr(knight, 'is_garrisoned', False):
                return knight
        return None
    
    def add_knight(self, knight):
        """Add a knight to the game state"""
        self._knights.append(knight)
        
    def remove_knight(self, knight):
        """Remove a knight from the game state"""
        if knight in self._knights:
            self._knights.remove(knight)
            
    def add_castle(self, castle):
        """Add a castle to the game state"""
        self._castles.append(castle)