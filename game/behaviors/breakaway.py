"""Breakaway behavior for units in combat"""
from typing import Dict, Any
from game.components.base import Behavior
from game.combat_config import CombatConfig

class BreakawayBehavior(Behavior):
    """Behavior for breaking away from combat"""
    
    def __init__(self):
        super().__init__("breakaway")
        
    def can_execute(self, unit, game_state) -> bool:
        """Check if unit can attempt to break away from combat"""
        if not unit.is_engaged_in_combat or not unit.engaged_with:
            return False
            
        if unit.action_points < CombatConfig.MIN_AP_FOR_BREAKAWAY:
            return False
            
        # Check if unit type can break away from the engaged enemy
        return unit.can_break_away_from(unit.engaged_with)
        
    def get_ap_cost(self, unit=None, target=None) -> int:
        """AP cost for breakaway attempt"""
        return CombatConfig.BREAKAWAY_AP_COST
        
    def execute(self, unit, game_state, **kwargs) -> Dict[str, Any]:
        """Execute breakaway attempt"""
        if not self.can_execute(unit, game_state):
            return {'success': False, 'reason': 'Cannot break away'}
            
        enemy_unit = unit.engaged_with
        if not enemy_unit:
            return {'success': False, 'reason': 'Not engaged with any enemy'}
            
        # Attempt breakaway using unit's method
        result = unit.attempt_breakaway(enemy_unit, game_state)
        
        # If successful and enemy gets opportunity attack
        if result.get('success') and result.get('opportunity_attack'):
            # Calculate opportunity attack damage
            from game.behaviors.combat import AttackBehavior
            attack_behavior = AttackBehavior()
            
            # Opportunity attack deals reduced damage
            damage = attack_behavior.calculate_damage(enemy_unit, unit)
            opportunity_damage = int(damage * CombatConfig.OPPORTUNITY_ATTACK_MULTIPLIER)
            
            # Apply damage with breakaway reduction
            final_damage = int(opportunity_damage * CombatConfig.BREAKAWAY_DAMAGE_REDUCTION)
            
            if final_damage > 0:
                unit.take_casualties(final_damage)
                result['opportunity_damage'] = final_damage
                result['message'] += f' Took {final_damage} casualties from opportunity attack.'
                
        return result
        
    def get_valid_targets(self, unit, game_state) -> list:
        """No targets needed for breakaway - it's a self-targeted action"""
        return []