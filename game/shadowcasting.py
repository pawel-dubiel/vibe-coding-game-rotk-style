"""
Shadow casting algorithm for efficient line-of-sight calculation in hexagonal grids.
Based on recursive shadowcasting adapted for hexagonal grids.
"""
from typing import Dict, Tuple, List
from dataclasses import dataclass
from game.hex_utils import HexCoord, HexGrid


@dataclass
class Shadow:
    """Represents a shadow/blocked area in the field of view"""
    start: float  # Start angle of shadow
    end: float    # End angle of shadow
    
    def contains(self, angle: float) -> bool:
        """Check if an angle is within this shadow"""
        return self.start <= angle <= self.end
    
    def blocks(self, start: float, end: float) -> bool:
        """Check if this shadow completely blocks an arc"""
        return self.start <= start and self.end >= end


class HexShadowcaster:
    """
    Efficient shadow casting for hexagonal grids.
    Calculates visible hexes from a point using shadow propagation.
    """
    
    def __init__(self):
        self.hex_grid = HexGrid()
        # Pre-calculate hex directions for the 6 sextants
        self._init_sextants()
        
    def _init_sextants(self):
        """Initialize the 6 sextants (60-degree wedges) for hex grids"""
        # Each sextant covers 60 degrees of the hex grid
        # We'll process each sextant separately to handle symmetry
        self.sextants = []
        
        # Define the 6 directions and their angular ranges
        # In a hex grid, we have natural 60-degree divisions
        for i in range(6):
            start_angle = i * 60.0
            end_angle = (i + 1) * 60.0
            self.sextants.append({
                'id': i,
                'start_angle': start_angle,
                'end_angle': end_angle,
                'direction': i  # Maps to hex directions
            })
    
    def calculate_visible_hexes(self, game_state, origin: Tuple[int, int], 
                               max_range: int, viewer_elevation: float = 0.0) -> Dict[Tuple[int, int], int]:
        """
        Calculate all visible hexes from origin using shadow casting.
        
        Args:
            game_state: Game state for terrain/unit queries
            origin: Starting position (x, y) in offset coordinates
            max_range: Maximum vision range
            viewer_elevation: Height of viewer (0 for ground, positive for elevated)
            
        Returns:
            Dict mapping visible positions to their distance from origin
        """
        visible_hexes = {origin: 0}  # Always see your own position
        
        # Convert origin to hex coordinates
        origin_hex = self.hex_grid.offset_to_axial(origin[0], origin[1])
        
        # Process each of the 6 sextants
        for sextant in self.sextants:
            self._cast_shadows_in_sextant(
                game_state, origin, origin_hex, max_range, 
                viewer_elevation, sextant['direction'], visible_hexes
            )
            
        return visible_hexes
    
    def _cast_shadows_in_sextant(self, game_state, origin: Tuple[int, int],
                                 origin_hex: HexCoord, max_range: int,
                                 viewer_elevation: float, direction: int,
                                 visible_hexes: Dict[Tuple[int, int], int]):
        """
        Cast shadows in one 60-degree sextant using recursive shadow casting.
        """
        # Track shadows as we go outward
        shadows: List[Shadow] = []
        
        # Process each ring of hexes outward from origin
        for distance in range(1, max_range + 1):
            # Get hexes at this distance in this sextant
            ring_hexes = self._get_ring_hexes_in_sextant(origin_hex, distance, direction)
            
            for hex_pos, angle_start, angle_end in ring_hexes:
                # Convert back to offset coordinates
                offset_x, offset_y = self.hex_grid.axial_to_offset(hex_pos)
                
                # Check if this hex is in valid bounds
                if not (0 <= offset_x < game_state.board_width and 
                       0 <= offset_y < game_state.board_height):
                    continue
                
                # Check if this hex is completely shadowed
                if self._is_shadowed(angle_start, angle_end, shadows):
                    continue
                    
                # This hex is at least partially visible
                offset_pos = (offset_x, offset_y)
                visible_hexes[offset_pos] = distance
                
                # Check if this hex blocks vision
                if self._blocks_vision(game_state, origin, offset_pos, viewer_elevation):
                    # Add shadow for this blocking hex
                    self._add_shadow(angle_start, angle_end, shadows)
    
    def _get_ring_hexes_in_sextant(self, center: HexCoord, radius: int, 
                                   direction: int) -> List[Tuple[HexCoord, float, float]]:
        """
        Get all hexes at given radius in a specific sextant (60-degree wedge).
        Returns list of (hex_coord, start_angle, end_angle) tuples.
        """
        results = []
        
        # Use hex ring algorithm but filter to sextant
        # Start from the direction and go 1/6 of the way around
        directions = [
            HexCoord(1, 0), HexCoord(1, -1), HexCoord(0, -1),
            HexCoord(-1, 0), HexCoord(-1, 1), HexCoord(0, 1)
        ]
        
        # Start position for this ring
        current = center
        for _ in range(radius):
            current = HexCoord(current.q + directions[direction].q,
                             current.r + directions[direction].r)
        
        # Walk 1/6 of the ring (for this sextant)
        steps_per_sextant = radius
        dir_index = (direction + 2) % 6  # Perpendicular direction
        
        for step in range(steps_per_sextant):
            # Calculate angular position of this hex
            angle = self._calculate_hex_angle(center, current)
            # Hex "width" in angular terms depends on distance
            angular_width = 60.0 / max(1, radius)  # Approximation
            
            results.append((
                current,
                angle - angular_width / 2,
                angle + angular_width / 2
            ))
            
            # Move to next hex in ring
            current = HexCoord(current.q + directions[dir_index].q,
                             current.r + directions[dir_index].r)
            
        return results
    
    def _calculate_hex_angle(self, origin: HexCoord, target: HexCoord) -> float:
        """Calculate angle from origin to target hex (in degrees)"""
        # Convert to cube coordinates for easier calculation
        ox, oy, oz = origin.to_cube()
        tx, ty, tz = target.to_cube()
        
        # Calculate angle using cube coordinate differences
        dx = tx - ox
        dy = ty - oy
        
        # Convert to angle (0-360 degrees)
        # This is simplified for hex grids
        if dx == 0 and dy == 0:
            return 0.0
            
        # Use the hex direction to determine angle
        # Each of the 6 directions is 60 degrees apart
        if dx > 0 and dy <= 0:
            base_angle = 0.0
        elif dx == 0 and dy < 0:
            base_angle = 60.0
        elif dx < 0 and dy < 0:
            base_angle = 120.0
        elif dx < 0 and dy >= 0:
            base_angle = 180.0
        elif dx == 0 and dy > 0:
            base_angle = 240.0
        else:  # dx > 0 and dy > 0
            base_angle = 300.0
            
        # Add fractional angle based on position within sextant
        return base_angle
    
    def _is_shadowed(self, start_angle: float, end_angle: float, 
                     shadows: List[Shadow]) -> bool:
        """Check if an angular range is completely in shadow"""
        for shadow in shadows:
            if shadow.blocks(start_angle, end_angle):
                return True
        return False
    
    def _blocks_vision(self, game_state, origin: Tuple[int, int],
                      target: Tuple[int, int], viewer_elevation: float) -> bool:
        """
        Check if a hex blocks vision based on terrain and units.
        """
        # Get terrain at target
        terrain = game_state.terrain_map.get_terrain(target[0], target[1])
        
        # Hills block unless viewer is elevated
        if terrain and terrain.type.value.lower() == 'hills':
            origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
            viewer_on_hills = origin_terrain and origin_terrain.type.value.lower() == 'hills'
            
            if viewer_elevation <= 0 and not viewer_on_hills:
                return True  # Hills block vision
                
        # Mountains always block
        if terrain and terrain.type.value.lower() == 'mountains':
            return True
            
        # Check for castle blocking
        if hasattr(game_state, 'castles'):
            for castle in game_state.castles:
                if hasattr(castle, 'contains_position') and castle.contains_position(target[0], target[1]):
                    # Castles block vision unless viewer is elevated or on a mountain
                    origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
                    viewer_on_mountain = origin_terrain and origin_terrain.type.value.lower() == 'mountains'
                    if viewer_elevation <= 0 and not viewer_on_mountain:
                        return True
            
        # Check for blocking units
        unit = game_state.get_unit_at(target[0], target[1])
        if unit and unit.player_id != game_state.current_player:
            # Enemy units can block vision
            vision_behavior = unit.get_behavior('VisionBehavior') if hasattr(unit, 'get_behavior') else None
            if vision_behavior and vision_behavior.blocks_vision():
                # Check elevation interaction
                unit_elevation = 1.0 if vision_behavior.is_elevated() else 0.0
                
                # Higher elevation can see over lower blockers
                if viewer_elevation > unit_elevation:
                    return False
                    
                return True
                
        return False
    
    def _add_shadow(self, start_angle: float, end_angle: float, 
                   shadows: List[Shadow]):
        """Add a shadow to the list, merging with existing shadows if needed"""
        new_shadow = Shadow(start_angle, end_angle)
        
        # Simple implementation: just add the shadow
        # A more sophisticated version would merge overlapping shadows
        shadows.append(new_shadow)
        
        # Sort shadows by start angle for easier processing
        shadows.sort(key=lambda s: s.start)
        
        # Merge overlapping shadows
        merged = []
        for shadow in shadows:
            if not merged:
                merged.append(shadow)
            else:
                last = merged[-1]
                if shadow.start <= last.end:
                    # Overlapping, merge them
                    last.end = max(last.end, shadow.end)
                else:
                    merged.append(shadow)
                    
        shadows[:] = merged


