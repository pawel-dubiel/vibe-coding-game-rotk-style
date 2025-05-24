"""Rotation behavior for changing unit facing"""
from typing import Dict, Any, Optional
from game.components.base import Behavior
from game.components.facing import FacingDirection
from game.terrain import TerrainType

class RotationBehavior(Behavior):
    """Behavior that allows units to rotate in place"""
    
    def __init__(self):
        super().__init__("rotate")
        self.base_ap_cost = 1  # Base cost to rotate
        
    def can_execute(self, unit, game_state) -> bool:
        """Check if unit can rotate"""
        # Need at least base AP
        if unit.action_points < self.get_ap_cost(unit, game_state):
            return False
            
        # Cannot rotate if in combat (adjacent to enemy)
        if self._is_in_combat(unit, game_state):
            return False
            
        # Cannot rotate if routing
        if unit.is_routing:
            return False
            
        return True
        
    def get_ap_cost(self, unit, game_state) -> int:
        """Calculate AP cost for rotation based on terrain"""
        base_cost = self.base_ap_cost
        
        # Check terrain
        if game_state and hasattr(game_state, 'terrain_map'):
            terrain = game_state.terrain_map.get_terrain(unit.x, unit.y)
            if terrain:
                # Different terrains affect rotation difficulty
                terrain_costs = {
                    TerrainType.PLAINS: 1,
                    TerrainType.ROAD: 1,
                    TerrainType.FOREST: 2,      # Harder to rotate in forest
                    TerrainType.HILLS: 2,        # Harder on hills
                    TerrainType.SWAMP: 3,        # Very hard in swamp
                    TerrainType.WATER: 1,        # Normal on bridges
                    TerrainType.BRIDGE: 1
                }
                base_cost = terrain_costs.get(terrain.type, 1)
        
        # Heavy units (cavalry) cost more to rotate
        if hasattr(unit, 'unit_class'):
            from game.entities.knight import KnightClass
            if unit.unit_class == KnightClass.CAVALRY:
                base_cost += 1
                
        return base_cost
        
    def execute(self, unit, game_state, direction: str = 'clockwise') -> Dict[str, Any]:
        """Execute rotation"""
        if not self.can_execute(unit, game_state):
            return {'success': False, 'reason': 'Cannot rotate'}
            
        # Calculate AP cost
        ap_cost = self.get_ap_cost(unit, game_state)
        
        # Perform rotation
        if direction == 'clockwise':
            unit.facing.rotate_clockwise()
        else:
            unit.facing.rotate_counter_clockwise()
            
        # Consume AP
        unit.action_points -= ap_cost
        
        return {
            'success': True,
            'new_facing': unit.facing.facing,
            'ap_cost': ap_cost,
            'message': f'{unit.name} rotated to face {unit.facing.facing.name.replace("_", " ").lower()}'
        }
        
    def _is_in_combat(self, unit, game_state) -> bool:
        """Check if unit is adjacent to any enemy"""
        if not game_state:
            return False
            
        for enemy in game_state.knights:
            if enemy.player_id != unit.player_id:
                # Check adjacency (including diagonals)
                dx = abs(unit.x - enemy.x)
                dy = abs(unit.y - enemy.y)
                if dx <= 1 and dy <= 1 and (dx + dy > 0):
                    return True
                    
        return False
        
    def get_rotation_options(self, unit) -> list:
        """Get available rotation options"""
        if not hasattr(unit, 'facing'):
            return []
            
        current = unit.facing.facing
        clockwise = FacingDirection((current.value + 1) % 6)
        counter_clockwise = FacingDirection((current.value - 1) % 6)
        
        return [
            ('rotate_cw', f'Rotate to {clockwise.name.replace("_", " ").title()}', 'clockwise'),
            ('rotate_ccw', f'Rotate to {counter_clockwise.name.replace("_", " ").title()}', 'counter_clockwise')
        ]