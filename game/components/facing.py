"""Unit facing component for directional combat mechanics"""
from enum import Enum
from typing import Tuple, Optional
import math
from dataclasses import dataclass

class FacingDirection(Enum):
    """Six possible facing directions in a hex grid"""
    NORTH_EAST = 0      # Top-right
    EAST = 1            # Right
    SOUTH_EAST = 2      # Bottom-right
    SOUTH_WEST = 3      # Bottom-left
    WEST = 4            # Left
    NORTH_WEST = 5      # Top-left
    
    def get_opposite(self) -> 'FacingDirection':
        """Get the opposite facing direction"""
        return FacingDirection((self.value + 3) % 6)
    
    def get_adjacent_directions(self) -> Tuple['FacingDirection', 'FacingDirection']:
        """Get the two adjacent directions (for determining flanks)"""
        left = FacingDirection((self.value - 1) % 6)
        right = FacingDirection((self.value + 1) % 6)
        return left, right

@dataclass
class AttackAngle:
    """Result of calculating attack angle"""
    is_frontal: bool
    is_rear: bool
    is_flank: bool
    angle_degrees: float
    description: str

class FacingComponent:
    """Component that handles unit facing and directional combat"""
    
    def __init__(self, initial_facing: FacingDirection = FacingDirection.NORTH_EAST):
        self.facing = initial_facing
        self._last_move_direction = None
        
    def update_facing_from_movement(self, from_x: int, from_y: int, to_x: int, to_y: int):
        """Update facing based on movement direction (Odd-R Flat-Top Layout)"""
        dx = to_x - from_x
        dy = to_y - from_y
        
        if dx == 0 and dy == 0:
            return  # No movement
            
        if dy == 0:
            # Pure horizontal movement
            if dx > 0:
                self.facing = FacingDirection.EAST
            else:
                self.facing = FacingDirection.WEST
        elif dy > 0:
            # Moving South
            if dx > 0:
                self.facing = FacingDirection.SOUTH_EAST
            elif dx < 0:
                self.facing = FacingDirection.SOUTH_WEST
            else:
                # dx == 0, depends on row parity
                if from_y % 2 == 0: # Even row, pushed left, so dx=0 is Right/East-ish
                    self.facing = FacingDirection.SOUTH_EAST
                else: # Odd row, pushed right, so dx=0 is Left/West-ish
                    self.facing = FacingDirection.SOUTH_WEST
        else:
            # Moving North
            if dx > 0:
                self.facing = FacingDirection.NORTH_EAST
            elif dx < 0:
                self.facing = FacingDirection.NORTH_WEST
            else:
                # dx == 0
                if from_y % 2 == 0: # Even row
                    self.facing = FacingDirection.NORTH_EAST
                else: # Odd row
                    self.facing = FacingDirection.NORTH_WEST
                
        self._last_move_direction = (dx, dy)
    
    def get_attack_angle(self, attacker_x: int, attacker_y: int, 
                        defender_x: int, defender_y: int) -> AttackAngle:
        """Determine if an attack is frontal, rear, or flank"""
        # Calculate relative position of attacker from defender's perspective
        dx = attacker_x - defender_x
        dy = attacker_y - defender_y
        
        # Convert to angle (0-360 degrees)
        angle_rad = math.atan2(dy, dx)
        angle_deg = (math.degrees(angle_rad) + 360) % 360
        
        # Get facing angle
        facing_angles = {
            FacingDirection.EAST: 0,
            FacingDirection.SOUTH_EAST: 60,
            FacingDirection.SOUTH_WEST: 120,
            FacingDirection.WEST: 180,
            FacingDirection.NORTH_WEST: 240,
            FacingDirection.NORTH_EAST: 300
        }
        
        facing_angle = facing_angles[self.facing]
        
        # Calculate relative angle
        relative_angle = (angle_deg - facing_angle + 360) % 360
        
        # Determine attack type based on relative angle
        # Front arc: 300-360 and 0-60 degrees (120 degree arc)
        # Rear arc: 120-240 degrees (120 degree arc)
        # Flank arcs: 60-120 and 240-300 degrees (60 degrees each)
        
        if relative_angle <= 60 or relative_angle >= 300:
            return AttackAngle(
                is_frontal=True, 
                is_rear=False, 
                is_flank=False,
                angle_degrees=relative_angle,
                description="Frontal attack"
            )
        elif 120 <= relative_angle <= 240:
            return AttackAngle(
                is_frontal=False, 
                is_rear=True, 
                is_flank=False,
                angle_degrees=relative_angle,
                description="Rear attack"
            )
        else:
            return AttackAngle(
                is_frontal=False, 
                is_rear=False, 
                is_flank=True,
                angle_degrees=relative_angle,
                description="Flank attack"
            )
    
    def get_damage_modifier(self, attack_angle: AttackAngle) -> float:
        """Get damage modifier based on attack angle"""
        if attack_angle.is_rear:
            return 1.5  # 50% more damage from rear
        elif attack_angle.is_flank:
            return 1.25  # 25% more damage from flank
        else:
            return 1.0  # Normal damage from front
    
    def get_morale_penalty(self, attack_angle: AttackAngle) -> int:
        """Get additional morale penalty for being attacked from bad angle"""
        if attack_angle.is_rear:
            return 15  # Extra morale loss from rear attacks
        elif attack_angle.is_flank:
            return 10  # Extra morale loss from flank attacks
        else:
            return 0
    
    def check_routing_chance(self, attack_angle: AttackAngle, 
                           current_morale: float, casualties_percent: float) -> bool:
        """Check if unit should route based on attack angle and casualties"""
        import random
        
        # Base routing chance
        base_chance = 0
        
        # Rear attacks have high routing chance
        if attack_angle.is_rear:
            if casualties_percent > 0.3:  # Lost 30% in one attack
                base_chance = 60
            elif casualties_percent > 0.2:  # Lost 20% in one attack
                base_chance = 40
            elif casualties_percent > 0.1:  # Lost 10% in one attack
                base_chance = 20
                
            # Low morale increases chance
            if current_morale < 40:
                base_chance += 20
            elif current_morale < 60:
                base_chance += 10
                
        # Flank attacks have moderate routing chance
        elif attack_angle.is_flank:
            if casualties_percent > 0.4:  # Lost 40% in one attack
                base_chance = 30
            elif casualties_percent > 0.25:  # Lost 25% in one attack
                base_chance = 15
                
            # Low morale increases chance
            if current_morale < 30:
                base_chance += 15
                
        # Even frontal attacks can cause routing with heavy casualties
        else:
            if casualties_percent > 0.5 and current_morale < 40:
                base_chance = 20
                
        return random.randint(1, 100) <= base_chance
    
    def get_facing_arrow_coords(self, center_x: float, center_y: float, 
                               length: float = 20) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get coordinates for drawing facing arrow"""
        # Calculate arrow endpoint based on facing
        facing_angles = {
            FacingDirection.EAST: 0,
            FacingDirection.SOUTH_EAST: 60,
            FacingDirection.SOUTH_WEST: 120,
            FacingDirection.WEST: 180,
            FacingDirection.NORTH_WEST: 240,
            FacingDirection.NORTH_EAST: 300
        }
        
        angle_deg = facing_angles[self.facing]
        angle_rad = math.radians(angle_deg)
        
        # Calculate arrow endpoint
        end_x = center_x + length * math.cos(angle_rad)
        end_y = center_y + length * math.sin(angle_rad)
        
        return (center_x, center_y), (end_x, end_y)
    
    def rotate_clockwise(self):
        """Rotate facing 60 degrees clockwise"""
        self.facing = FacingDirection((self.facing.value + 1) % 6)
        
    def rotate_counter_clockwise(self):
        """Rotate facing 60 degrees counter-clockwise"""
        self.facing = FacingDirection((self.facing.value - 1) % 6)
        
    def face_towards(self, target_x: int, target_y: int, unit_x: int, unit_y: int):
        """Face towards a specific hex coordinate"""
        # Use the same logic as movement
        self.update_facing_from_movement(unit_x, unit_y, target_x, target_y)