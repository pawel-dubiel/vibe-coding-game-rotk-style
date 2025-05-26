"""Vision behavior for units - handles sight range and visibility mechanics"""
from typing import Optional, Dict, Any
from game.components.base import Behavior


class VisionBehavior(Behavior):
    """Behavior for unit vision capabilities"""
    
    def __init__(self, base_range: int = 3, elevated_bonus: int = 1):
        """
        Initialize vision behavior.
        
        Args:
            base_range: Base vision range in hexes
            elevated_bonus: Additional range when on elevated terrain
        """
        super().__init__("vision")
        self.base_range = base_range
        self.elevated_bonus = elevated_bonus
        self.vision_modifiers: Dict[str, int] = {}
        
    def update(self, dt: float):
        """Update vision (if needed for dynamic changes)"""
        pass
        
    def can_execute(self, unit, game_state) -> bool:
        """Vision is always active - this is a passive behavior"""
        return False  # Not an executable action
        
    def execute(self, unit, game_state, **kwargs) -> Dict[str, Any]:
        """Vision is passive - cannot be executed"""
        return {'success': False, 'reason': 'Vision is a passive ability'}
        
    def get_ap_cost(self) -> int:
        """Vision costs no AP - it's passive"""
        return 0
        
    def get_vision_range(self, terrain=None) -> int:
        """
        Get effective vision range considering all modifiers.
        
        Args:
            terrain: Current terrain the unit is on
            
        Returns:
            Effective vision range in hexes
        """
        total_range = self.base_range
        
        # Apply terrain bonuses
        if terrain and terrain.type.value.lower() == 'hills':
            total_range += self.elevated_bonus
            
        # Apply general bonuses if unit has generals
        if hasattr(self.parent, 'generals') and self.parent.generals:
            bonuses = self.parent.generals.get_all_passive_bonuses(self.parent)
            vision_bonus = bonuses.get('vision_bonus', 0)
            total_range += vision_bonus
            
        # Apply any temporary modifiers
        for modifier in self.vision_modifiers.values():
            total_range += modifier
            
        return max(1, total_range)  # Minimum vision of 1
        
    def add_vision_modifier(self, key: str, modifier: int):
        """Add a temporary vision modifier"""
        self.vision_modifiers[key] = modifier
        
    def remove_vision_modifier(self, key: str):
        """Remove a temporary vision modifier"""
        self.vision_modifiers.pop(key, None)
        
    def is_elevated(self) -> bool:
        """Check if unit has elevated vision (cavalry, on hills, etc)"""
        if not self.parent:
            return False
            
        # Check if on hills
        if hasattr(self.parent, 'get_terrain'):
            terrain = self.parent.get_terrain()
            if terrain and terrain.type.value.lower() == 'hills':
                return True
                
        # Cavalry units are naturally elevated
        if hasattr(self.parent, 'unit_class'):
            from game.entities.knight import KnightClass
            if self.parent.unit_class == KnightClass.CAVALRY:
                return True
                
        return False
        
    def blocks_vision(self) -> bool:
        """Check if this unit blocks vision behind it"""
        if not self.parent:
            return False
            
        # Cavalry blocks vision
        if hasattr(self.parent, 'unit_class'):
            from game.entities.knight import KnightClass
            return self.parent.unit_class == KnightClass.CAVALRY
            
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize vision behavior"""
        return {
            'base_range': self.base_range,
            'elevated_bonus': self.elevated_bonus,
            'modifiers': self.vision_modifiers.copy()
        }


class ScoutVisionBehavior(VisionBehavior):
    """Enhanced vision for scout-type units"""
    
    def __init__(self):
        super().__init__(base_range=4, elevated_bonus=2)
        

class ArcherVisionBehavior(VisionBehavior):
    """Archer vision with good range"""
    
    def __init__(self):
        super().__init__(base_range=4, elevated_bonus=1)
        

class StandardVisionBehavior(VisionBehavior):
    """Standard vision for most units"""
    
    def __init__(self):
        super().__init__(base_range=3, elevated_bonus=1)