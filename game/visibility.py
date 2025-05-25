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


class VisibilityState(Enum):
    """States for hex visibility."""
    HIDDEN = 0      # Never seen, no terrain info
    EXPLORED = 1    # Previously seen, terrain visible but grayed out
    PARTIAL = 2     # Can see terrain and that a unit exists, but not details
    VISIBLE = 3     # Full visibility of terrain and unit details


@dataclass
class VisionRange:
    """Vision range configuration for units."""
    base_range: int = 3  # Base vision range in hexes
    cavalry_range: int = 4  # Cavalry has better vision
    archer_range: int = 4   # Archers have good vision
    mage_range: int = 3     # Mages have normal vision
    warrior_range: int = 3  # Warriors have normal vision
    general_bonus: int = 1  # Additional range with skilled general
    
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
        for player_id in range(num_players):
            self.visibility_maps[player_id] = {}
            for x in range(board_width):
                for y in range(board_height):
                    self.visibility_maps[player_id][(x, y)] = VisibilityState.HIDDEN
                    
        self.vision_config = VisionRange()
        
    def update_player_visibility(self, game_state, player_id: int):
        """Update visibility map for a specific player based on their units."""
        from game.entities.unit import Unit
        from game.entities.castle import Castle
        
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
            visible_hexes = self._calculate_los_from_position(
                game_state, 
                (unit.x, unit.y), 
                vision_range,
                str(unit.unit_class).split('.')[-1].lower() == 'cavalry'  # Cavalry is taller
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
        """Get vision range for a unit including general bonuses."""
        # Map unit class to string for lookup
        unit_type = str(unit.unit_class).split('.')[-1].lower() if hasattr(unit, 'unit_class') else 'warrior'
        
        base_range = {
            'warrior': self.vision_config.warrior_range,
            'archer': self.vision_config.archer_range,
            'cavalry': self.vision_config.cavalry_range,
            'mage': self.vision_config.mage_range
        }.get(unit_type, self.vision_config.base_range)
        
        # Check for general with keen sight ability
        if hasattr(unit, 'generals') and unit.generals:
            bonuses = unit.generals.get_all_passive_bonuses(unit)
            vision_bonus = bonuses.get('vision_bonus', 0)
            base_range += vision_bonus
                
        return base_range
        
    def _calculate_los_from_position(self, game_state, origin: Tuple[int, int], 
                                   max_range: int, is_elevated: bool = False) -> Dict[Tuple[int, int], int]:
        """
        Calculate line of sight from a position.
        Returns dict of visible hex coordinates -> distance.
        """
        visible_hexes = {}
        hex_grid = HexGrid()
        origin_hex = hex_grid.offset_to_axial(origin[0], origin[1])
        
        # Always see your own position
        visible_hexes[origin] = 0
        
        # Check all hexes within range using a simple approach
        for y in range(max(0, origin[1] - max_range), min(game_state.board_height, origin[1] + max_range + 1)):
            for x in range(max(0, origin[0] - max_range), min(game_state.board_width, origin[0] + max_range + 1)):
                if (x, y) == origin:
                    continue
                    
                # Calculate hex distance
                target_hex = hex_grid.offset_to_axial(x, y)
                distance = origin_hex.distance_to(target_hex)
                
                if distance > 0 and distance <= max_range:
                    # Check if we have line of sight to this hex
                    if self._has_line_of_sight(game_state, origin, (x, y), is_elevated):
                        visible_hexes[(x, y)] = distance
                        
        return visible_hexes
        
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
            
            # Hills block unless viewer is elevated or on a hill
            if terrain and terrain.type.value.lower() == 'hills':
                origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
                if not is_elevated and (not origin_terrain or origin_terrain.type.value.lower() != 'hills'):
                    return False
                    
            # Check unit blocking (cavalry blocks view behind it)
            blocking_unit = game_state.get_unit_at(hex_x, hex_y)
            if blocking_unit and str(blocking_unit.unit_class).split('.')[-1].lower() == 'cavalry':
                # Cavalry blocks view unless viewer is elevated
                if not is_elevated:
                    # Check if target is directly behind the cavalry
                    if self._is_behind_blocker(origin, (hex_x, hex_y), target):
                        return False
                        
        return True
        
    def _is_behind_blocker(self, viewer: Tuple[int, int], blocker: Tuple[int, int], 
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
        
    def _is_valid_hex(self, game_state, x: int, y: int) -> bool:
        """Check if hex coordinates are valid on the board."""
        return 0 <= x < self.width and 0 <= y < self.height
        
    def _get_line(self, start: HexCoord, end: HexCoord) -> List[HexCoord]:
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
        
        for unit in game_state.units:
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
        
        for unit in game_state.units:
            visibility = self.get_visibility_state(player_id, unit.x, unit.y)
            
            if visibility == VisibilityState.VISIBLE:
                # Full identification - convert unit class to string
                unit_type = str(unit.unit_class).split('.')[-1].lower()
                known_units[(unit.x, unit.y)] = unit_type
            elif visibility == VisibilityState.PARTIAL:
                # Can see unit but not identify
                known_units[(unit.x, unit.y)] = None
                
        return known_units