"""
Centralized movement service - single source of truth for all movement logic.

Consolidates movement calculations, validation, and execution from unit.py, 
movement.py, and game_state.py. Eliminates code duplication and ensures consistency.
"""
from typing import List, Tuple, Optional
from game.pathfinding import PathFinder, DijkstraPathFinder
from game.hex_utils import HexGrid


class MovementService:
    """Centralized service for all movement operations and validation."""
    
    def __init__(self):
        self.hex_grid = HexGrid()
    
    def get_possible_moves(self, unit, game_state) -> List[Tuple[int, int]]:
        """
        Get all valid movement positions for a unit.
        
        This is the single source of truth for movement validation,
        replacing duplicate logic across multiple files.
        """
        # Check if unit can move at all
        if not self._can_unit_move(unit):
            return []
        
        # Get movement behavior
        movement_behavior = unit.behaviors.get('move')
        if not movement_behavior:
            return []
        
        # Get raw possible moves from behavior
        raw_moves = movement_behavior.get_possible_moves(unit, game_state)
        
        # Apply game state validation filters
        valid_moves = self._filter_valid_moves(raw_moves, unit, game_state)
        
        return valid_moves
    
    def can_move_to_position(self, unit, target_x: int, target_y: int, game_state) -> bool:
        """Check if unit can move to a specific position."""
        possible_moves = self.get_possible_moves(unit, game_state)
        return (target_x, target_y) in possible_moves
    
    def get_movement_path(self, unit, target_x: int, target_y: int, game_state) -> Optional[List[Tuple[int, int]]]:
        """Get the movement path to reach a target position."""
        movement_behavior = unit.behaviors.get('move')
        if not movement_behavior or not hasattr(movement_behavior, 'pathfinder'):
            return None
        
        # Use the pathfinder to get the actual path
        path = movement_behavior.pathfinder.find_path(
            start=(unit.x, unit.y),
            end=(target_x, target_y),
            game_state=game_state,
            unit=unit
        )
        
        return path
    
    def calculate_movement_cost(self, unit, from_pos: Tuple[int, int], to_pos: Tuple[int, int], game_state) -> float:
        """Calculate AP cost for movement between two positions."""
        movement_behavior = unit.behaviors.get('move')
        if not movement_behavior:
            return float('inf')  # Can't move without movement behavior
        
        return movement_behavior.get_ap_cost(from_pos, to_pos, unit, game_state)
    
    def execute_movement(self, unit, target_x: int, target_y: int, game_state) -> bool:
        """
        Execute movement to target position.
        
        Returns True if movement was successful, False otherwise.
        """
        if not self.can_move_to_position(unit, target_x, target_y, game_state):
            return False
        
        movement_behavior = unit.behaviors.get('move')
        if not movement_behavior:
            return False
        
        # Calculate path and cost
        path = self.get_movement_path(unit, target_x, target_y, game_state)
        if not path:
            return False
        
        # Calculate total AP cost
        total_cost = 0
        current_pos = (unit.x, unit.y)
        for next_pos in path[1:]:  # Skip starting position
            cost = self.calculate_movement_cost(unit, current_pos, next_pos, game_state)
            total_cost += cost
            current_pos = next_pos
        
        # Check if unit has enough AP
        if total_cost > unit.action_points:
            return False
        
        # Execute the movement
        success = movement_behavior.execute(unit, (target_x, target_y), game_state)
        
        if success:
            # Update unit position and consume AP
            unit.x = target_x
            unit.y = target_y
            unit.action_points -= total_cost
            unit.has_moved = True
            
            # Update game state tracking
            if hasattr(game_state, 'pending_positions'):
                game_state.pending_positions[id(unit)] = (target_x, target_y)
            
            # Store movement history for display
            if hasattr(game_state, 'movement_history'):
                if path:
                    full_path = [(unit.x, unit.y)] + path
                    game_state.movement_history[id(unit)] = full_path
                else:
                    game_state.movement_history[id(unit)] = [(unit.x, unit.y), (target_x, target_y)]
        
        return success
    
    def _can_unit_move(self, unit) -> bool:
        """Check basic movement prerequisites for a unit."""
        if not unit:
            return False
        
        # Unit must have action points
        if unit.action_points <= 0:
            return False
        
        # Unit must not have already moved (if using turn-based restrictions)
        if hasattr(unit, 'has_moved') and unit.has_moved:
            return False
        
        # Garrisoned units can't move
        if hasattr(unit, 'is_garrisoned') and unit.is_garrisoned:
            return False
        
        return True
    
    def _filter_valid_moves(self, moves: List[Tuple[int, int]], unit, game_state) -> List[Tuple[int, int]]:
        """Filter moves based on game state constraints (occupied positions, etc.)."""
        valid_moves = []
        
        for move_x, move_y in moves:
            if not self._is_position_occupied(move_x, move_y, unit, game_state):
                valid_moves.append((move_x, move_y))
        
        return valid_moves
    
    def _is_position_occupied(self, x: int, y: int, exclude_unit, game_state) -> bool:
        """Check if a position is occupied by units, castles, or pending moves."""
        # Check castle positions
        for castle in game_state.castles:
            if castle.contains_position(x, y):
                return True
        
        # Check current unit positions (excluding garrisoned units)
        for unit in game_state.knights:
            if (unit != exclude_unit and 
                not getattr(unit, 'is_garrisoned', False) and 
                unit.x == x and unit.y == y):
                return True
        
        # Check pending positions (units that are moving in animations)
        if hasattr(game_state, 'pending_positions'):
            for unit_id, pos in game_state.pending_positions.items():
                if pos == (x, y):
                    # Make sure this pending position is not from the excluded unit
                    for unit in game_state.knights:
                        if id(unit) == unit_id and unit != exclude_unit:
                            return True
        
        return False
    
    def get_movement_range(self, unit) -> int:
        """Get the base movement range for a unit."""
        movement_behavior = unit.behaviors.get('move')
        if not movement_behavior:
            return 0
        
        return getattr(movement_behavior, 'movement_range', 0)
    
    def consume_movement_ap(self, unit, amount: float = 1.0):
        """Consume action points for movement."""
        unit.action_points = max(0, unit.action_points - amount)
        unit.has_moved = True
    
    def reset_movement_status(self, unit):
        """Reset movement status for new turn."""
        unit.has_moved = False
        # Don't reset action points here - that's handled elsewhere