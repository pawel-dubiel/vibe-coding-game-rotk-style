"""Combat behaviors for units"""
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from game.components.base import Behavior
from game.entities.knight import KnightClass
from game.combat_config import CombatConfig
from game.visibility import VisibilityState

class CombatMode(Enum):
    """Different modes of combat engagement"""
    RANGED = "ranged"      # Attacker shoots from distance (no counter-attack)
    MELEE = "melee"        # Close combat (both sides can attack)
    SKIRMISH = "skirmish"  # Hit-and-run tactics (reduced counter-attack)
    CHARGE = "charge"      # Cavalry charge (bonus damage, but vulnerable to counter)

class AttackBehavior(Behavior):
    """Basic attack behavior"""
    
    def __init__(self, attack_range: int = 1):
        super().__init__("attack")
        self.attack_range = attack_range
        
    def can_execute(self, unit, game_state) -> bool:
        """Check if unit can attack"""
        base_cost = self.get_ap_cost(unit)  # Get base cost without terrain penalty
        
        if getattr(unit, 'is_routing', False):
            return False

        # Basic requirements - remove has_acted check to allow multiple attacks
        if unit.action_points < base_cost:
            return False
            
        # Morale requirement: Need 50%+ morale to attack (except first attack)
        if not hasattr(unit, 'attacks_this_turn'):
            unit.attacks_this_turn = 0
            
        if unit.attacks_this_turn > 0:
            from game.combat_config import CombatConfig
            if unit.morale < CombatConfig.MORALE_ATTACK_THRESHOLD:
                return False
            if hasattr(unit, 'cohesion') and unit.cohesion < CombatConfig.COHESION_ATTACK_THRESHOLD:
                return False
            
        return True
        
    def get_ap_cost(self, unit=None, target=None, game_state=None) -> int:
        """Calculate AP cost for attack based on unit type, target terrain, and distance"""
        base_cost = 3  # Default

        if unit and hasattr(unit, 'unit_class'):
            from game.combat_config import CombatConfig
            base_cost = CombatConfig.get_attack_ap_cost(unit.unit_class.value)
        
        # Add terrain-based attack cost if target and game_state are provided
        if target and game_state and hasattr(game_state, 'terrain_map') and game_state.terrain_map:
            target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
            if target_terrain:
                # Get the base terrain movement cost (without unit-specific modifiers)
                terrain_movement_cost = target_terrain.movement_cost
                
                # Apply terrain penalty: twice the additional movement cost as extra AP
                if terrain_movement_cost > 1.0:  # Only apply penalty for difficult terrain
                    terrain_penalty = int((terrain_movement_cost - 1.0) * 2)
                    base_cost += terrain_penalty
                
        return base_cost
        
    def determine_combat_mode(self, attacker, target, distance: int) -> CombatMode:
        """Determine the combat mode based on units and distance"""
        # Ranged combat when attacking from distance
        if distance > 1:
            return CombatMode.RANGED
            
        # Melee combat at close range
        if distance == 1:
            # Special case: cavalry charging (could be expanded with charge mechanic)
            if attacker.unit_class == KnightClass.CAVALRY and not hasattr(attacker, 'has_charged'):
                return CombatMode.CHARGE
                
            # Standard melee combat
            return CombatMode.MELEE
            
        # Should not reach here, but default to melee
        return CombatMode.MELEE
        
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
            
        # Determine combat mode
        combat_mode = self.determine_combat_mode(unit, target, distance)
        
        # Get terrain modifiers
        attacker_terrain = game_state.terrain_map.get_terrain(unit.x, unit.y)
        target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
        
        # Calculate damage based on combat mode
        damage = self.calculate_damage(unit, target, attacker_terrain, target_terrain, combat_mode)
        
        # Calculate counter damage based on combat mode
        counter_damage = 0
        if combat_mode == CombatMode.MELEE:
            # Full counter-attack in melee
            counter_damage = self.calculate_counter_damage(target, unit, target_terrain, attacker_terrain)
        elif combat_mode == CombatMode.SKIRMISH:
            # Reduced counter-attack for skirmish
            counter_damage = int(self.calculate_counter_damage(target, unit, target_terrain, attacker_terrain) * 0.5)
        elif combat_mode == CombatMode.CHARGE:
            # Cavalry charges can receive counter-attack but at reduced effectiveness
            counter_damage = int(self.calculate_counter_damage(target, unit, target_terrain, attacker_terrain) * 0.75)
        # RANGED mode has no counter-attack (counter_damage remains 0)
            
        # Consume AP (including terrain penalty)
        ap_cost = self.get_ap_cost(unit, target, game_state)
        if unit.action_points < ap_cost:
            return {'success': False, 'reason': 'Not enough action points'}
        unit.action_points -= ap_cost
        # Mark unit as having acted this turn
        unit.has_acted = True
        
        # Track attacks this turn and apply progressive morale loss
        if not hasattr(unit, 'attacks_this_turn'):
            unit.attacks_this_turn = 0
            
        unit.attacks_this_turn += 1
        
        # Apply fatigue for multiple attacks
        if unit.attacks_this_turn > 1:
            from game.combat_config import CombatConfig
            fatigue_multiplier = unit.attacks_this_turn - 1
            morale_loss = CombatConfig.ATTACK_FATIGUE_MORALE_PER_ATTACK * fatigue_multiplier
            cohesion_loss = CombatConfig.ATTACK_FATIGUE_COHESION_PER_ATTACK * fatigue_multiplier
            unit.stats.stats.morale = max(0, unit.stats.stats.morale - morale_loss)
            if hasattr(unit.stats.stats, 'current_cohesion'):
                unit.stats.stats.current_cohesion = max(0, unit.stats.stats.current_cohesion - cohesion_loss)
        
        # Mark units as engaged in combat (only for melee/close combat)
        if combat_mode in [CombatMode.MELEE, CombatMode.CHARGE]:
            unit.is_engaged_in_combat = True
            unit.engaged_with = target
            target.is_engaged_in_combat = True
            target.engaged_with = unit
            
        # Auto-face target when attacking (unless routing)
        if hasattr(unit, 'facing') and not unit.is_routing:
            unit.facing.face_towards(target.x, target.y, unit.x, unit.y)
            
        # Ranged attacks do not engage units in combat
        
        # Check attack angle for additional effects
        attack_angle = None
        extra_morale_penalty = 0
        extra_cohesion_penalty = 0
        should_check_routing = False
        
        if hasattr(target, 'facing'):
            attack_angle = target.facing.get_attack_angle(unit.x, unit.y, target.x, target.y)
            extra_morale_penalty = target.facing.get_morale_penalty(attack_angle)
            if hasattr(target.facing, 'get_cohesion_penalty'):
                extra_cohesion_penalty = target.facing.get_cohesion_penalty(attack_angle)

            # Check for routing on rear/flank attacks
            if attack_angle.is_rear or attack_angle.is_flank:
                should_check_routing = True

        from game.combat_config import CombatConfig
        mode_morale_shock = {
            CombatMode.MELEE: CombatConfig.MORALE_SHOCK_MELEE,
            CombatMode.RANGED: CombatConfig.MORALE_SHOCK_RANGED,
            CombatMode.SKIRMISH: CombatConfig.MORALE_SHOCK_SKIRMISH,
            CombatMode.CHARGE: CombatConfig.MORALE_SHOCK_CHARGE,
        }
        mode_cohesion_shock = {
            CombatMode.MELEE: CombatConfig.COHESION_SHOCK_MELEE,
            CombatMode.RANGED: CombatConfig.COHESION_SHOCK_RANGED,
            CombatMode.SKIRMISH: CombatConfig.COHESION_SHOCK_SKIRMISH,
            CombatMode.CHARGE: CombatConfig.COHESION_SHOCK_CHARGE,
        }
        if combat_mode not in mode_morale_shock or combat_mode not in mode_cohesion_shock:
            raise ValueError(f"Unsupported combat mode for shock: {combat_mode}")
        extra_morale_penalty += mode_morale_shock[combat_mode]
        extra_cohesion_penalty += mode_cohesion_shock[combat_mode]
        if extra_morale_penalty > 0 or extra_cohesion_penalty > 0:
            should_check_routing = True

        from game.systems.combat_resolver import CombatResolver
        CombatResolver.resolve_attack(
            attacker=unit,
            target=target,
            damage=damage,
            counter_damage=counter_damage,
            extra_morale_penalty=extra_morale_penalty,
            extra_cohesion_penalty=extra_cohesion_penalty,
            should_check_routing=should_check_routing,
            game_state=game_state
        )
        
        return {
            'success': True,
            'damage': damage,
            'counter_damage': counter_damage,
            'animation': 'attack',
            'target': target,
            'attack_angle': attack_angle,
            'extra_morale_penalty': extra_morale_penalty,
            'extra_cohesion_penalty': extra_cohesion_penalty,
            'should_check_routing': should_check_routing,
            'combat_mode': combat_mode
        }
        
    def calculate_damage(self, attacker, target, attacker_terrain=None, target_terrain=None, combat_mode=None) -> int:
        """Calculate damage to target based on combat mode"""
        # Get effective soldiers
        attacking_soldiers = attacker.stats.get_effective_soldiers(attacker_terrain)
        base_damage = attacking_soldiers * attacker.stats.stats.attack_per_soldier
        
        # Apply combat mode modifiers
        if combat_mode:
            if combat_mode == CombatMode.CHARGE:
                # Cavalry charges deal bonus damage
                base_damage *= 1.3
            elif combat_mode == CombatMode.SKIRMISH:
                # Skirmish attacks deal reduced damage
                base_damage *= 0.8
            # RANGED and MELEE use normal damage
        
        # Apply terrain combat modifier (but separate from height advantage)
        if attacker_terrain:
            terrain_modifier = attacker_terrain.get_combat_modifier_for_unit(attacker.unit_class)
            base_damage *= terrain_modifier
            
        # Apply morale modifier
        base_damage *= (attacker.morale / 100)  # Use property that includes general bonuses

        # Apply cohesion modifier
        if hasattr(attacker, 'cohesion'):
            from game.combat_config import CombatConfig
            if attacker.max_cohesion <= 0:
                raise ValueError("max_cohesion must be positive for damage calculation")
            cohesion_ratio = attacker.cohesion / attacker.max_cohesion
            base_damage *= max(CombatConfig.COHESION_DAMAGE_MIN_FACTOR, cohesion_ratio)
        
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
        if hasattr(defender, 'cohesion'):
            from game.combat_config import CombatConfig
            if defender.max_cohesion <= 0:
                raise ValueError("max_cohesion must be positive for counter damage calculation")
            cohesion_ratio = defender.cohesion / defender.max_cohesion
            base_damage *= max(CombatConfig.COHESION_DAMAGE_MIN_FACTOR, cohesion_ratio)
        
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
        
    def _is_valid_target(self, unit, target, game_state) -> bool:
        """Check if a target is valid for attack"""
        # Check fog of war visibility
        if hasattr(game_state, 'fog_of_war') and game_state.current_player is not None:
            visibility = game_state.fog_of_war.get_visibility_state(
                game_state.current_player, target.x, target.y
            )
            # Only target units we can see
            if visibility != VisibilityState.VISIBLE:
                return False
        
        # Use Chebyshev distance to include diagonals
        dx = abs(unit.x - target.x)
        dy = abs(unit.y - target.y)
        distance = max(dx, dy)
        if distance > self.attack_range:
            return False
            
        return True
        
    def get_valid_targets(self, unit, game_state) -> list:
        """Get list of valid attack targets"""
        if not self.can_execute(unit, game_state):
            return []
            
        targets = []
        for other in game_state.knights:
            if other.player_id != unit.player_id and self._is_valid_target(unit, other, game_state):
                targets.append(other)
                    
        return targets
        
    def get_attack_blocked_reason(self, unit, target, game_state) -> str:
        """Get reason why an attack is blocked (for user feedback)"""
        # Check basic requirements first
        if not self.can_execute(unit, game_state):
            base_cost = self.get_ap_cost(unit)
            if unit.action_points < base_cost:
                return "Not enough action points"
            if hasattr(unit, 'attacks_this_turn') and unit.attacks_this_turn > 0 and unit.morale < 50:
                return "Morale too low for additional attacks"
        
        # Check if it's an enemy
        if target.player_id == unit.player_id:
            return "Cannot attack friendly units"
            
        # Check visibility
        if hasattr(game_state, 'fog_of_war') and game_state.current_player is not None:
            visibility = game_state.fog_of_war.get_visibility_state(
                game_state.current_player, target.x, target.y
            )
            if visibility != VisibilityState.VISIBLE:
                return "Target not visible"
        
        # Check range
        dx = abs(unit.x - target.x)
        dy = abs(unit.y - target.y)
        distance = max(dx, dy)
        if distance > self.attack_range:
            return f"Target out of range (distance: {distance}, max range: {self.attack_range})"
            
        return "Attack should be possible"

