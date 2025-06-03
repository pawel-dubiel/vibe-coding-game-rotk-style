"""
Victory condition checking and game completion detection.

Handles all win/loss conditions including unit elimination and castle destruction.
Extracted from GameState for better testability and single responsibility.
"""
from typing import Optional, List
from game.entities.unit import Unit
from game.entities.castle import Castle


class VictoryManager:
    """Manages victory condition checking and game completion detection."""
    
    def __init__(self):
        self.victory_conditions = ['unit_elimination', 'castle_destruction']
    
    def check_victory(self, units: List[Unit], castles: List[Castle]) -> Optional[int]:
        """
        Check for victory conditions and return winning player ID.
        
        Args:
            units: List of all units in the game
            castles: List of all castles in the game
            
        Returns:
            Player ID of winner (1 or 2), or None if game continues
        """
        # Check unit elimination victory
        player1_units = [u for u in units if u.player_id == 1]
        player2_units = [u for u in units if u.player_id == 2]
        
        if not player1_units:
            return 2  # Player 2 wins by eliminating all Player 1 units
        elif not player2_units:
            return 1  # Player 1 wins by eliminating all Player 2 units
            
        # Check castle destruction victory (if castles exist)
        if castles:
            player1_castles = [c for c in castles if c.player_id == 1]
            player2_castles = [c for c in castles if c.player_id == 2]
            
            # Player loses if all their castles are destroyed
            if player1_castles and all(c.is_destroyed() for c in player1_castles):
                return 2  # Player 2 wins by destroying all Player 1 castles
            elif player2_castles and all(c.is_destroyed() for c in player2_castles):
                return 1  # Player 1 wins by destroying all Player 2 castles
        
        return None  # Game continues
    
    def get_victory_summary(self, winner: int, units: List[Unit], castles: List[Castle]) -> str:
        """Generate a summary of how the victory was achieved."""
        if winner is None:
            return "Game continues"
            
        loser = 2 if winner == 1 else 1
        
        # Check what caused the victory
        player_units = [u for u in units if u.player_id == loser]
        player_castles = [c for c in castles if c.player_id == loser]
        
        if not player_units:
            return f"Player {winner} wins by eliminating all enemy units!"
        elif player_castles and all(c.is_destroyed() for c in player_castles):
            return f"Player {winner} wins by destroying all enemy castles!"
        else:
            return f"Player {winner} wins!"
    
    def is_game_over(self, units: List[Unit], castles: List[Castle]) -> bool:
        """Check if the game has ended (any victory condition met)."""
        return self.check_victory(units, castles) is not None
    
    def get_player_status(self, player_id: int, units: List[Unit], castles: List[Castle]) -> dict:
        """Get detailed status for a specific player."""
        player_units = [u for u in units if u.player_id == player_id]
        player_castles = [c for c in castles if c.player_id == player_id]
        
        return {
            'player_id': player_id,
            'unit_count': len(player_units),
            'active_units': len([u for u in player_units if not u.is_routing]),
            'routing_units': len([u for u in player_units if u.is_routing]),
            'castle_count': len(player_castles),
            'destroyed_castles': len([c for c in player_castles if c.is_destroyed()]),
            'is_eliminated': len(player_units) == 0,
            'has_lost_all_castles': player_castles and all(c.is_destroyed() for c in player_castles)
        }