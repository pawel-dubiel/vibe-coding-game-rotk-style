"""
Fog of War and Line of Sight system for the strategy game.

This module handles:
- Line of sight calculations
- Visibility states (visible, partial, hidden)
- Terrain and unit blocking
- Player-specific visibility maps
"""

from enum import Enum
from typing import Dict, List, Tuple, Set, Optional
import math
from dataclasses import dataclass

from game.hex_utils import HexCoord, HexGrid
from game.shadowcasting import SimpleShadowcaster


class VisibilityState(Enum):
    """States for hex visibility."""
    HIDDEN = 0      # Never seen, no terrain info
    EXPLORED = 1    # Previously seen, terrain visible but grayed out
    PARTIAL = 2     # Can see terrain and that a unit exists, but not details
    VISIBLE = 3     # Full visibility of terrain and unit details


@dataclass
class VisionRange:
    """Vision range configuration for fog of war."""
    # Default/fallback vision range for units without vision behavior
    default_range: int = 3
    
    # Distance thresholds for unit identification
    full_id_range: int = 2      # Can identify unit type within this range
    partial_id_range: int = 3    # Can see unit exists but not type
    

class FogOfWar:
    """Manages fog of war for all players."""
    
    def __init__(self, board_width: int, board_height: int, num_players: int):
        self.width = board_width
        self.height = board_height
        self.num_players = num_players
        
        # Visibility map for each player
        # Key: player_id, Value: Dict[hex_coords, VisibilityState]
        self.visibility_maps: Dict[int, Dict[Tuple[int, int], VisibilityState]] = {}
        
        # Initialize all hexes as hidden for each player
        # Player IDs are 1-based (1, 2, etc.)
        for player_id in range(1, num_players + 1):
            self.visibility_maps[player_id] = {}
            for x in range(board_width):
                for y in range(board_height):
                    self.visibility_maps[player_id][(x, y)] = VisibilityState.HIDDEN
                    
        self.vision_config = VisionRange()
        self._cached_game_state = None  # Initialize in __init__
        
        # Initialize shadow caster for efficient LOS calculations
        self.shadowcaster = SimpleShadowcaster()
        
    def update_player_visibility(self, game_state, player_id: int):
        """Update visibility map for a specific player based on their units."""
        from game.entities.unit import Unit
        from game.entities.castle import Castle
        
        # Cache game_state for use in helper methods
        self._cached_game_state = game_state
        
        # First, downgrade all visible hexes to explored
        for coords in self.visibility_maps[player_id]:
            if self.visibility_maps[player_id][coords] == VisibilityState.VISIBLE:
                self.visibility_maps[player_id][coords] = VisibilityState.EXPLORED
            elif self.visibility_maps[player_id][coords] == VisibilityState.PARTIAL:
                self.visibility_maps[player_id][coords] = VisibilityState.EXPLORED
                
        # Get all units belonging to this player
        player_units = []
        for unit in game_state.units:
            if unit.player_id == player_id:
                player_units.append(unit)
                
        # Add castle vision if player has a castle
        castle_positions = []
        for castle in game_state.castles:
            if castle.player_id == player_id:
                # Castle has multiple hex footprint, use occupied tiles
                castle_positions.extend(castle.occupied_tiles)
                        
        # Calculate visibility from each unit
        for unit in player_units:
            vision_range = self._get_unit_vision_range(unit)
            # Check if unit has elevated vision
            vision_behavior = unit.get_behavior('VisionBehavior') if hasattr(unit, 'get_behavior') else None
            is_elevated = vision_behavior.is_elevated() if vision_behavior else False
            
            visible_hexes = self._calculate_los_from_position(
                game_state, 
                (unit.x, unit.y), 
                vision_range,
                is_elevated
            )
            
            # Update visibility states
            for hex_coords, distance in visible_hexes.items():
                current_state = self.visibility_maps[player_id][hex_coords]
                
                # Determine new visibility state based on distance
                if distance <= self.vision_config.full_id_range:
                    new_state = VisibilityState.VISIBLE
                elif distance <= self.vision_config.partial_id_range:
                    new_state = VisibilityState.PARTIAL
                else:
                    new_state = VisibilityState.EXPLORED
                    
                # Only upgrade visibility, never downgrade
                if new_state.value > current_state.value:
                    self.visibility_maps[player_id][hex_coords] = new_state
                    
        # Add castle vision (castles have fixed vision range)
        for pos in castle_positions:
            visible_hexes = self._calculate_los_from_position(
                game_state,
                pos,
                4,  # Castles have good vision
                True  # Castles are tall structures
            )
            
            for hex_coords, distance in visible_hexes.items():
                current_state = self.visibility_maps[player_id].get(hex_coords, VisibilityState.HIDDEN)
                if distance <= 2:
                    new_state = VisibilityState.VISIBLE
                else:
                    new_state = VisibilityState.PARTIAL
                    
                if new_state.value > current_state.value:
                    self.visibility_maps[player_id][hex_coords] = new_state
                    
    def _get_unit_vision_range(self, unit) -> int:
        """Get vision range for a unit using its vision behavior."""
        # Get vision behavior if it exists
        vision_behavior = unit.get_behavior('VisionBehavior') if hasattr(unit, 'get_behavior') else None
        
        if vision_behavior:
            # Use the behavior to get vision range
            terrain = None
            if hasattr(unit, 'get_terrain'):
                # Pass game_state to get_terrain if available
                terrain = unit.get_terrain(self._cached_game_state if hasattr(self, '_cached_game_state') else None)
            return vision_behavior.get_vision_range(terrain)
        
        # Fallback for units without vision behavior
        return self.vision_config.default_range
        
    def _calculate_los_from_position(self, game_state, origin: Tuple[int, int], 
                                   max_range: int, is_elevated: bool = False) -> Dict[Tuple[int, int], int]:
        """
        Calculate line of sight from a position using shadow casting.
        Returns dict of visible hex coordinates -> distance.
        """
        # Use the shadow caster for efficient visibility calculation
        visible_hexes = self.shadowcaster.calculate_visible_hexes(
            game_state, origin, max_range, is_elevated
        )
        
        # Additional filtering: verify line of sight for edge cases
        # The shadow caster gives us a good approximation, but we might want
        # to double-check certain hexes, especially those partially in shadow
        verified_hexes = {}
        for hex_pos, distance in visible_hexes.items():
            # For now, trust the shadow caster completely
            # In a more complex implementation, we might verify edge cases
            verified_hexes[hex_pos] = distance
            
        return verified_hexes
        
    def _has_line_of_sight(self, game_state, origin: Tuple[int, int], 
                          target: Tuple[int, int], is_elevated: bool) -> bool:
        """Check if there's line of sight between two hexes."""
        # Simple line of sight - check each hex along the path
        hex_grid = HexGrid()
        origin_hex = hex_grid.offset_to_axial(origin[0], origin[1])
        target_hex = hex_grid.offset_to_axial(target[0], target[1])
        
        # Get line between hexes
        line_hexes = self._get_line(origin_hex, target_hex)
        
        # Check each hex along the line for blocking
        for i, hex_coord in enumerate(line_hexes[1:-1], 1):  # Skip origin and target
            # Convert back to offset coordinates
            hex_x, hex_y = hex_grid.axial_to_offset(hex_coord)
            
            # Check terrain blocking
            terrain = game_state.terrain_map.get_terrain(hex_x, hex_y)
            
            if terrain:
                terrain_type = terrain.type.value.lower()
                
                # Mountains always block line of sight (impassable high terrain)
                if terrain_type == 'mountains':
                    return False
                
                # High hills block unless viewer is elevated or on high ground
                if terrain_type == 'high hills':
                    origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
                    viewer_on_high_ground = origin_terrain and origin_terrain.type.value.lower() in ['hills', 'high hills', 'mountains']
                    if not is_elevated and not viewer_on_high_ground:
                        return False
                
                # Hills block unless viewer is elevated or on a hill
                if terrain_type == 'hills':
                    origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
                    # If viewer is on hills or is elevated (cavalry), they can see over hills
                    viewer_on_hills = origin_terrain and origin_terrain.type.value.lower() in ['hills', 'high hills', 'mountains']
                    if not is_elevated and not viewer_on_hills:
                        return False
                    
            # Check unit blocking
            blocking_unit = game_state.get_unit_at(hex_x, hex_y)
            if blocking_unit:
                # Check if unit blocks vision using its behavior
                vision_behavior = blocking_unit.get_behavior('VisionBehavior') if hasattr(blocking_unit, 'get_behavior') else None
                if vision_behavior and vision_behavior.blocks_vision():
                    # Check if blocker is also elevated
                    blocker_elevated = vision_behavior.is_elevated() if hasattr(vision_behavior, 'is_elevated') else False
                    
                    # Elevated viewers can see over non-elevated blockers
                    if is_elevated and not blocker_elevated:
                        continue
                        
                    # If both are elevated (e.g., cavalry viewing past cavalry), no blocking
                    if is_elevated and blocker_elevated:
                        continue
                        
                    # Otherwise check if target is behind the blocker
                    if self._is_behind_blocker(origin, (hex_x, hex_y), target):
                        return False
                        
        return True
        
    @staticmethod
    def _is_behind_blocker(viewer: Tuple[int, int], blocker: Tuple[int, int], 
                          target: Tuple[int, int]) -> bool:
        """Check if target is behind blocker from viewer's perspective."""
        # Simple check: if blocker is between viewer and target on the line
        hex_grid = HexGrid()
        viewer_hex = hex_grid.offset_to_axial(viewer[0], viewer[1])
        blocker_hex = hex_grid.offset_to_axial(blocker[0], blocker[1])
        target_hex = hex_grid.offset_to_axial(target[0], target[1])
        
        # Calculate distances
        viewer_to_blocker = viewer_hex.distance_to(blocker_hex)
        viewer_to_target = viewer_hex.distance_to(target_hex)
        
        # Target is behind if it's further than blocker
        return viewer_to_target > viewer_to_blocker
        
    def _is_valid_hex(self, x: int, y: int) -> bool:
        """Check if hex coordinates are valid on the board."""
        return 0 <= x < self.width and 0 <= y < self.height
        
    @staticmethod
    def _get_line(start: HexCoord, end: HexCoord) -> List[HexCoord]:
        """Get a line of hexes between two points"""
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
        
    def get_visibility_state(self, player_id: int, x: int, y: int) -> VisibilityState:
        """Get visibility state of a hex for a player."""
        if player_id not in self.visibility_maps:
            return VisibilityState.HIDDEN
        return self.visibility_maps[player_id].get((x, y), VisibilityState.HIDDEN)
        
    def is_hex_visible(self, player_id: int, x: int, y: int) -> bool:
        """Check if a hex is at least partially visible to a player."""
        state = self.get_visibility_state(player_id, x, y)
        return state in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]
        
    def can_identify_unit(self, player_id: int, x: int, y: int) -> bool:
        """Check if a player can identify unit type at position."""
        state = self.get_visibility_state(player_id, x, y)
        return state == VisibilityState.VISIBLE
        
    def get_visible_units(self, game_state, player_id: int) -> List:
        """Get list of units visible to a player."""
        visible_units = []
        
        # Use knights instead of units
        for unit in game_state.knights:
            visibility = self.get_visibility_state(player_id, unit.x, unit.y)
            if visibility in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                visible_units.append(unit)
                
        return visible_units
        
    def get_known_units(self, game_state, player_id: int) -> Dict[Tuple[int, int], Optional[str]]:
        """
        Get units known to player with their identification status.
        Returns dict: position -> unit_type (or None if unidentified)
        """
        known_units = {}
        
        # Use knights instead of units
        for unit in game_state.knights:
            visibility = self.get_visibility_state(player_id, unit.x, unit.y)
            
            if visibility == VisibilityState.VISIBLE:
                # Full identification - get unit type
                if hasattr(unit, 'unit_class'):
                    unit_type = str(unit.unit_class).split('.')[-1].lower()
                else:
                    unit_type = 'unknown'
                known_units[(unit.x, unit.y)] = unit_type
            elif visibility == VisibilityState.PARTIAL:
                # Can see unit but not identify
                known_units[(unit.x, unit.y)] = None
                
        return known_units
        
    def update_player_visibility_incremental(self, game_state, player_id: int, 
                                           changed_positions: Optional[List[Tuple[int, int]]] = None):
        """
        Incrementally update visibility for positions that might have changed.
        More efficient than full recalculation.
        
        Args:
            game_state: Current game state
            player_id: Player to update visibility for
            changed_positions: List of positions where units moved to/from
        """
        if changed_positions is None:
            # Fall back to full update
            self.update_player_visibility(game_state, player_id)
            return
            
        # Cache game_state
        self._cached_game_state = game_state
        
        # For each changed position, update visibility in that area
        updated_hexes = set()
        max_vision_range = 5  # Maximum possible vision range
        
        for pos in changed_positions:
            # Get hexes that might be affected by change at this position
            hex_grid = HexGrid()
            center_hex = hex_grid.offset_to_axial(pos[0], pos[1])
            
            # Check all hexes within max vision range
            for y in range(max(0, pos[1] - max_vision_range), 
                          min(self.height, pos[1] + max_vision_range + 1)):
                for x in range(max(0, pos[0] - max_vision_range), 
                              min(self.width, pos[0] + max_vision_range + 1)):
                    target_hex = hex_grid.offset_to_axial(x, y)
                    if center_hex.distance_to(target_hex) <= max_vision_range:
                        updated_hexes.add((x, y))
                        
        # Now recalculate visibility only for affected hexes
        # First downgrade existing visibility in affected areas
        for hex_pos in updated_hexes:
            if hex_pos in self.visibility_maps[player_id]:
                current = self.visibility_maps[player_id][hex_pos]
                if current in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                    self.visibility_maps[player_id][hex_pos] = VisibilityState.EXPLORED
                    
        # Then calculate new visibility from player's units
        for unit in game_state.units:
            if unit.player_id == player_id:
                vision_range = self._get_unit_vision_range(unit)
                vision_behavior = unit.get_behavior('VisionBehavior') if hasattr(unit, 'get_behavior') else None
                is_elevated = vision_behavior.is_elevated() if vision_behavior else False
                
                # Only check visibility for affected hexes within this unit's range
                for hex_pos in updated_hexes:
                    hex_grid = HexGrid()
                    unit_hex = hex_grid.offset_to_axial(unit.x, unit.y)
                    target_hex = hex_grid.offset_to_axial(hex_pos[0], hex_pos[1])
                    distance = unit_hex.distance_to(target_hex)
                    
                    if distance <= vision_range:
                        if self._has_line_of_sight(game_state, (unit.x, unit.y), hex_pos, is_elevated):
                            # Update visibility state based on distance
                            if distance <= self.vision_config.full_id_range:
                                new_state = VisibilityState.VISIBLE
                            elif distance <= self.vision_config.partial_id_range:
                                new_state = VisibilityState.PARTIAL
                            else:
                                new_state = VisibilityState.EXPLORED
                                
                            current_state = self.visibility_maps[player_id].get(hex_pos, VisibilityState.HIDDEN)
                            if new_state.value > current_state.value:
                                self.visibility_maps[player_id][hex_pos] = new_state