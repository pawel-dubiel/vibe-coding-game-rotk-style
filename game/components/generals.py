"""General system for units - leaders that provide bonuses and abilities"""
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from game.entities.unit import Unit

class GeneralAbilityType(Enum):
    """Types of general abilities"""
    PASSIVE = "passive"  # Always active
    ACTIVE = "active"    # Must be activated, costs will
    TRIGGERED = "triggered"  # Activates under certain conditions

class GeneralAbility(ABC):
    """Base class for general abilities"""
    
    def __init__(self, name: str, description: str, ability_type: GeneralAbilityType):
        self.name = name
        self.description = description
        self.ability_type = ability_type
        self.cooldown = 0
        self.max_cooldown = 0
        
    @abstractmethod
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the ability effect"""
        pass
        
    def can_use(self, unit: 'Unit') -> bool:
        """Check if ability can be used"""
        if self.cooldown > 0:
            return False
        if self.ability_type == GeneralAbilityType.ACTIVE:
            return unit.will >= self.get_will_cost()
        return True
        
    def get_will_cost(self) -> int:
        """Get will cost for active abilities"""
        return 0
        
    def on_turn_end(self):
        """Called at end of turn to reduce cooldown"""
        if self.cooldown > 0:
            self.cooldown -= 1

# Passive Abilities
class InspireAbility(GeneralAbility):
    """Passive: Increases unit morale and morale recovery"""
    
    def __init__(self):
        super().__init__(
            "Inspire", 
            "Unit has +10 morale and recovers 5 morale per turn",
            GeneralAbilityType.PASSIVE
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'morale_bonus': 10,
            'morale_regen': 5
        }

class TacticianAbility(GeneralAbility):
    """Passive: Increases movement range by 1"""
    
    def __init__(self):
        super().__init__(
            "Tactician",
            "Unit gains +1 movement range",
            GeneralAbilityType.PASSIVE
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'movement_bonus': 1
        }

class VeteranAbility(GeneralAbility):
    """Passive: Unit takes 10% less casualties"""
    
    def __init__(self):
        super().__init__(
            "Veteran",
            "Unit takes 10% less casualties in combat",
            GeneralAbilityType.PASSIVE
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'damage_reduction': 0.1
        }

class AggressiveAbility(GeneralAbility):
    """Passive: Unit deals 15% more damage"""
    
    def __init__(self):
        super().__init__(
            "Aggressive",
            "Unit deals 15% more damage in combat",
            GeneralAbilityType.PASSIVE
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'damage_bonus': 0.15
        }

class KeenSightAbility(GeneralAbility):
    """Passive: Unit has extended vision range"""
    
    def __init__(self):
        super().__init__(
            "Keen Sight",
            "Unit gains +1 vision range",
            GeneralAbilityType.PASSIVE
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'vision_bonus': 1
        }

# Active Abilities
class RallyAbility(GeneralAbility):
    """Active: Restore morale and remove routing"""
    
    def __init__(self):
        super().__init__(
            "Rally",
            "Restore 30 morale and stop routing (20 Will)",
            GeneralAbilityType.ACTIVE
        )
        self.max_cooldown = 3
        
    def get_will_cost(self) -> int:
        return 20
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        unit.stats.stats.morale = min(100, unit.stats.stats.morale + 30)
        unit.is_routing = False
        unit.stats.consume_will(self.get_will_cost())
        self.cooldown = self.max_cooldown
        return {
            'success': True,
            'message': f"{unit.name} rallies the troops!"
        }

class BerserkAbility(GeneralAbility):
    """Active: Double damage for one attack but take more damage"""
    
    def __init__(self):
        super().__init__(
            "Berserk",
            "Next attack deals double damage but unit takes 50% more damage (30 Will)",
            GeneralAbilityType.ACTIVE
        )
        self.max_cooldown = 2
        
    def get_will_cost(self) -> int:
        return 30
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        unit.stats.consume_will(self.get_will_cost())
        self.cooldown = self.max_cooldown
        
        # Apply the effect to the unit
        unit.temp_damage_multiplier = 2.0
        unit.temp_vulnerability = 1.5
        
        return {
            'success': True,
            'damage_multiplier': 2.0,
            'vulnerability': 1.5,
            'duration': 1,
            'message': f"{unit.name} goes berserk!"
        }

# Triggered Abilities
class LastStandAbility(GeneralAbility):
    """Triggered: When below 25% soldiers, gain damage reduction"""
    
    def __init__(self):
        super().__init__(
            "Last Stand",
            "When below 25% soldiers, take 30% less damage",
            GeneralAbilityType.TRIGGERED
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        if unit.soldiers < unit.max_soldiers * 0.25:
            return {
                'damage_reduction': 0.3,
                'triggered': True
            }
        return {'triggered': False}

class CounterchargeAbility(GeneralAbility):
    """Triggered: When charged by cavalry, deal damage back"""
    
    def __init__(self):
        super().__init__(
            "Countercharge",
            "When charged by cavalry, automatically countercharge",
            GeneralAbilityType.TRIGGERED
        )
        
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        if context.get('being_charged', False):
            return {
                'counter_damage_bonus': 0.5,
                'triggered': True,
                'message': f"{unit.name} countercharges!"
            }
        return {'triggered': False}

@dataclass
class General:
    """A general that leads troops"""
    name: str
    title: str
    abilities: List[GeneralAbility]
    level: int = 1
    experience: int = 0
    
    def get_passive_bonuses(self, unit: 'Unit') -> Dict[str, Any]:
        """Get all passive bonuses from this general"""
        bonuses = {
            'morale_bonus': 0,
            'morale_regen': 0,
            'movement_bonus': 0,
            'damage_bonus': 0,
            'damage_reduction': 0,
            'attack_bonus': 0,
            'defense_bonus': 0
        }
        
        for ability in self.abilities:
            if ability.ability_type == GeneralAbilityType.PASSIVE:
                result = ability.apply(unit, {})
                for key, value in result.items():
                    if key in bonuses:
                        bonuses[key] += value
                        
        # Level bonuses
        bonuses['morale_bonus'] += self.level * 2
        bonuses['attack_bonus'] += self.level * 0.02
        bonuses['defense_bonus'] += self.level * 0.02
        
        return bonuses
        
    def check_triggered_abilities(self, unit: 'Unit', context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check and apply triggered abilities"""
        triggered = []
        for ability in self.abilities:
            if ability.ability_type == GeneralAbilityType.TRIGGERED:
                result = ability.apply(unit, context)
                if result.get('triggered', False):
                    triggered.append({
                        'ability': ability,
                        'result': result
                    })
        return triggered
        
    def gain_experience(self, amount: int):
        """Gain experience and potentially level up"""
        self.experience += amount
        exp_for_next_level = self.level * 100
        
        if self.experience >= exp_for_next_level:
            self.level += 1
            self.experience -= exp_for_next_level
            return True  # Leveled up
        return False
        
    def on_turn_end(self):
        """Called at end of turn"""
        for ability in self.abilities:
            ability.on_turn_end()

