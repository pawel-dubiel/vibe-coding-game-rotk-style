"""Stats component for units"""
from dataclasses import dataclass
from typing import Dict, Any
from game.components.base import Component

@dataclass
class UnitStats:
    """Data class for unit statistics"""
    max_soldiers: int
    current_soldiers: int
    attack_per_soldier: float
    base_defense: float
    formation_width: int
    morale: float = 100.0
    max_morale: float = 100.0
    will: float = 100.0
    max_will: float = 100.0

class StatsComponent(Component):
    """Component for managing unit statistics"""
    
    def __init__(self, stats: UnitStats):
        super().__init__()
        self.stats = stats
        
    def update(self, dt: float):
        """Update stats over time (e.g., morale recovery)"""
        pass
        
    def take_casualties(self, amount: int) -> bool:
        """Apply casualties to the unit. Returns True if unit is destroyed."""
        self.stats.current_soldiers = max(0, self.stats.current_soldiers - amount)
        
        # Morale loss based on casualties
        casualty_percent = amount / self.stats.max_soldiers
        self.stats.morale = max(0, self.stats.morale - casualty_percent * 20)
        
        return self.stats.current_soldiers <= 0
        
    def consume_will(self, amount: float) -> bool:
        """Consume will points. Returns True if successful."""
        if self.stats.will >= amount:
            self.stats.will -= amount
            return True
        return False
        
    def regenerate_will(self, amount: float):
        """Regenerate will points"""
        self.stats.will = min(self.stats.max_will, self.stats.will + amount)
        
    def get_effective_soldiers(self, terrain=None) -> int:
        """Get number of soldiers that can actually fight"""
        effective_width = self.stats.formation_width
        
        # Terrain affects frontage
        if terrain:
            terrain_name = terrain.type.value
            if terrain_name in ["Forest", "Hills"]:
                effective_width *= 0.7
            elif terrain_name == "Bridge":
                effective_width *= 0.5
            elif terrain_name in ["Plains", "Road"]:
                # Some units might get bonuses on open terrain
                pass
                
        return min(int(effective_width), self.stats.current_soldiers)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for serialization"""
        return {
            'soldiers': self.stats.current_soldiers,
            'max_soldiers': self.stats.max_soldiers,
            'morale': self.stats.morale,
            'will': self.stats.will
        }