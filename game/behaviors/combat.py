"""Combat behaviors for units"""
from typing import Dict, Any, Optional, Tuple
from game.components.base import Behavior
from game.entities.knight import KnightClass
from game.combat_config import CombatConfig
from game.visibility import VisibilityState

class AttackBehavior(Behavior):
    """Basic attack behavior"""
    
    def __init__(self, attack_range: int = 1):
        super().__init__("attack")
        self.attack_range = attack_range
        
    def can_execute(self, unit, game_state) -> bool:
        """Check if unit can attack"""
        return unit.action_points >= self.get_ap_cost(unit) and not unit.has_acted
        
    def get_ap_cost(self, unit=None, target=None) -> int:
        """Calculate AP cost for attack based on unit type and distance"""
        base_cost = 3  # Base melee attack cost
        
        if unit and hasattr(unit, 'unit_class'):
            from game.entities.knight import KnightClass
            
            # Different costs by unit type
            if unit.unit_class == KnightClass.WARRIOR:
                base_cost = 4  # Warriors are methodical
            elif unit.unit_class == KnightClass.CAVALRY:
                base_cost = 3  # Cavalry are quick
            elif unit.unit_class == KnightClass.MAGE:
                base_cost = 2  # Magic is efficient
                
        return base_cost
        
    def execute(self, unit, game_state, target) -> Dict[str, Any]:
        """Execute attack against target"""
        if not self.can_execute(unit, game_state):
            return {'success': False, 'reason': 'Cannot attack'}
            
        # Check range (Chebyshev distance for grid movement)
        dx = abs(unit.x - target.x)
        dy = abs(unit.y - target.y)
        distance = max(dx, dy)  # Chebyshev distance allows diagonals
        
        if distance > self.attack_range:
            return {'success': False, 'reason': 'Target out of range'}
            
        # Check target is enemy
        if target.player_id == unit.player_id:
            return {'success': False, 'reason': 'Cannot attack friendly units'}
            
        # Get terrain modifiers
        attacker_terrain = game_state.terrain_map.get_terrain(unit.x, unit.y)
        target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
        
        # Calculate damage
        damage = self.calculate_damage(unit, target, attacker_terrain, target_terrain)
        
        # Calculate counter damage for melee
        counter_damage = 0
        if distance == 1:  # Melee range (adjacent including diagonals)
            counter_damage = self.calculate_counter_damage(target, unit, target_terrain, attacker_terrain)
            
        # Consume AP
        ap_cost = self.get_ap_cost(unit, target)
        unit.action_points -= ap_cost
        unit.has_acted = True
        
        # Mark units as engaged in combat
        unit.is_engaged_in_combat = True
        unit.engaged_with = target
        target.is_engaged_in_combat = True
        target.engaged_with = unit
        
        # Check attack angle for additional effects
        attack_angle = None
        extra_morale_penalty = 0
        should_check_routing = False
        
        if hasattr(target, 'facing'):
            attack_angle = target.facing.get_attack_angle(unit.x, unit.y, target.x, target.y)
            extra_morale_penalty = target.facing.get_morale_penalty(attack_angle)
            
            # Check for routing on rear/flank attacks
            if attack_angle.is_rear or attack_angle.is_flank:
                should_check_routing = True
        
        return {
            'success': True,
            'damage': damage,
            'counter_damage': counter_damage,
            'animation': 'attack',
            'target': target,
            'attack_angle': attack_angle,
            'extra_morale_penalty': extra_morale_penalty,
            'should_check_routing': should_check_routing
        }
        
    def calculate_damage(self, attacker, target, attacker_terrain=None, target_terrain=None) -> int:
        """Calculate damage to target"""
        # Get effective soldiers
        attacking_soldiers = attacker.stats.get_effective_soldiers(attacker_terrain)
        base_damage = attacking_soldiers * attacker.stats.stats.attack_per_soldier
        
        # Apply terrain combat modifier (but separate from height advantage)
        terrain_modifier = 1.0
        if attacker_terrain:
            terrain_modifier = attacker_terrain.get_combat_modifier_for_unit(attacker.unit_class)
            base_damage *= terrain_modifier
            
        # Apply morale modifier
        base_damage *= (attacker.morale / 100)  # Use property that includes general bonuses
        
        # Apply disrupted penalty
        if hasattr(attacker, 'is_disrupted') and attacker.is_disrupted:
            base_damage *= 0.5  # 50% damage penalty when disrupted
        
        # Apply general damage bonuses
        if hasattr(attacker, 'get_damage_modifier'):
            base_damage *= attacker.get_damage_modifier()
            
        # Apply facing modifier
        if hasattr(target, 'facing'):
            attack_angle = target.facing.get_attack_angle(attacker.x, attacker.y, target.x, target.y)
            facing_modifier = target.facing.get_damage_modifier(attack_angle)
            base_damage *= facing_modifier
            
        # Apply height advantage/disadvantage for ranged attacks
        if self.attack_range > 1 and attacker_terrain and target_terrain:
            # Check if attacker is shooting from lower ground to higher ground
            attacker_on_hills = attacker_terrain.type.value.lower() == 'hills'
            target_on_hills = target_terrain.type.value.lower() == 'hills'
            
            if not attacker_on_hills and target_on_hills:
                # Shooting uphill - 50% damage penalty
                base_damage = int(base_damage * 0.5)
            elif attacker_on_hills and not target_on_hills:
                # Shooting downhill - 50% damage bonus
                base_damage = int(base_damage * 1.5)
            
        # Calculate defense with general bonuses
        target_defense = target.stats.stats.base_defense
        if hasattr(target, 'generals'):
            defense_bonuses = target.generals.get_all_passive_bonuses(target)
            target_defense *= (1 + defense_bonuses.get('defense_bonus', 0))
            
        if target_terrain:
            target_defense += target_terrain.defense_bonus
            
        # Apply disrupted penalty to defense
        if hasattr(target, 'is_disrupted') and target.is_disrupted:
            target_defense *= 0.5  # 50% defense penalty when disrupted
            
        # Special case: garrisoned units
        if hasattr(target, 'is_garrisoned') and target.is_garrisoned:
            target_defense += 20
            
        # Calculate casualties
        damage_ratio = base_damage / (base_damage + target_defense)
        base_casualties = int(damage_ratio * attacking_soldiers * 0.25)
        
        # Unit matchup bonuses
        if attacker.unit_class == KnightClass.CAVALRY and target.unit_class == KnightClass.ARCHER:
            base_casualties = int(base_casualties * 1.5)
        elif attacker.unit_class == KnightClass.ARCHER and target.unit_class == KnightClass.WARRIOR:
            base_casualties = int(base_casualties * 0.8)
            
        return min(base_casualties, target.stats.stats.current_soldiers)
        
    def calculate_counter_damage(self, defender, attacker, defender_terrain=None, attacker_terrain=None) -> int:
        """Calculate counter damage in melee"""
        # Archers don't counter in melee
        if defender.unit_class == KnightClass.ARCHER:
            return 0
            
        # Counter damage calculations
        defending_soldiers = defender.stats.get_effective_soldiers(defender_terrain)
        base_damage = defender.stats.stats.attack_per_soldier * defending_soldiers
        
        if defender_terrain:
            base_damage *= defender_terrain.get_combat_modifier_for_unit(defender.unit_class)
            
        # Reduced morale effect for counter-attacks
        base_damage *= (defender.stats.stats.morale / 200)
        
        # Calculate attacker's defense
        attacker_defense = attacker.stats.stats.base_defense
        if attacker_terrain:
            attacker_defense += attacker_terrain.defense_bonus
            
        # Calculate casualties - counter attacks deal less
        damage_ratio = base_damage / (base_damage + attacker_defense)
        base_casualties = int(damage_ratio * defending_soldiers * 0.15)
        
        # Bonus if defender is warrior against cavalry
        if defender.unit_class == KnightClass.WARRIOR and attacker.unit_class == KnightClass.CAVALRY:
            base_casualties = int(base_casualties * 1.2)
            
        return min(base_casualties, attacker.stats.stats.current_soldiers)
        
    def get_valid_targets(self, unit, game_state) -> list:
        """Get list of valid attack targets"""
        if not self.can_execute(unit, game_state):
            return []
            
        targets = []
        for other in game_state.knights:
            if other.player_id != unit.player_id:
                # Check fog of war visibility
                if hasattr(game_state, 'fog_of_war') and game_state.current_player is not None:
                    visibility = game_state.fog_of_war.get_visibility_state(
                        game_state.current_player, other.x, other.y
                    )
                    # Only target units we can see
                    if visibility != VisibilityState.VISIBLE:
                        continue
                
                # Use Chebyshev distance to include diagonals
                dx = abs(unit.x - other.x)
                dy = abs(unit.y - other.y)
                distance = max(dx, dy)
                if distance <= self.attack_range:
                    targets.append(other)
                    
        return targets

class ArcherAttackBehavior(AttackBehavior):
    """Ranged attack behavior for archers"""
    
    def __init__(self):
        super().__init__(attack_range=3)
        # Keep name as "attack" so can_attack() works correctly
        self.name = "attack"
        
    def get_ap_cost(self, unit=None, target=None) -> int:
        """Ranged attacks cost less AP than melee"""
        return 2  # Ranged attacks are quicker to execute