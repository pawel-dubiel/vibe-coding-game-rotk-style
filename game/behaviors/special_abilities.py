"""Special ability behaviors"""
from typing import Dict, Any
from game.components.base import Behavior
from game.entities.knight import KnightClass

class CavalryChargeBehavior(Behavior):
    """Cavalry charge special ability"""
    
    def __init__(self):
        super().__init__("cavalry_charge")
        self.will_cost = 40
        
    def can_execute(self, unit, game_state) -> bool:
        """Check if unit can charge"""
        if unit.unit_class != KnightClass.CAVALRY:
            return False
            
        if unit.has_used_special or unit.stats.stats.will < self.will_cost:
            return False
            
        # Need action points for charge
        if unit.action_points < self.get_ap_cost():
            return False
            
        return True
        
    def get_ap_cost(self) -> int:
        return 5  # Charges are expensive actions
        
    def execute(self, unit, game_state, target) -> Dict[str, Any]:
        """Execute cavalry charge"""
        if not self.can_execute(unit, game_state):
            return {'success': False, 'reason': 'Cannot charge'}
            
        # Check if target is adjacent (including diagonals)
        dx = abs(unit.x - target.x)
        dy = abs(unit.y - target.y)
        if not (dx <= 1 and dy <= 1 and (dx + dy > 0)):  # Adjacent including diagonals
            return {'success': False, 'reason': 'Target must be adjacent'}
            
        # Check if target is enemy
        if target.player_id == unit.player_id:
            return {'success': False, 'reason': 'Cannot charge friendly units'}
            
        # Check terrain restrictions for cavalry charges
        if game_state.terrain_map:
            # Cavalry cannot charge when on hills
            cavalry_terrain = game_state.terrain_map.get_terrain(unit.x, unit.y)
            if cavalry_terrain and cavalry_terrain.type.value.lower() == 'hills':
                return {'success': False, 'reason': 'Cannot charge from hills'}
            
            # Cavalry cannot charge enemies on hills
            target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
            if target_terrain and target_terrain.type.value.lower() == 'hills':
                return {'success': False, 'reason': 'Cannot charge enemies on hills'}
            
        # Calculate push direction
        push_dir_x = target.x - unit.x
        push_dir_y = target.y - unit.y
        push_x = target.x + push_dir_x
        push_y = target.y + push_dir_y
        
        # Check what's behind the target
        push_result = self._check_push_destination(push_x, push_y, target, unit, game_state)
        can_push = push_result['can_push']
        obstacle_type = push_result['obstacle_type']
        obstacle_unit = push_result['obstacle_unit']
        
        # Calculate base damage using frontage
        terrain = game_state.terrain_map.get_terrain(unit.x, unit.y) if game_state.terrain_map else None
        effective_soldiers = unit.stats.get_effective_soldiers(terrain)
        base_charge_damage = int(effective_soldiers * 0.8)
        
        # Check attack angle for devastating rear charges
        rear_charge_multiplier = 1.0
        extra_morale_damage = 0
        
        if hasattr(target, 'facing'):
            attack_angle = target.facing.get_attack_angle(unit.x, unit.y, target.x, target.y)
            if attack_angle.is_rear:
                rear_charge_multiplier = 2.0  # Double damage from rear
                extra_morale_damage = 30  # Devastating morale impact
            elif attack_angle.is_flank:
                rear_charge_multiplier = 1.5  # 50% more damage from flank
                extra_morale_damage = 15
                
        base_charge_damage = int(base_charge_damage * rear_charge_multiplier)
        
        # Calculate damage based on what's behind
        if not can_push:
            if obstacle_type == 'wall':  # Map edge or castle
                # Crushing charge - nowhere to escape
                charge_damage = int(base_charge_damage * 1.5)
                self_damage = int(unit.stats.stats.current_soldiers * 0.1)
                morale_damage = 30
                message = f"Devastating charge! {target.name} crushed against the wall!"
            elif obstacle_type == 'terrain':  # Impassable terrain
                charge_damage = int(base_charge_damage * 1.3)
                self_damage = int(unit.stats.stats.current_soldiers * 0.08)
                morale_damage = 25
                message = f"Crushing charge! {target.name} trapped by terrain!"
            elif obstacle_type == 'unit':  # Another unit behind
                charge_damage = int(base_charge_damage * 1.2)
                self_damage = int(unit.stats.stats.current_soldiers * 0.07)
                morale_damage = 20
                
                # Collateral damage to unit behind
                collateral_damage = int(base_charge_damage * 0.3)
                obstacle_unit_damage = collateral_damage if obstacle_unit else 0
                
                if obstacle_unit:
                    message = f"Charge! {target.name} slammed into {obstacle_unit.name}!"
                else:
                    message = f"Charge! {target.name} crushed in the chaos!"
            else:
                # Should not happen, but handle gracefully
                charge_damage = base_charge_damage
                self_damage = int(unit.stats.stats.current_soldiers * 0.05)
                morale_damage = 20
                message = f"Charge! {target.name} has nowhere to retreat!"
        else:
            # Normal charge with push
            charge_damage = base_charge_damage
            self_damage = int(unit.stats.stats.current_soldiers * 0.05)
            morale_damage = 20
            message = f"Charge! Pushed {target.name} back!"
            
        # Consume resources
        unit.stats.consume_will(self.will_cost)
        unit.action_points -= self.get_ap_cost()
        unit.has_used_special = True
        
        # Add extra morale damage from angle
        total_morale_damage = morale_damage + extra_morale_damage
        
        # Update message for rear charges
        if hasattr(target, 'facing') and extra_morale_damage > 0:
            if attack_angle.is_rear:
                message = f"DEVASTATING REAR CHARGE! {message}"
            elif attack_angle.is_flank:
                message = f"FLANK CHARGE! {message}"
        
        result = {
            'success': True,
            'damage': charge_damage,
            'self_damage': self_damage,
            'push': can_push,
            'push_to': (push_x, push_y) if can_push else None,
            'morale_damage': total_morale_damage,
            'message': message,
            'animation': 'charge',
            'target': target,
            'is_rear_charge': extra_morale_damage > 20  # Flag for special effects
        }
        
        # Add collateral damage info if applicable
        if obstacle_type == 'unit' and obstacle_unit:
            result['collateral_unit'] = obstacle_unit
            result['collateral_damage'] = collateral_damage
            
        return result
        
    def _check_push_destination(self, x: int, y: int, target, charger, game_state) -> Dict[str, Any]:
        """Check what's at the push destination"""
        result = {
            'can_push': True,
            'obstacle_type': None,
            'obstacle_unit': None
        }
        
        # Check map bounds
        if not (0 <= x < game_state.board_width and 0 <= y < game_state.board_height):
            result['can_push'] = False
            result['obstacle_type'] = 'wall'
            return result
            
        # Check for castles
        for castle in game_state.castles:
            if castle.contains_position(x, y):
                result['can_push'] = False
                result['obstacle_type'] = 'wall'
                return result
            
        # Check terrain
        if game_state.terrain_map and not game_state.terrain_map.is_passable(x, y, target.unit_class):
            result['can_push'] = False
            result['obstacle_type'] = 'terrain'
            return result
            
        # Check for units
        for knight in game_state.knights:
            if knight.x == x and knight.y == y and not knight.is_garrisoned:
                result['can_push'] = False
                result['obstacle_type'] = 'unit'
                result['obstacle_unit'] = knight
                return result
                
        # Nothing blocking - can push
        return result
        
    def get_valid_targets(self, unit, game_state) -> list:
        """Get valid charge targets"""
        if not self.can_execute(unit, game_state):
            return []
            
        targets = []
        # Check all 8 adjacent positions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            check_x = unit.x + dx
            check_y = unit.y + dy
            
            for knight in game_state.knights:
                if (knight.player_id != unit.player_id and
                    knight.x == check_x and 
                    knight.y == check_y and
                    not knight.is_garrisoned):
                    targets.append(knight)
                    
        return targets