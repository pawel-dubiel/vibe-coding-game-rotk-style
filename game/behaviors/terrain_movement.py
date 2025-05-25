"""Terrain movement behavior for units - handles terrain-specific movement costs"""
from typing import Dict, Optional
from game.components.base import Behavior
from game.terrain import TerrainType


class TerrainMovementBehavior(Behavior):
    """Base behavior for unit terrain movement capabilities"""
    
    def __init__(self, terrain_modifiers: Optional[Dict[TerrainType, float]] = None):
        """
        Initialize terrain movement behavior.
        
        Args:
            terrain_modifiers: Dict mapping terrain types to movement cost multipliers
        """
        super().__init__("terrain_movement")
        self.terrain_modifiers = terrain_modifiers or {}
        
    def can_execute(self, unit, game_state) -> bool:
        """Terrain movement is passive - not executable"""
        return False
        
    def execute(self, unit, game_state, **kwargs) -> Dict[str, any]:
        """Terrain movement is passive"""
        return {'success': False, 'reason': 'Terrain movement is a passive ability'}
        
    def get_ap_cost(self) -> int:
        """No AP cost - passive ability"""
        return 0
        
    def get_movement_cost_modifier(self, terrain_type: TerrainType) -> float:
        """
        Get movement cost modifier for specific terrain.
        
        Args:
            terrain_type: The terrain type to check
            
        Returns:
            Movement cost multiplier (1.0 = normal, >1.0 = slower, <1.0 = faster)
        """
        return self.terrain_modifiers.get(terrain_type, 1.0)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """
        Get combat effectiveness modifier for terrain.
        Override in subclasses for unit-specific combat modifiers.
        
        Args:
            terrain_type: The terrain type to check
            
        Returns:
            Combat effectiveness multiplier
        """
        return 1.0


class CavalryTerrainBehavior(TerrainMovementBehavior):
    """Cavalry struggle in difficult terrain but excel on open ground"""
    
    def __init__(self):
        modifiers = {
            TerrainType.FOREST: 2.0,      # Double penalty in forest
            TerrainType.SWAMP: 2.0,       # Double penalty in swamp
            TerrainType.HILLS: 1.5,       # 50% penalty on hills
            TerrainType.ROAD: 0.8,        # 20% bonus on roads
            TerrainType.PLAINS: 1.0,      # Normal on plains
            TerrainType.BRIDGE: 1.0,      # Normal on bridges
        }
        super().__init__(modifiers)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """Cavalry combat effectiveness varies by terrain"""
        combat_mods = {
            TerrainType.FOREST: 0.8,      # 20% penalty
            TerrainType.SWAMP: 0.8,       # 20% penalty
            TerrainType.HILLS: 0.8,       # 20% penalty
            TerrainType.PLAINS: 1.1,      # 10% bonus
            TerrainType.ROAD: 1.1,        # 10% bonus
        }
        return combat_mods.get(terrain_type, 1.0)


class ArcherTerrainBehavior(TerrainMovementBehavior):
    """Archers are adept at forest movement and combat"""
    
    def __init__(self):
        modifiers = {
            TerrainType.FOREST: 0.75,     # 25% bonus in forest
            TerrainType.HILLS: 1.0,       # Normal on hills (but combat bonus)
            TerrainType.SWAMP: 1.0,       # Normal in swamp
            TerrainType.ROAD: 0.5,        # Standard road bonus
        }
        super().__init__(modifiers)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """Archers excel in defensive terrain"""
        combat_mods = {
            TerrainType.FOREST: 1.2,      # 20% bonus
            TerrainType.HILLS: 1.2,       # 20% bonus
        }
        return combat_mods.get(terrain_type, 1.0)


class WarriorTerrainBehavior(TerrainMovementBehavior):
    """Warriors are less affected by difficult terrain"""
    
    def __init__(self):
        modifiers = {
            TerrainType.HILLS: 0.8,       # Only 20% penalty (vs 100% base)
            TerrainType.SWAMP: 0.8,       # Reduced penalty in swamp
            TerrainType.FOREST: 1.0,      # Normal in forest
            TerrainType.ROAD: 0.5,        # Standard road bonus
        }
        super().__init__(modifiers)


class MageTerrainBehavior(TerrainMovementBehavior):
    """Mages struggle in swamps but otherwise have standard movement"""
    
    def __init__(self):
        modifiers = {
            TerrainType.SWAMP: 1.2,       # Extra penalty in swamps
            TerrainType.ROAD: 0.5,        # Standard road bonus
        }
        super().__init__(modifiers)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """Mages are particularly affected by swamps"""
        if terrain_type == TerrainType.SWAMP:
            return 0.7  # 30% penalty
        return 1.0


class StandardTerrainBehavior(TerrainMovementBehavior):
    """Default terrain behavior with no special modifiers"""
    
    def __init__(self):
        # Only apply standard road bonus
        modifiers = {
            TerrainType.ROAD: 0.5,
        }
        super().__init__(modifiers)