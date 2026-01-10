"""Movement behaviors for units"""
from typing import List, Tuple, Optional, Set
from collections import deque
import math
from game.components.base import Behavior
from game.pathfinding import PathFinder, DijkstraPathFinder, AStarPathFinder
from game.hex_utils import HexGrid
from game.entities.knight import KnightClass
from game.visibility import VisibilityState

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
        
        if unit.is_routing:
            return False
            
        # Units can always move - ZOC restrictions are handled in get_possible_moves
        # This allows units to enter ZOC to engage enemies
        return True
        
    def get_ap_cost(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], unit, game_state) -> int:
        """Calculate AP cost for movement based on terrain and conditions"""
        # Base movement cost
        terrain_cost = 1.0
        if game_state.terrain_map:
            terrain_cost = float(game_state.terrain_map.get_movement_cost(to_pos[0], to_pos[1], unit))
        
        # Penalty for moving in enemy ZOC
        if unit.in_enemy_zoc:
            terrain_cost += 1  # Extra AP to disengage
            
        # Penalty for breaking formation
        if self._would_break_formation(from_pos, to_pos, unit, game_state):
            terrain_cost += 1  # Formation breaking penalty
            
        # Handle impassable terrain
        if terrain_cost == float('inf'):
            return 999  # Very high cost to indicate impassable terrain
            
        return max(1, math.ceil(terrain_cost))  # Minimum 1 AP, always round up
        
    def execute(self, unit, game_state, target_x: int, target_y: int, final_facing: Optional[int] = None):
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
            
        # Store original position
        from_x, from_y = unit.x, unit.y
        
        # Consume AP and mark as moved
        unit.action_points -= ap_cost
        unit.has_moved = True
        
        # Update unit position (normally done by animation, but needed for facing calculation)
        unit.x = target_x
        unit.y = target_y

        if hasattr(game_state, 'fog_of_war'):
            game_state.fog_of_war.reveal_unit_visibility(game_state, unit)
        
        # Check if we should auto-face an enemy
        should_auto_face = self._should_auto_face_enemy(target_x, target_y, unit, game_state)
        
        if should_auto_face:
            # Auto-face nearest enemy
            self._auto_face_nearest_enemy(target_x, target_y, unit, game_state)
        elif final_facing is not None and hasattr(unit, 'facing'):
            # Apply user-selected final facing (limited to 60 degree turn)
            # First update facing based on movement
            unit.facing.update_facing_from_movement(from_x, from_y, target_x, target_y)
            current_facing = unit.facing.facing.value
            
            # Then check if the requested facing is within 60 degrees (1 hex face)
            if self._is_valid_rotation(current_facing, final_facing):
                from game.components.facing import FacingDirection
                unit.facing.facing = FacingDirection(final_facing)
        else:
            # Default: update facing based on movement direction
            if hasattr(unit, 'facing'):
                unit.facing.update_facing_from_movement(from_x, from_y, target_x, target_y)
        
        return {
            'success': True,
            'from': (from_x, from_y),
            'to': (target_x, target_y),
            'animation': 'move',
            'auto_faced': should_auto_face
        }
        
    def get_path_to(self, unit, game_state, target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Get the optimal path to a specific destination"""
        if not self.can_execute(unit, game_state):
            return []
            
        # Define custom cost function for ZOC
        def custom_get_cost(from_pos, to_pos, game_state, unit):
            base = self.get_ap_cost(from_pos, to_pos, unit, game_state)
            if self._zoc_transition_blocked(from_pos, to_pos, unit, game_state):
                return float('inf')
            return base
        
        # Find path with AP limit and custom cost function
        path = self.pathfinder.find_path(
            start=(unit.x, unit.y),
            end=(target_x, target_y),
            game_state=game_state,
            unit=unit,
            max_cost=unit.action_points,
            cost_function=custom_get_cost
        )
        if not path:
            print(f"DEBUG: get_path_to failed for {unit.name} to ({target_x}, {target_y}). AP: {unit.action_points}")
        return path or []
    
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
            
        # Define custom cost function for ZOC
        def custom_get_cost(from_pos, to_pos, game_state, unit):
            base_cost = self.get_ap_cost(from_pos, to_pos, unit, game_state)
            if self._zoc_transition_blocked(from_pos, to_pos, unit, game_state):
                return float('inf')
            return base_cost

        # Use Dijkstra pathfinder to find all reachable positions
        if isinstance(self.pathfinder, DijkstraPathFinder):
            # Find all reachable positions within AP limit using custom cost function
            reachable = self.pathfinder.find_all_reachable(
                start=(unit.x, unit.y),
                game_state=game_state,
                unit=unit,
                max_cost=unit.action_points,
                cost_function=custom_get_cost
            )
            
            # Filter out starting position
            moves = []
            for pos, cost in reachable.items():
                if pos != (unit.x, unit.y) and cost <= unit.action_points:
                    # Units can move into enemy ZOC to engage - no restrictions on entering ZOC
                    # ZOC only restricts movement when you're already IN enemy ZOC
                    moves.append(pos)
            
            return moves
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
                    
                    path = self.pathfinder.find_path(
                        start=(unit.x, unit.y),
                        end=(x, y),
                        game_state=game_state,
                        unit=unit,
                        max_cost=unit.action_points,
                        cost_function=custom_get_cost
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
        # Routing units always try to move
        if unit.is_routing:
            return True
            
        # Cavalry can sometimes disengage using special ability (check this first!)
        if hasattr(unit, 'unit_class'):
            from game.entities.knight import KnightClass
            if unit.unit_class == KnightClass.CAVALRY:
                # Cavalry with high morale can attempt to disengage
                if unit.morale >= 75:
                    return True
        
        # Check if unit is heavy and engaged with another heavy unit
        if hasattr(unit, 'is_heavy_unit') and unit.is_heavy_unit():
            # Check if engaged with a heavy enemy
            if hasattr(unit, 'engaged_with') and unit.engaged_with:
                enemy = unit.engaged_with
                if hasattr(enemy, 'is_heavy_unit') and enemy.is_heavy_unit():
                    # Heavy units cannot disengage from other heavy units unless routing
                    return False
        
        # If engaged with an enemy, check breakaway rules
        if hasattr(unit, 'engaged_with') and unit.engaged_with:
            # Check if unit can break away based on unit types
            if hasattr(unit, 'can_break_away_from'):
                return unit.can_break_away_from(unit.engaged_with)
                
        # Other units can attempt to disengage (will use breakaway behavior)
        return True
        
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
        from game.systems.engagement import EngagementSystem
        in_zoc, _ = EngagementSystem.is_tile_in_enemy_zoc(x, y, unit, game_state)
        return in_zoc

    def _is_enemy_zoc_tile(self, x: int, y: int, unit, game_state) -> bool:
        """Check if a tile is inside enemy ZOC"""
        from game.systems.engagement import EngagementSystem
        in_zoc, _ = EngagementSystem.is_tile_in_enemy_zoc(x, y, unit, game_state)
        return in_zoc

    def _zoc_transition_blocked(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int],
                                unit, game_state) -> bool:
        """Check if moving from one tile to another violates ZOC rules"""
        # Only restrict if unit is currently outside enemy ZOC
        if unit.in_enemy_zoc:
            return False

        from_in_zoc = self._is_enemy_zoc_tile(from_pos[0], from_pos[1], unit, game_state)
        to_in_zoc = self._is_enemy_zoc_tile(to_pos[0], to_pos[1], unit, game_state)

        # Once we enter enemy ZOC we cannot leave in the same movement
        if from_in_zoc and not to_in_zoc and not self._is_enemy_at(to_pos[0], to_pos[1], unit, game_state):
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
        
    def get_auto_face_target(self, unit, game_state, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get the coordinates of the enemy to face, if any"""
        candidates = self._get_auto_face_candidates(unit, game_state, x, y)
        if candidates:
            nearest_distance = min(distance for _, distance in candidates)
            nearest_candidates = [enemy for enemy, distance in candidates if distance == nearest_distance]

            # Prioritize threats: Cavalry > Warrior > Mage > Archer
            threat_priority = {
                KnightClass.CAVALRY: 4,
                KnightClass.WARRIOR: 3,
                KnightClass.MAGE: 2,
                KnightClass.ARCHER: 1
            }

            nearest_candidates.sort(key=lambda e: threat_priority.get(e.unit_class, 0), reverse=True)
            nearest_enemy = nearest_candidates[0]
            return (nearest_enemy.x, nearest_enemy.y)
        return None

    def _should_auto_face_enemy(self, x: int, y: int, unit, game_state) -> bool:
        """Check if unit should automatically face an enemy after movement"""
        return bool(self._get_auto_face_candidates(unit, game_state, x, y))

    def _get_viewer_player_id(self, game_state) -> int:
        """Get viewer player id for fog-based visibility checks."""
        if hasattr(game_state, 'fog_view_player'):
            viewer_player = game_state.fog_view_player
            if viewer_player is None:
                raise ValueError("fog_view_player is None for visibility checks")
            return viewer_player
        if hasattr(game_state, 'current_player'):
            return game_state.current_player
        raise ValueError("game_state missing fog_view_player/current_player for visibility checks")

    def _is_enemy_visible_for_autoface(self, unit, enemy, game_state, origin: Tuple[int, int]) -> bool:
        """Check visibility for auto-face, including projected visibility from a target position."""
        if not hasattr(game_state, 'fog_of_war'):
            return True

        viewer_player = self._get_viewer_player_id(game_state)
        visibility = game_state.fog_of_war.get_visibility_state(viewer_player, enemy.x, enemy.y)

        vis_value = visibility.value if hasattr(visibility, 'value') else visibility
        if vis_value >= VisibilityState.PARTIAL.value:
            return True

        projected = game_state.fog_of_war.get_visibility_from_position(
            game_state,
            unit,
            origin,
            (enemy.x, enemy.y)
        )
        projected_value = projected.value if hasattr(projected, 'value') else projected
        return projected_value >= VisibilityState.PARTIAL.value

    def _get_auto_face_candidates(self, unit, game_state, x: int, y: int):
        """Collect adjacent auto-face candidates that are visible to the unit."""
        hex_grid = HexGrid()
        unit_hex = hex_grid.offset_to_axial(x, y)

        candidates = []
        for enemy in game_state.knights:
            if enemy.player_id != unit.player_id:
                enemy_hex = hex_grid.offset_to_axial(enemy.x, enemy.y)
                distance = unit_hex.distance_to(enemy_hex)
                if distance <= 1 and self._is_enemy_visible_for_autoface(unit, enemy, game_state, (x, y)):
                    candidates.append((enemy, distance))

        return candidates
        
    def _auto_face_nearest_enemy(self, x: int, y: int, unit, game_state):
        """Automatically face the nearest enemy"""
        if not hasattr(unit, 'facing'):
            return

        target = self.get_auto_face_target(unit, game_state, x, y)
        if target:
            target_x, target_y = target
            unit.x = x
            unit.y = y
            unit.facing.face_towards(target_x, target_y, unit.x, unit.y)
            
    def _is_valid_rotation(self, current_facing: int, target_facing: int) -> bool:
        """Check if rotation is within 60 degrees (one hex face)"""
        # Calculate the difference in facing
        diff = abs(target_facing - current_facing)
        # Handle wrap-around (0 and 5 are adjacent)
        if diff > 3:
            diff = 6 - diff
        # Only allow rotation by 1 face (60 degrees)
        return diff <= 1