class SimpleShadowcaster:
    """
    Simpler shadow casting implementation that's more suitable for hex grids.
    Uses a sector-based approach rather than true shadow casting.
    """
    
    def __init__(self):
        self.hex_grid = HexGrid()
    
    def calculate_visible_hexes(self, game_state, origin: Tuple[int, int],
                               max_range: int, is_elevated: bool = False) -> Dict[Tuple[int, int], int]:
        """
        Calculate visible hexes using a simplified shadow casting approach.
        More efficient than checking line-of-sight to every hex.
        """
        visible_hexes = {origin: 0}
        origin_hex = self.hex_grid.offset_to_axial(origin[0], origin[1])
        
        # Instead of tracking blocked sectors, check line of sight for each hex
        # This is more accurate for hex grids where "sectors" don't map cleanly
        
        # Process each ring of hexes
        for distance in range(1, max_range + 1):
            # Get all hexes at this distance
            ring_hexes = SimpleShadowcaster._get_hex_ring(origin_hex, distance)
            
            for hex_coord in ring_hexes:
                # Convert to offset coordinates
                offset_x, offset_y = self.hex_grid.axial_to_offset(hex_coord)
                offset_pos = (offset_x, offset_y)
                
                # Check bounds
                if not (0 <= offset_x < game_state.board_width and 
                       0 <= offset_y < game_state.board_height):
                    continue
                
                # Check if we can see this hex using line of sight
                if SimpleShadowcaster._check_visibility_simple(game_state, origin, offset_pos, is_elevated):
                    visible_hexes[offset_pos] = distance
                        
        return visible_hexes
    
    @staticmethod
    def _get_hex_ring(center: HexCoord, radius: int) -> List[HexCoord]:
        """Get all hexes at exactly 'radius' distance from center"""
        if radius == 0:
            return [center]
            
        results = []
        directions = [
            HexCoord(1, 0), HexCoord(1, -1), HexCoord(0, -1),
            HexCoord(-1, 0), HexCoord(-1, 1), HexCoord(0, 1)
        ]
        
        # Start at a corner of the ring
        current = center
        for _ in range(radius):
            current = HexCoord(current.q + directions[4].q, current.r + directions[4].r)
            
        # Walk around the ring
        for i in range(6):
            for _ in range(radius):
                results.append(current)
                current = HexCoord(current.q + directions[i].q, current.r + directions[i].r)
                
        return results
    
    @staticmethod
    def _get_sector(origin: HexCoord, target: HexCoord) -> int:
        """
        Determine which of the 6 hex sectors the target is in relative to origin.
        Returns 0-5 for the 6 directions.
        """
        dx = target.q - origin.q
        dy = target.r - origin.r
        
        # Determine primary direction
        if dx > 0 and dy <= 0:
            return 0  # East
        elif dx == 0 and dy < 0:
            return 1  # Northeast  
        elif dx < 0 and dy < 0:
            return 2  # Northwest
        elif dx < 0 and dy >= 0:
            return 3  # West
        elif dx == 0 and dy > 0:
            return 4  # Southwest
        else:
            return 5  # Southeast
            
    @staticmethod
    def _check_visibility_simple(game_state, origin: Tuple[int, int],
                                target: Tuple[int, int], is_elevated: bool) -> bool:
        """Check visibility along the line between origin and target"""
        hex_grid = HexGrid()
        origin_hex = hex_grid.offset_to_axial(origin[0], origin[1])
        target_hex = hex_grid.offset_to_axial(target[0], target[1])
        
        # Get all hexes along the line
        line_hexes = HexGrid.get_line(origin_hex, target_hex)
        
        # Check each hex for blocking (except origin and target)
        for i, hex_coord in enumerate(line_hexes[1:-1], 1):
            offset_x, offset_y = hex_grid.axial_to_offset(hex_coord)
            
            # Check bounds
            if not (0 <= offset_x < game_state.board_width and 
                   0 <= offset_y < game_state.board_height):
                continue
                
            # Check if this hex blocks vision to the target
            # Note: we're checking if the hex at (offset_x, offset_y) blocks vision from origin
            if SimpleShadowcaster._blocks_vision_simple(game_state, origin, (offset_x, offset_y), is_elevated):
                return False
                
        return True
        
    @staticmethod
    def _blocks_vision_simple(game_state, origin: Tuple[int, int],
                             target: Tuple[int, int], is_elevated: bool) -> bool:
        """Check if this hex blocks further vision"""
        # Don't block at origin
        if target == origin:
            return False
            
        terrain = game_state.terrain_map.get_terrain(target[0], target[1])
        
        # Mountains always block
        if terrain and terrain.type.value.lower() == 'mountains':
            return True
            
        # Hills block unless viewer is elevated
        if terrain and terrain.type.value.lower() == 'hills':
            origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
            viewer_on_hills = origin_terrain and origin_terrain.type.value.lower() == 'hills'
            
            if not is_elevated and not viewer_on_hills:
                return True
        
        # Check for castle blocking
        if hasattr(game_state, 'castles'):
            for castle in game_state.castles:
                if hasattr(castle, 'contains_position') and castle.contains_position(target[0], target[1]):
                    # Castles block vision unless viewer is elevated or on a mountain
                    origin_terrain = game_state.terrain_map.get_terrain(origin[0], origin[1])
                    viewer_on_mountain = origin_terrain and origin_terrain.type.value.lower() == 'mountains'
                    if not is_elevated and not viewer_on_mountain:
                        # print(f"DEBUG: Castle at {target} blocks vision from {origin}")
                        return True
        # Check units
        unit = game_state.get_unit_at(target[0], target[1])
        if unit:
            vision_behavior = unit.get_behavior('VisionBehavior') if hasattr(unit, 'get_behavior') else None
            if vision_behavior and vision_behavior.blocks_vision():
                # Elevated viewers can see over non-elevated blockers
                if is_elevated and not vision_behavior.is_elevated():
                    return False
                return True
                
        return False
    
