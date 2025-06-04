"""Terrain movement behavior for units - handles terrain-specific movement costs"""
from typing import Dict, Optional
from game.components.base import Behavior
try:
    from game.terrain_v2 import TerrainType
except ImportError:
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
            TerrainType.PLAINS: 0.9,          # 10% bonus on plains
            TerrainType.ROAD: 0.7,            # 30% bonus on roads
            TerrainType.BRIDGE: 1.0,          # Normal on bridges
            TerrainType.HILLS: 1.5,           # 50% penalty on hills
            TerrainType.FOREST: 2.0,          # Double penalty in forest
            TerrainType.SWAMP: 2.5,           # Major penalty in swamp
        }
        
        # Add new terrain types if available
        try:
            modifiers.update({
                TerrainType.LIGHT_FOREST: 1.5,     # Moderate penalty
                TerrainType.DENSE_FOREST: 3.0,     # Cannot effectively move
                TerrainType.HIGH_HILLS: 2.0,       # Major penalty
                TerrainType.MARSH: 2.0,            # Major penalty
                TerrainType.DESERT: 1.2,           # Some penalty
                TerrainType.SNOW: 1.5,             # Moderate penalty
            })
        except AttributeError:
            pass  # Using old terrain system
            
        super().__init__(modifiers)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """Cavalry combat effectiveness varies by terrain"""
        combat_mods = {
            TerrainType.PLAINS: 1.2,      # 20% bonus
            TerrainType.ROAD: 1.1,        # 10% bonus
            TerrainType.HILLS: 0.85,      # 15% penalty
            TerrainType.FOREST: 0.7,      # 30% penalty
            TerrainType.SWAMP: 0.6,       # 40% penalty
        }
        
        # Add new terrain types if available
        try:
            combat_mods.update({
                TerrainType.LIGHT_FOREST: 0.85,    # 15% penalty
                TerrainType.DENSE_FOREST: 0.5,     # 50% penalty - very bad
                TerrainType.HIGH_HILLS: 0.7,       # 30% penalty
                TerrainType.MARSH: 0.7,            # 30% penalty
                TerrainType.DESERT: 0.95,          # 5% penalty
                TerrainType.SNOW: 0.85,            # 15% penalty
            })
        except AttributeError:
            pass
            
        return combat_mods.get(terrain_type, 1.0)


class ArcherTerrainBehavior(TerrainMovementBehavior):
    """Archers are adept at forest movement and combat"""
    
    def __init__(self):
        modifiers = {
            TerrainType.FOREST: 0.75,     # 25% bonus in forest
            TerrainType.HILLS: 0.9,       # 10% bonus on hills
            TerrainType.SWAMP: 1.2,       # 20% penalty in swamp
            TerrainType.ROAD: 0.5,        # Standard road bonus
        }
        
        # Add new terrain types if available
        try:
            modifiers.update({
                TerrainType.LIGHT_FOREST: 0.8,     # 20% bonus
                TerrainType.DENSE_FOREST: 0.9,     # 10% bonus - still good
                TerrainType.HIGH_HILLS: 0.95,      # 5% bonus
                TerrainType.MARSH: 1.1,            # 10% penalty
                TerrainType.DESERT: 1.0,           # Normal
                TerrainType.SNOW: 1.1,             # 10% penalty
            })
        except AttributeError:
            pass
            
        super().__init__(modifiers)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """Archers excel in defensive terrain"""
        combat_mods = {
            TerrainType.FOREST: 1.2,      # 20% bonus
            TerrainType.HILLS: 1.25,      # 25% bonus
        }
        
        # Add new terrain types if available
        try:
            combat_mods.update({
                TerrainType.LIGHT_FOREST: 1.15,    # 15% bonus
                TerrainType.DENSE_FOREST: 1.25,    # 25% bonus - excellent cover
                TerrainType.HIGH_HILLS: 1.3,       # 30% bonus - height advantage
                TerrainType.MARSH: 0.9,            # 10% penalty
                TerrainType.DESERT: 0.95,          # 5% penalty
                TerrainType.SNOW: 1.0,             # Normal
            })
        except AttributeError:
            pass
            
        return combat_mods.get(terrain_type, 1.0)


class WarriorTerrainBehavior(TerrainMovementBehavior):
    """Warriors are less affected by difficult terrain"""
    
    def __init__(self):
        modifiers = {
            TerrainType.HILLS: 0.8,       # Only 20% penalty (vs 100% base)
            TerrainType.SWAMP: 0.85,      # Reduced penalty in swamp
            TerrainType.FOREST: 0.9,      # 10% bonus in forest
            TerrainType.ROAD: 0.5,        # Standard road bonus
        }
        
        # Add new terrain types if available
        try:
            modifiers.update({
                TerrainType.LIGHT_FOREST: 0.85,    # 15% bonus
                TerrainType.DENSE_FOREST: 1.0,     # Normal - trained for this
                TerrainType.HIGH_HILLS: 0.9,       # Only 10% penalty
                TerrainType.MARSH: 0.9,            # 10% penalty
                TerrainType.DESERT: 0.95,          # 5% penalty
                TerrainType.SNOW: 0.9,             # 10% penalty
            })
        except AttributeError:
            pass
            
        super().__init__(modifiers)


class MageTerrainBehavior(TerrainMovementBehavior):
    """Mages struggle in swamps but otherwise have standard movement"""
    
    def __init__(self):
        modifiers = {
            TerrainType.SWAMP: 1.5,       # Major penalty in swamps
            TerrainType.ROAD: 0.5,        # Standard road bonus
            TerrainType.HILLS: 1.1,       # Slight penalty
        }
        
        # Add new terrain types if available
        try:
            modifiers.update({
                TerrainType.LIGHT_FOREST: 1.0,     # Normal
                TerrainType.DENSE_FOREST: 1.2,     # 20% penalty
                TerrainType.HIGH_HILLS: 1.3,       # 30% penalty - hard climb
                TerrainType.MARSH: 1.3,            # 30% penalty
                TerrainType.DESERT: 1.1,           # 10% penalty
                TerrainType.SNOW: 1.2,             # 20% penalty
            })
        except AttributeError:
            pass
            
        super().__init__(modifiers)
        
    def get_combat_modifier(self, terrain_type: TerrainType) -> float:
        """Mages are particularly affected by certain terrains"""
        combat_mods = {
            TerrainType.SWAMP: 0.6,       # 40% penalty
        }
        
        # Add new terrain types if available
        try:
            combat_mods.update({
                TerrainType.MARSH: 0.7,            # 30% penalty
                TerrainType.DENSE_FOREST: 0.85,    # 15% penalty - hard to cast
                TerrainType.HIGH_HILLS: 1.1,       # 10% bonus - good vantage
                TerrainType.SNOW: 0.9,             # 10% penalty
            })
        except AttributeError:
            pass
            
        return combat_mods.get(terrain_type, 1.0)


class StandardTerrainBehavior(TerrainMovementBehavior):
    """Default terrain behavior with no special modifiers"""
    
    def __init__(self):
        # Only apply standard road bonus
        modifiers = {
            TerrainType.ROAD: 0.5,
        }
        super().__init__(modifiers)