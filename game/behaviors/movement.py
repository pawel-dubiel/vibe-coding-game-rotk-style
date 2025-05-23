"""Movement behaviors for units"""
from typing import List, Tuple, Optional, Set
from collections import deque
import math
from game.components.base import Behavior
from game.pathfinding import PathFinder, DijkstraPathFinder, AStarPathFinder
from game.hex_utils import HexGrid

class MovementBehavior(Behavior):
    """Basic movement behavior"""
    
    def __init__(self, movement_range: int = 3, pathfinder: Optional[PathFinder] = None):
        super().__init__("move")
        self.movement_range = movement_range
        self.pathfinder = pathfinder or DijkstraPathFinder()
        
    def can_execute(self, unit, game_state) -> bool:
        """Check if unit can move"""
        if unit.action_points < 1 or unit.has_moved:  # Need at least 1 AP to move
            return False
            
        # Routing units always try to move
        if unit.is_routing:
            return True
            
        # Check if in enemy ZOC and can't disengage
        if unit.in_enemy_zoc and not self._can_disengage_from_zoc(unit):
            return False
            
        return True
        
    def get_ap_cost(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], unit, game_state) -> int:
        """Calculate AP cost for movement based on terrain and conditions"""
        # Base movement cost
        terrain_cost = 1.0
        if game_state.terrain_map:
            terrain_cost = float(game_state.terrain_map.get_movement_cost(to_pos[0], to_pos[1], unit.unit_class))
        
        # Diagonal movement costs more
        dx = abs(to_pos[0] - from_pos[0])
        dy = abs(to_pos[1] - from_pos[1])
        is_diagonal = dx > 0 and dy > 0
        
        if is_diagonal:
            terrain_cost = math.ceil(terrain_cost * 1.4)  # 40% more for diagonal, always round up
            
        # Penalty for moving in enemy ZOC
        if unit.in_enemy_zoc:
            terrain_cost += 1  # Extra AP to disengage
            
        # Penalty for breaking formation
        if self._would_break_formation(from_pos, to_pos, unit, game_state):
            terrain_cost += 1  # Formation breaking penalty
            
        return max(1, math.ceil(terrain_cost))  # Minimum 1 AP, always round up
        
    def execute(self, unit, game_state, target_x: int, target_y: int):
        """Execute movement to target position"""
        if not self.can_execute(unit, game_state):
            return {'success': False, 'reason': 'Cannot move'}
            
        # Validate target is within possible moves
        possible_moves = self.get_possible_moves(unit, game_state)
        if (target_x, target_y) not in possible_moves:
            return {'success': False, 'reason': 'Invalid target position'}
            
        # Calculate actual AP cost for this move
        ap_cost = self.get_ap_cost((unit.x, unit.y), (target_x, target_y), unit, game_state)
        
        # Check if we have enough AP
        if unit.action_points < ap_cost:
            return {'success': False, 'reason': 'Not enough action points'}
            
        # Consume AP and mark as moved
        unit.action_points -= ap_cost
        unit.has_moved = True
        
        return {
            'success': True,
            'from': (unit.x, unit.y),
            'to': (target_x, target_y),
            'animation': 'move'
        }
        
    def get_path_to(self, unit, game_state, target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Get the optimal path to a specific destination"""
        if not self.can_execute(unit, game_state):
            return []
            
        # Use pathfinder with custom cost calculation
        # We need to wrap the pathfinder to use our AP cost calculation
        original_get_cost = self.pathfinder._get_movement_cost
        
        def custom_get_cost(from_pos, to_pos, game_state, unit):
            return self.get_ap_cost(from_pos, to_pos, unit, game_state)
        
        # Temporarily replace the cost function
        self.pathfinder._get_movement_cost = custom_get_cost
        
        try:
            # Find path with AP limit
            path = self.pathfinder.find_path(
                start=(unit.x, unit.y),
                end=(target_x, target_y),
                game_state=game_state,
                unit=unit,
                max_cost=unit.action_points
            )
            return path or []
        finally:
            # Restore original cost function
            self.pathfinder._get_movement_cost = original_get_cost
    
    def get_possible_moves(self, unit, game_state) -> List[Tuple[int, int]]:
        """Calculate possible movement positions using pathfinding algorithm"""
        if not self.can_execute(unit, game_state):
            return []
            
        # Special handling for units in ZOC
        if unit.in_enemy_zoc and not self._can_disengage_from_zoc(unit):
            # Can only move to attack the engaging enemy
            if unit.engaged_with:
                return [(unit.engaged_with.x, unit.engaged_with.y)]
            return []
            
        # Routing units move differently
        if unit.is_routing:
            return self._get_routing_moves(unit, game_state)
            
        # Use Dijkstra pathfinder to find all reachable positions
        if isinstance(self.pathfinder, DijkstraPathFinder):
            # We need to wrap the pathfinder to use our AP cost calculation
            original_get_cost = self.pathfinder._get_movement_cost
            
            def custom_get_cost(from_pos, to_pos, game_state, unit):
                base_cost = self.get_ap_cost(from_pos, to_pos, unit, game_state)
                # Don't modify cost here - we'll handle ZOC in the filtering step
                return base_cost
            
            # Temporarily replace the cost function
            self.pathfinder._get_movement_cost = custom_get_cost
            
            try:
                # Find all reachable positions within AP limit
                reachable = self.pathfinder.find_all_reachable(
                    start=(unit.x, unit.y),
                    game_state=game_state,
                    unit=unit,
                    max_cost=unit.action_points
                )
                
                # Filter out starting position and positions that would enter ZOC
                moves = []
                for pos, cost in reachable.items():
                    if pos != (unit.x, unit.y) and cost <= unit.action_points:
                        # Check if position is valid
                        if self._will_enter_enemy_zoc(pos[0], pos[1], unit, game_state):
                            # Allow entering ZOC if it's adjacent to current position
                            # This allows units to approach and attack enemies
                            hex_grid = HexGrid()
                            start_hex = hex_grid.offset_to_axial(unit.x, unit.y)
                            end_hex = hex_grid.offset_to_axial(pos[0], pos[1])
                            
                            # If adjacent (distance 1 in hex), allow the move
                            if start_hex.distance_to(end_hex) == 1:
                                moves.append(pos)
                        else:
                            # Not entering ZOC, so move is allowed
                            moves.append(pos)
                
                return moves
            finally:
                # Restore original cost function
                self.pathfinder._get_movement_cost = original_get_cost
        else:
            # For other pathfinders, use a simple range-based approach
            moves = []
            hex_grid = HexGrid()
            start_hex = hex_grid.offset_to_axial(unit.x, unit.y)
            
            # Check all positions within movement range
            for hex_coord in start_hex.get_neighbors_within_range(self.movement_range):
                offset_pos = hex_grid.axial_to_offset(hex_coord)
                x, y = offset_pos
                
                if (0 <= x < game_state.board_width and 
                    0 <= y < game_state.board_height and
                    (x, y) != (unit.x, unit.y)):
                    
                    # Use pathfinder to check if reachable
                    path = self.pathfinder.find_path(
                        start=(unit.x, unit.y),
                        end=(x, y),
                        game_state=game_state,
                        unit=unit,
                        max_cost=unit.action_points
                    )
                    if path:
                        moves.append((x, y))
            return moves
        
    def _would_break_formation(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], unit, game_state) -> bool:
        """Check if this move would break formation"""
        # Check if we start adjacent to friendly units
        has_friendly_at_start = self._has_adjacent_friendly(from_pos[0], from_pos[1], unit, game_state)
        if not has_friendly_at_start:
            return False  # No formation to break
            
        # Check if we'll still be adjacent to friendlies after move
        has_friendly_at_end = self._has_adjacent_friendly(to_pos[0], to_pos[1], unit, game_state)
        
        return not has_friendly_at_end  # Breaking formation if no longer adjacent
        
    def _can_disengage_from_zoc(self, unit) -> bool:
        """Check if unit can disengage from Zone of Control"""
        # High morale units can disengage
        return unit.morale >= 75
        
    def _is_enemy_at(self, x: int, y: int, unit, game_state) -> bool:
        """Check if enemy unit is at position"""
        for other in game_state.knights:
            if other.player_id != unit.player_id and other.x == x and other.y == y:
                return True
        return False
        
    def _has_adjacent_friendly(self, x: int, y: int, unit, game_state) -> bool:
        """Check if position has adjacent friendly units"""
        # Check all 8 directions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            check_x, check_y = x + dx, y + dy
            for other in game_state.knights:
                if (other.player_id == unit.player_id and 
                    other != unit and
                    other.x == check_x and 
                    other.y == check_y and
                    not other.is_routing):
                    return True
        return False
        
    def _will_enter_enemy_zoc(self, x: int, y: int, unit, game_state) -> bool:
        """Check if moving to position would enter enemy ZOC"""
        for enemy in game_state.knights:
            if (enemy.player_id != unit.player_id and 
                enemy.has_zone_of_control()):
                # Check if adjacent (including diagonals)
                dx = abs(x - enemy.x)
                dy = abs(y - enemy.y)
                if dx <= 1 and dy <= 1 and (dx + dy > 0):  # Adjacent including diagonals
                    return True
        return False
        
    def _get_routing_moves(self, unit, game_state) -> List[Tuple[int, int]]:
        """Get movement options for routing units (away from enemies)"""
        moves = []
        board_width = game_state.board_width
        board_height = game_state.board_height
        
        # Find nearest enemies
        enemies = [k for k in game_state.knights if k.player_id != unit.player_id]
        if not enemies:
            return []
            
        # Try to move away from nearest enemy
        nearest_enemy = min(enemies, key=lambda e: abs(e.x - unit.x) + abs(e.y - unit.y))
        
        # Check all 8 directions for routing
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_x, new_y = unit.x + dx, unit.y + dy
            
            if not (0 <= new_x < board_width and 0 <= new_y < board_height):
                continue
                
            # Check if this moves away from nearest enemy
            current_dist = abs(unit.x - nearest_enemy.x) + abs(unit.y - nearest_enemy.y)
            new_dist = abs(new_x - nearest_enemy.x) + abs(new_y - nearest_enemy.y)
            
            if new_dist > current_dist and not self._is_enemy_at(new_x, new_y, unit, game_state):
                moves.append((new_x, new_y))
                
        return moves