"""Refactored unit class using components and behaviors"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from game.components.stats import StatsComponent, UnitStats
from game.components.base import Behavior
from game.components.generals import GeneralRoster
from game.entities.knight import KnightClass

@dataclass
class UnitPosition:
    x: int
    y: int

class Unit:
    """Base unit class using component architecture"""
    
    def __init__(self, name: str, unit_class: KnightClass, x: int, y: int):
        self.name = name
        self.unit_class = unit_class
        self.position = UnitPosition(x, y)
        
        # Core properties
        self.player_id: Optional[int] = None
        self.selected = False
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False
        
        # Action points
        self.max_action_points = self._get_max_ap()
        self.action_points = self.max_action_points
        
        # Components
        self.stats = StatsComponent(self._create_unit_stats())
        self.stats.attach(self)
        
        # General roster
        self.generals = GeneralRoster(max_generals=3)
        
        # Behaviors
        self.behaviors: Dict[str, Behavior] = {}
        
        # State flags
        self.is_garrisoned = False
        self.garrison_location = None
        self.in_enemy_zoc = False
        self.is_routing = False
        self.engaged_with = None
        
        # Combat modifiers from abilities
        self.temp_damage_multiplier = 1.0
        self.temp_vulnerability = 1.0
        
    @property
    def x(self) -> int:
        return self.position.x
        
    @x.setter
    def x(self, value: int):
        self.position.x = value
        
    @property
    def y(self) -> int:
        return self.position.y
        
    @y.setter  
    def y(self, value: int):
        self.position.y = value
        
    @property
    def soldiers(self) -> int:
        """Compatibility property"""
        return self.stats.stats.current_soldiers
        
    @property
    def max_soldiers(self) -> int:
        """Compatibility property"""
        return self.stats.stats.max_soldiers
        
    @property
    def morale(self) -> float:
        """Compatibility property with general bonuses"""
        base_morale = self.stats.stats.morale
        bonuses = self.generals.get_all_passive_bonuses(self)
        return min(100, base_morale + bonuses.get('morale_bonus', 0))
        
    @morale.setter
    def morale(self, value: float):
        """Compatibility property"""
        self.stats.stats.morale = value
        
    @property
    def will(self) -> float:
        """Compatibility property"""
        return self.stats.stats.will
        
    @will.setter
    def will(self, value: float):
        """Compatibility property"""
        self.stats.stats.will = value
        
    @property
    def max_will(self) -> float:
        """Compatibility property"""
        return self.stats.stats.max_will
        
    def add_behavior(self, behavior: Behavior):
        """Add a behavior to this unit"""
        self.behaviors[behavior.name] = behavior
        
    def remove_behavior(self, behavior_name: str):
        """Remove a behavior from this unit"""
        if behavior_name in self.behaviors:
            del self.behaviors[behavior_name]
            
    def can_execute_behavior(self, behavior_name: str, game_state) -> bool:
        """Check if a behavior can be executed"""
        if behavior_name not in self.behaviors:
            return False
        return self.behaviors[behavior_name].can_execute(self, game_state)
        
    def execute_behavior(self, behavior_name: str, game_state, **kwargs) -> Dict[str, Any]:
        """Execute a behavior"""
        if behavior_name not in self.behaviors:
            return {'success': False, 'reason': 'Behavior not found'}
            
        behavior = self.behaviors[behavior_name]
        return behavior.execute(self, game_state, **kwargs)
        
    def get_available_behaviors(self, game_state) -> List[str]:
        """Get list of currently executable behaviors"""
        available = []
        for name, behavior in self.behaviors.items():
            if behavior.can_execute(self, game_state):
                available.append(name)
        return available
        
    def take_casualties(self, amount: int) -> bool:
        """Apply casualties to unit"""
        return self.stats.take_casualties(amount)
        
    def end_turn(self):
        """Reset for new turn"""
        self.action_points = self.max_action_points
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False
        
        # Regenerate will
        self.stats.regenerate_will(20)
        
        # Apply general morale regeneration
        bonuses = self.generals.get_all_passive_bonuses(self)
        morale_regen = bonuses.get('morale_regen', 0)
        if morale_regen > 0:
            self.stats.stats.morale = min(100, self.stats.stats.morale + morale_regen)
            
        # Reset temporary combat modifiers
        self.temp_damage_multiplier = 1.0
        self.temp_vulnerability = 1.0
        
        # Update generals
        self.generals.on_turn_end()
        
    def has_zone_of_control(self) -> bool:
        """Check if unit exerts Zone of Control"""
        # Only non-routing units with good morale have ZOC
        return not self.is_routing and self.morale >= 25 and self.soldiers > 0
        
    def is_in_enemy_zoc(self, game_state) -> Tuple[bool, Optional['Unit']]:
        """Check if unit is in enemy Zone of Control"""
        for enemy in game_state.knights:
            if (enemy.player_id != self.player_id and 
                enemy.has_zone_of_control()):
                # Check if adjacent (including diagonals)
                dx = abs(self.x - enemy.x)
                dy = abs(self.y - enemy.y)
                if dx <= 1 and dy <= 1 and (dx + dy > 0):  # Adjacent including diagonals
                    return True, enemy
        return False, None
        
    def _get_max_ap(self) -> int:
        """Get max action points for unit class"""
        ap_by_class = {
            KnightClass.WARRIOR: 8,   # High AP for heavy infantry
            KnightClass.ARCHER: 7,    # Good AP for ranged units
            KnightClass.CAVALRY: 10,  # Highest AP for mobile units
            KnightClass.MAGE: 6       # Moderate AP for spellcasters
        }
        return ap_by_class.get(self.unit_class, 7)
        
    def _create_unit_stats(self) -> UnitStats:
        """Create stats based on unit class"""
        stats_by_class = {
            KnightClass.WARRIOR: UnitStats(
                max_soldiers=100,
                current_soldiers=100,
                attack_per_soldier=1.0,
                base_defense=30,
                formation_width=40
            ),
            KnightClass.ARCHER: UnitStats(
                max_soldiers=80,
                current_soldiers=80,
                attack_per_soldier=1.5,
                base_defense=20,
                formation_width=40
            ),
            KnightClass.CAVALRY: UnitStats(
                max_soldiers=50,
                current_soldiers=50,
                attack_per_soldier=2.0,
                base_defense=25,
                formation_width=25
            ),
            KnightClass.MAGE: UnitStats(
                max_soldiers=30,
                current_soldiers=30,
                attack_per_soldier=3.0,
                base_defense=15,
                formation_width=15
            )
        }
        return stats_by_class.get(self.unit_class, UnitStats(100, 100, 1.0, 25, 30))
        
    # Compatibility methods for existing code
    @property
    def knight_class(self) -> KnightClass:
        """Compatibility property"""
        return self.unit_class
        
    @property
    def health(self) -> float:
        """Compatibility - map health to soldier percentage"""
        return (self.soldiers / self.max_soldiers) * 100
        
    @property
    def max_health(self) -> float:
        """Compatibility property"""
        return 100.0
        
    def can_move(self) -> bool:
        """Check if unit can move - for compatibility"""
        return 'move' in self.behaviors and self.behaviors['move'].can_execute(self, None)
        
    def can_attack(self) -> bool:
        """Check if unit can attack - for compatibility"""
        return 'attack' in self.behaviors and self.behaviors['attack'].can_execute(self, None)
        
    def get_movement_range(self) -> int:
        """Get movement range including general bonuses"""
        base_range = 3  # Default
        if 'move' in self.behaviors:
            base_range = self.behaviors['move'].movement_range
            
        bonuses = self.generals.get_all_passive_bonuses(self)
        return base_range + bonuses.get('movement_bonus', 0)
        
    def get_damage_modifier(self) -> float:
        """Get total damage modifier from generals and temporary effects"""
        bonuses = self.generals.get_all_passive_bonuses(self)
        base_modifier = 1.0 + bonuses.get('damage_bonus', 0) + bonuses.get('attack_bonus', 0)
        return base_modifier * self.temp_damage_multiplier
        
    def get_damage_reduction(self) -> float:
        """Get total damage reduction from generals"""
        bonuses = self.generals.get_all_passive_bonuses(self)
        base_reduction = bonuses.get('damage_reduction', 0)
        
        # Check triggered abilities (like Last Stand)
        triggered = self.generals.check_all_triggered_abilities(self, {})
        for ability_result in triggered:
            result = ability_result['result']
            base_reduction += result.get('damage_reduction', 0)
            
        return min(0.5, base_reduction)  # Cap at 50% reduction
        
    def take_casualties_with_generals(self, amount: int, context: Dict[str, Any] = None) -> bool:
        """Take casualties with general damage reduction"""
        if context is None:
            context = {}
            
        # Apply damage reduction
        reduction = self.get_damage_reduction()
        reduced_amount = int(amount * (1 - reduction))
        
        # Apply vulnerability if any
        if self.temp_vulnerability > 1.0:
            reduced_amount = int(reduced_amount * self.temp_vulnerability)
            
        return self.stats.take_casualties(reduced_amount)
        
    def execute_general_ability(self, general, ability, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an active general ability"""
        if context is None:
            context = {}
            
        if not ability.can_use(self):
            return {'success': False, 'reason': 'Cannot use ability'}
            
        return ability.apply(self, context)