class ArcherAttackBehavior(AttackBehavior):
    """Ranged attack behavior for archers"""
    
    def __init__(self):
        super().__init__(attack_range=3)
        # Keep name as "attack" so can_attack() works correctly
        self.name = "attack"
        
    def get_ap_cost(self, unit=None, target=None, game_state=None) -> int:
        """Ranged attacks cost less AP than melee, but still affected by terrain"""
        base_cost = 2  # Ranged attacks are quicker to execute
        
        # Add terrain-based attack cost for ranged attacks too (reduced penalty)
        if target and game_state and hasattr(game_state, 'terrain_map') and game_state.terrain_map:
            target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
            if target_terrain:
                # Get the base terrain movement cost (without unit-specific modifiers)
                terrain_movement_cost = target_terrain.movement_cost
                
                # Apply reduced terrain penalty for ranged attacks (1x instead of 2x)
                if terrain_movement_cost > 1.0:  # Only apply penalty for difficult terrain
                    terrain_penalty = int(terrain_movement_cost - 1.0)
                    base_cost += terrain_penalty
                
        return base_cost
        
    def _has_line_of_sight(self, unit, target, game_state) -> bool:
        """Check if archer has line of sight to target"""
        if not hasattr(game_state, 'fog_of_war'):
            return True
            
        # Check if unit has elevated vision
        vision_behavior = unit.get_behavior('VisionBehavior') if hasattr(unit, 'get_behavior') else None
        is_elevated = vision_behavior.is_elevated() if vision_behavior else False
        
        # Use fog of war's line of sight checking
        return game_state.fog_of_war._has_line_of_sight(game_state, (unit.x, unit.y), (target.x, target.y), is_elevated)
        
    def _is_valid_target(self, unit, target, game_state) -> bool:
        """Check if a target is valid for ranged attack (includes line of sight)"""
        # Check basic validity first
        if not super()._is_valid_target(unit, target, game_state):
            return False
            
        # For ranged attacks (archers), also check line of sight
        return self._has_line_of_sight(unit, target, game_state)
        
    def get_attack_blocked_reason(self, unit, target, game_state) -> str:
        """Get reason why a ranged attack is blocked (includes line-of-sight reasons)"""
        # Check basic reasons first
        base_reason = super().get_attack_blocked_reason(unit, target, game_state)
        if base_reason != "Attack should be possible":
            return base_reason
            
        # Check line of sight for ranged attacks
        if not self._has_line_of_sight(unit, target, game_state):
            return "No line of sight - arrows blocked by terrain"
            
        return "Attack should be possible"