class GeneralRoster:
    """Manages generals for a unit"""
    
    def __init__(self, max_generals: int = 3):
        self.generals: List[General] = []
        self.max_generals = max_generals
        
    def add_general(self, general: General) -> bool:
        """Add a general to the roster"""
        if len(self.generals) < self.max_generals:
            self.generals.append(general)
            return True
        return False
        
    def remove_general(self, general: General):
        """Remove a general from the roster"""
        if general in self.generals:
            self.generals.remove(general)
            
    def get_all_passive_bonuses(self, unit: 'Unit') -> Dict[str, Any]:
        """Get combined passive bonuses from all generals"""
        combined = {
            'morale_bonus': 0,
            'morale_regen': 0,
            'movement_bonus': 0,
            'damage_bonus': 0,
            'damage_reduction': 0,
            'attack_bonus': 0,
            'defense_bonus': 0
        }
        
        for general in self.generals:
            bonuses = general.get_passive_bonuses(unit)
            for key, value in bonuses.items():
                combined[key] += value
                
        return combined
        
    def check_all_triggered_abilities(self, unit: 'Unit', context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check triggered abilities from all generals"""
        all_triggered = []
        for general in self.generals:
            triggered = general.check_triggered_abilities(unit, context)
            all_triggered.extend(triggered)
        return all_triggered
        
    def get_active_abilities(self, unit: 'Unit') -> List[Tuple[General, GeneralAbility]]:
        """Get all available active abilities"""
        active = []
        for general in self.generals:
            for ability in general.abilities:
                if ability.ability_type == GeneralAbilityType.ACTIVE and ability.can_use(unit):
                    active.append((general, ability))
        return active
        
    def on_turn_end(self):
        """Called at end of turn"""
        for general in self.generals:
            general.on_turn_end()
            
    def on_battle_end(self, victory: bool, casualties: int):
        """Called after battle to award experience"""
        exp = 10 if victory else 5
        exp += casualties // 10  # Bonus for scale of battle
        
        for general in self.generals:
            if general.gain_experience(exp):
                # General leveled up!
                pass