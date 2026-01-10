"""Refactored unit class using components and behaviors"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from game.components.stats import StatsComponent, UnitStats
from game.components.base import Behavior
from game.components.generals import GeneralRoster
from game.components.facing import FacingComponent, FacingDirection
from game.entities.knight import KnightClass
from game.combat_config import CombatConfig
from game.hex_utils import HexGrid
from game.behaviors.movement_service import MovementService

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
        
        # Facing component
        self.facing = FacingComponent()
        
        # Behaviors
        self.behaviors: Dict[str, Behavior] = {}
        
        # Reference to game state
        self.game_state = None
        
        # State flags
        self.is_garrisoned = False
        self.is_disrupted = False
        self.garrison_location = None
        self.in_enemy_zoc = False
        self.is_routing = False
        self.engaged_with = None
        self.is_engaged_in_combat = False
        
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
    def cohesion(self) -> float:
        """Current cohesion (formation integrity)"""
        return self.stats.stats.current_cohesion

    @cohesion.setter
    def cohesion(self, value: float):
        """Set current cohesion"""
        self.stats.stats.current_cohesion = value

    @property
    def max_cohesion(self) -> float:
        """Maximum cohesion value"""
        return self.stats.stats.max_cohesion

    @max_cohesion.setter
    def max_cohesion(self, value: float):
        """Set maximum cohesion"""
        self.stats.stats.max_cohesion = value
        
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
        behavior.attach(self)
        
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
    
    def has_component(self, component_name: str) -> bool:
        """Check if unit has a component"""
        # Currently we only have 'stats' and 'generals' components
        return component_name in ['stats', 'generals']
        
    def get_behavior(self, behavior_type: str) -> Optional[Behavior]:
        """Get a behavior by its type name (e.g. 'VisionBehavior')"""
        for behavior in self.behaviors.values():
            # Check exact match
            if type(behavior).__name__ == behavior_type:
                return behavior
            # Check if it's a subclass of the requested type
            behavior_class_name = type(behavior).__name__
            if behavior_type in behavior_class_name or behavior_class_name.endswith(behavior_type):
                return behavior
            # Check inheritance hierarchy
            for base_class in type(behavior).__mro__:
                if base_class.__name__ == behavior_type:
                    return behavior
        return None
    
    def get_component(self, component_name: str):
        """Get a component by name"""
        if component_name == 'stats':
            return self.stats
        elif component_name == 'generals':
            return self.generals
        return None
        
    def take_casualties(self, amount: int, game_state) -> bool:
        """Apply casualties to unit"""
        if game_state is None:
            raise ValueError("game_state is required when applying casualties")
        # Routing units are harder to hit effectively (they're fleeing/scattered)
        if self.is_routing:
            amount = int(amount * 0.7)  # 30% damage reduction for routing units
            
        was_destroyed = self.stats.take_casualties(amount)
        
        # Check for automatic routing after casualties (only if not already routing)
        if not was_destroyed and not self.is_routing:
            self.check_routing(game_state, shock_bonus=0.0)
            
        return was_destroyed
    
    def check_routing(self, game_state, shock_bonus: float) -> bool:
        """Check if unit should start routing based on morale, cohesion, and conditions"""
        if game_state is None:
            raise ValueError("game_state is required for routing checks")
        if shock_bonus is None:
            raise ValueError("shock_bonus is required for routing checks")
        # Already routing
        if self.is_routing:
            return True
            
        from game.combat_config import CombatConfig

        # Units with very low morale or cohesion start routing immediately
        if (self.morale <= CombatConfig.ROUTING_HARD_MORALE_THRESHOLD or
                self.cohesion <= CombatConfig.ROUTING_HARD_COHESION_THRESHOLD):
            self._start_routing(game_state)
            return True
            
        pressure_bonus = 0.0
        adjacent_enemies = 0
        adjacent_friendlies = 0
        for other in game_state.knights:
            if other == self or other.is_garrisoned:
                continue
            dx = abs(self.x - other.x)
            dy = abs(self.y - other.y)
            if dx <= 1 and dy <= 1 and (dx + dy > 0):
                if other.player_id != self.player_id:
                    adjacent_enemies += 1
                else:
                    adjacent_friendlies += 1

        if adjacent_enemies > adjacent_friendlies:
            pressure_bonus = CombatConfig.ROUTING_PRESSURE_BONUS

        route_chance = CombatConfig.calculate_routing_chance(
            morale=self.morale,
            cohesion=self.cohesion,
            pressure_bonus=pressure_bonus,
            shock_bonus=shock_bonus
        )
        if route_chance > 0:
            import random
            if random.random() < (route_chance / 100.0):
                self._start_routing(game_state)
                return True
                
        return False
        
    def _start_routing(self, game_state=None):
        """Start routing and attempt immediate flee movement"""
        was_routing = self.is_routing
        self.is_routing = True
        
        # If game state is available and unit just started routing, try to auto-flee
        if not was_routing and game_state is not None:
            self._attempt_auto_routing_movement(game_state)
    
    def _attempt_auto_routing_movement(self, game_state):
        """Attempt automatic routing movement away from enemies"""
        if not self.is_routing:
            return False
            
        # Check if unit has movement behavior and can move
        movement_behavior = self.get_behavior('MovementBehavior')
        if not movement_behavior:
            return False
            
        # Get routing movement options
        routing_moves = movement_behavior._get_routing_moves(self, game_state)
        if not routing_moves:
            return False
            
        # Choose the best routing move (furthest from nearest enemy)
        enemies = [k for k in game_state.knights if k.player_id != self.player_id]
        if not enemies:
            return False
            
        nearest_enemy = min(enemies, key=lambda e: abs(e.x - self.x) + abs(e.y - self.y))
        
        # Find the move that gets furthest from nearest enemy
        best_move = None
        best_distance = 0
        
        for move_x, move_y in routing_moves:
            distance = abs(move_x - nearest_enemy.x) + abs(move_y - nearest_enemy.y)
            if distance > best_distance:
                best_distance = distance
                best_move = (move_x, move_y)
        
        # Execute the routing movement if we found a good move
        if best_move:
            old_x, old_y = self.x, self.y
            new_x, new_y = best_move
            
            # Check if position is valid and not occupied
            if (0 <= new_x < game_state.board_width and 
                0 <= new_y < game_state.board_height and
                not game_state.get_knight_at(new_x, new_y)):
                
                # Execute the routing movement directly
                self.x = new_x
                self.y = new_y
                
                # Consume some AP for the panic movement (but don't block future movement)
                self.action_points = max(0, self.action_points - 1)
                
                # Add message about routing movement
                if hasattr(game_state, 'add_message'):
                    game_state.add_message(f"{self.name} routs and flees!", priority=2)
                
                # Update facing to show the unit is fleeing away from enemy
                if hasattr(self, 'facing') and self.facing:
                    self.facing.update_facing_from_movement(old_x, old_y, new_x, new_y)
                
                return True
        
        return False
        
    def end_turn(self):
        """Reset for new turn"""
        self.action_points = self.max_action_points
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False
        
        # Regenerate will
        self.stats.regenerate_will(20)
        
        from game.combat_config import CombatConfig

        # Apply base morale/cohesion regeneration
        if self.is_routing:
            base_morale_regen = CombatConfig.MORALE_REGEN_ROUTING
            base_cohesion_regen = CombatConfig.COHESION_REGEN_ROUTING
        else:
            base_morale_regen = CombatConfig.MORALE_REGEN_BASE
            base_cohesion_regen = CombatConfig.COHESION_REGEN_BASE

        if self.is_engaged_in_combat:
            base_morale_regen *= CombatConfig.REGEN_ENGAGED_MULTIPLIER
            base_cohesion_regen *= CombatConfig.REGEN_ENGAGED_MULTIPLIER

        # Apply general morale regeneration bonuses
        bonuses = self.generals.get_all_passive_bonuses(self)
        general_morale_regen = bonuses.get('morale_regen', 0)
        
        total_morale_regen = base_morale_regen + general_morale_regen
        self.stats.stats.morale = min(self.stats.stats.max_morale, self.stats.stats.morale + total_morale_regen)
        self.stats.stats.current_cohesion = min(
            self.stats.stats.max_cohesion,
            self.stats.stats.current_cohesion + base_cohesion_regen
        )
        
        # Check if routing unit recovers enough morale to stop routing
        self.has_rallied_this_turn = False
        if (self.is_routing and
                self.stats.stats.morale >= CombatConfig.RALLY_MORALE_THRESHOLD and
                self.stats.stats.current_cohesion >= CombatConfig.RALLY_COHESION_THRESHOLD):
            # Additional rally conditions for realism
            rally_chance = CombatConfig.RALLY_BASE_CHANCE
            
            # Better chance to rally with higher morale
            if self.stats.stats.morale >= CombatConfig.RALLY_HIGH_MORALE_THRESHOLD:
                rally_chance = CombatConfig.RALLY_HIGH_MORALE_CHANCE

            if self.stats.stats.current_cohesion >= CombatConfig.RALLY_HIGH_COHESION_THRESHOLD:
                rally_chance *= CombatConfig.RALLY_HIGH_COHESION_MULTIPLIER
                
            # Reduced chance if heavily damaged
            soldier_ratio = self.soldiers / self.max_soldiers
            if soldier_ratio < 0.5:  # Less than 50% soldiers remaining
                rally_chance *= CombatConfig.RALLY_LOW_STRENGTH_MULTIPLIER
                
            import random
            if random.random() < rally_chance:
                self.is_routing = False
                self.has_rallied_this_turn = True
            
        # Reset temporary combat modifiers
        self.temp_damage_multiplier = 1.0
        self.temp_vulnerability = 1.0
        
        # Reset attack counter for new turn
        self.attacks_this_turn = 0
        
        # Update generals
        self.generals.on_turn_end()
        
    def has_zone_of_control(self) -> bool:
        """Check if unit exerts Zone of Control"""
        # Only non-routing units with good morale have ZOC
        from game.combat_config import CombatConfig
        return (not self.is_routing and
                self.morale >= CombatConfig.ZOC_MORALE_THRESHOLD and
                self.cohesion >= CombatConfig.ZOC_COHESION_THRESHOLD and
                self.soldiers > 0)
        
    def is_in_enemy_zoc(self, game_state) -> Tuple[bool, Optional['Unit']]:
        """Check if unit is in enemy Zone of Control"""
        from game.systems.engagement import EngagementSystem
        return EngagementSystem.is_unit_in_enemy_zoc(self, game_state)
        
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
                formation_width=40,
                max_cohesion=100.0,
                current_cohesion=100.0
            ),
            KnightClass.ARCHER: UnitStats(
                max_soldiers=80,
                current_soldiers=80,
                attack_per_soldier=1.5,
                base_defense=20,
                formation_width=40,
                max_cohesion=85.0,
                current_cohesion=85.0
            ),
            KnightClass.CAVALRY: UnitStats(
                max_soldiers=50,
                current_soldiers=50,
                attack_per_soldier=2.0,
                base_defense=25,
                formation_width=25,
                max_cohesion=90.0,
                current_cohesion=90.0
            ),
            KnightClass.MAGE: UnitStats(
                max_soldiers=30,
                current_soldiers=30,
                attack_per_soldier=3.0,
                base_defense=15,
                formation_width=15,
                max_cohesion=75.0,
                current_cohesion=75.0
            )
        }
        return stats_by_class.get(self.unit_class, UnitStats(100, 100, 1.0, 25, 30, 90.0, 90.0))
        
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
        
    def is_heavy_unit(self) -> bool:
        """Check if this unit is considered heavy"""
        return CombatConfig.is_heavy_unit(self.unit_class.value)
        
    def is_light_unit(self) -> bool:
        """Check if this unit is considered light"""
        return CombatConfig.is_light_unit(self.unit_class.value)
        
    def get_terrain(self, game_state=None):
        """Get the terrain this unit is currently on"""
        # Use provided game_state or the one stored in the unit
        gs = game_state or self.game_state
        if gs and hasattr(gs, 'terrain_map'):
            return gs.terrain_map.get_terrain(self.x, self.y)
        return None
        
    def can_break_away_from(self, enemy_unit) -> bool:
        """Check if this unit can break away from combat with enemy"""
        if not self.is_engaged_in_combat:
            return False
            
        if self.action_points < CombatConfig.MIN_AP_FOR_BREAKAWAY:
            return False
            
        breakaway_chance = CombatConfig.get_breakaway_chance(
            enemy_unit.unit_class.value, 
            self.unit_class.value
        )
        
        return breakaway_chance > 0
        
    def attempt_breakaway(self, enemy_unit, game_state) -> Dict[str, Any]:
        """Attempt to break away from combat"""
        if not self.can_break_away_from(enemy_unit):
            return {'success': False, 'reason': 'Cannot break away'}
            
        # Calculate breakaway chance
        breakaway_chance = CombatConfig.get_breakaway_chance(
            enemy_unit.unit_class.value, 
            self.unit_class.value
        )
        
        # Roll for success
        import random
        roll = random.randint(1, 100)
        success = roll <= breakaway_chance
        
        # Consume AP
        self.action_points -= CombatConfig.BREAKAWAY_AP_COST
        
        if success:
            # Successful breakaway
            self.is_engaged_in_combat = False
            self.engaged_with = None
            enemy_unit.is_engaged_in_combat = False
            enemy_unit.engaged_with = None
            
            return {
                'success': True,
                'message': f'{self.name} successfully broke away from combat!',
                'opportunity_attack': True  # Enemy gets opportunity attack
            }
        else:
            # Failed breakaway
            self.morale = max(0, self.morale - CombatConfig.FAILED_BREAKAWAY_MORALE_LOSS)
            return {
                'success': False,
                'message': f'{self.name} failed to break away and lost morale!',
                'morale_loss': CombatConfig.FAILED_BREAKAWAY_MORALE_LOSS
            }
        
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
        
    # Compatibility methods for old Knight class interface
    def consume_move_ap(self):
        """Compatibility method - consume AP for movement"""
        if self.action_points >= 1 and not self.has_moved:
            self.action_points -= 1
            self.has_moved = True
            return True
        return False
        
    def consume_attack_ap(self):
        """Compatibility method - consume AP for attack"""
        from game.combat_config import CombatConfig

        ap_cost = CombatConfig.get_attack_ap_cost(self.unit_class.value)
                
        if self.action_points >= ap_cost and not self.has_acted:
            self.action_points -= ap_cost
            self.has_acted = True
            return True
        return False
        
    def calculate_damage(self, target, attacker_terrain=None, target_terrain=None):
        """Compatibility method - calculate damage using combat behavior"""
        if 'attack' in self.behaviors:
            attack_behavior = self.behaviors['attack']
            return attack_behavior.calculate_damage(self, target, attacker_terrain, target_terrain)
        else:
            # Fallback calculation
            attacking_soldiers = self.soldiers
            base_damage = attacking_soldiers * 1.0  # Default attack per soldier
            return max(1, int(base_damage * 0.25))  # 25% casualties
            
    def calculate_counter_damage(self, attacker, attacker_terrain=None, defender_terrain=None):
        """Compatibility method - calculate counter damage using combat behavior"""
        if 'attack' in self.behaviors:
            attack_behavior = self.behaviors['attack']
            return attack_behavior.calculate_counter_damage(self, attacker, defender_terrain, attacker_terrain)
        else:
            # Fallback calculation - archers don't counter in melee
            if self.unit_class == KnightClass.ARCHER:
                return 0
            defending_soldiers = self.soldiers
            base_damage = defending_soldiers * 1.0
            return max(0, int(base_damage * 0.15))  # 15% counter casualties
    
    def calculate_battle_losses(self, target, attacker_terrain=None, target_terrain=None):
        """Calculate battle losses for both attacker and defender
        
        Returns:
            Dict containing:
            - attacker_damage: Damage dealt to attacker (counter-attack)
            - defender_damage: Damage dealt to defender
            - attacker_casualties: Estimated casualties for attacker
            - defender_casualties: Estimated casualties for defender
            - attacker_casualty_percent: Percentage of attacker's force lost
            - defender_casualty_percent: Percentage of defender's force lost
        """
        # Calculate base damage values
        defender_damage = self.calculate_damage(target, attacker_terrain, target_terrain)
        attacker_damage = target.calculate_counter_damage(self, attacker_terrain, target_terrain)
        
        # Calculate casualties (actual casualties will be applied by animation)
        defender_casualties = min(defender_damage, target.soldiers)
        attacker_casualties = min(attacker_damage, self.soldiers)
        
        # Calculate casualty percentages
        attacker_casualty_percent = (attacker_casualties / self.max_soldiers) * 100 if self.max_soldiers > 0 else 0
        defender_casualty_percent = (defender_casualties / target.max_soldiers) * 100 if target.max_soldiers > 0 else 0
        
        # Apply general bonuses/reductions for more accurate estimation
        # These will be applied again during actual combat, this is just for preview
        if hasattr(target, 'get_damage_reduction'):
            reduction = target.get_damage_reduction()
            defender_casualties = int(defender_casualties * (1 - reduction))
            defender_casualty_percent = (defender_casualties / target.max_soldiers) * 100 if target.max_soldiers > 0 else 0
            
        if hasattr(self, 'get_damage_reduction'):
            reduction = self.get_damage_reduction()
            attacker_casualties = int(attacker_casualties * (1 - reduction))
            attacker_casualty_percent = (attacker_casualties / self.max_soldiers) * 100 if self.max_soldiers > 0 else 0
        
        return {
            'attacker_damage': attacker_damage,
            'defender_damage': defender_damage,
            'attacker_casualties': attacker_casualties,
            'defender_casualties': defender_casualties,
            'attacker_casualty_percent': round(attacker_casualty_percent, 1),
            'defender_casualty_percent': round(defender_casualty_percent, 1)
        }
            
    def get_possible_moves(self, board_width, board_height, terrain_map=None, game_state=None):
        """Get possible moves using centralized MovementService"""
        movement_service = MovementService()
        return movement_service.get_possible_moves(self, game_state)
            
    def get_effective_soldiers(self, terrain=None):
        """Compatibility method - get effective fighting soldiers"""
        return self.stats.get_effective_soldiers(terrain)
        
    def _has_adjacent_friendly(self, x, y, game_state):
        """Compatibility method - check if position has adjacent friendly units"""
        if not game_state:
            return False
        
        hex_grid = HexGrid()
        pos_hex = hex_grid.offset_to_axial(x, y)
        neighbors = pos_hex.get_neighbors()
        
        for neighbor_hex in neighbors:
            check_x, check_y = hex_grid.axial_to_offset(neighbor_hex)
            for knight in game_state.knights:
                if (knight != self and knight.player_id == self.player_id and 
                    knight.x == check_x and knight.y == check_y and not knight.is_garrisoned):
                    return True
        return False
        
    def move(self, new_x, new_y):
        """Simple move for AI - delegates to MovementService for consistency"""
        # For AI moves, we'll create a minimal game state context
        # This ensures consistent movement logic across all callers
        from game.behaviors.movement_service import MovementService
        movement_service = MovementService()
        
        # For AI, we skip some game state validations but still use core logic
        if self.can_move() and self.action_points > 0:
            old_x, old_y = self.x, self.y
            self.x = new_x
            self.y = new_y
            
            # Update facing based on movement direction
            if hasattr(self, 'facing'):
                self.facing.update_facing_from_movement(old_x, old_y, new_x, new_y)
            
            movement_service.consume_movement_ap(self, 1.0)
            return True
        return False
    
    def can_charge(self, target, game_state):
        """Check if cavalry can charge the target"""
        if self.knight_class != KnightClass.CAVALRY:
            return False, "Only cavalry can charge"
        
        # Use will property which goes through stats component
        if self.will < 40:
            return False, "Not enough will (need 40)"
        
        if self.has_used_special:
            return False, "Already used special ability"
        
        if self.is_routing:
            return False, "Routing units cannot charge"
        
        # Must be adjacent (including diagonals)
        dx = abs(self.x - target.x)
        dy = abs(self.y - target.y)
        if not (dx <= 1 and dy <= 1 and (dx + dy > 0)):
            return False, "Must be adjacent to charge"
        
        # Check terrain restrictions for cavalry charges
        if game_state.terrain_map:
            # Cavalry cannot charge when on hills
            cavalry_terrain = game_state.terrain_map.get_terrain(self.x, self.y)
            if cavalry_terrain and cavalry_terrain.type.value.lower() == 'hills':
                return False, "Cannot charge from hills"
            
            # Cavalry cannot charge enemies on hills
            target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
            if target_terrain and target_terrain.type.value.lower() == 'hills':
                return False, "Cannot charge enemies on hills"
        
        # Charges are allowed if terrain permits
        # The outcome (damage/push) depends on what's behind the target
        return True, "Can charge"
    
    def calculate_charge_losses(self, target, game_state):
        """Calculate potential losses from a cavalry charge
        
        Returns:
            Dict containing estimated casualties and effects
        """
        if not self.can_charge(target, game_state)[0]:
            return {
                'can_charge': False,
                'reason': 'Cannot perform charge'
            }
            
        # Calculate push direction
        push_dir_x = target.x - self.x
        push_dir_y = target.y - self.y
        push_x = target.x + push_dir_x
        push_y = target.y + push_dir_y
        
        # Check what's behind the target
        obstacle_type = None
        obstacle_unit = None
        can_push = True
        
        # Check map edge
        if not (0 <= push_x < game_state.board_width and 0 <= push_y < game_state.board_height):
            can_push = False
            obstacle_type = 'wall'
        # Check castles
        elif any(castle.contains_position(push_x, push_y) for castle in game_state.castles):
            can_push = False
            obstacle_type = 'wall'
        # Check terrain
        elif game_state.terrain_map and not game_state.terrain_map.is_passable(push_x, push_y, target.knight_class):
            can_push = False
            obstacle_type = 'terrain'
        else:
            # Check for units
            for knight in game_state.knights:
                if knight.x == push_x and knight.y == push_y and not knight.is_garrisoned:
                    obstacle_unit = knight
                    can_push = False
                    obstacle_type = 'unit'
                    break
        
        # Calculate base charge damage
        base_charge_damage = int(self.soldiers * 0.8)  # 80% of cavalry as base damage
        
        # Calculate damage based on obstacle type
        charge_damage = base_charge_damage
        self_damage = int(self.soldiers * 0.05)  # Default self-damage
        collateral_damage = 0
        collateral_unit = None
        morale_loss = 15  # Default morale loss
        
        if not can_push:
            if obstacle_type == 'wall':
                # Crushing charge against wall/castle
                charge_damage = int(base_charge_damage * 1.5)
                self_damage = int(self.soldiers * 0.1)
                morale_loss = 30
            elif obstacle_type == 'terrain':
                # Trapped by terrain
                charge_damage = int(base_charge_damage * 1.3)
                self_damage = int(self.soldiers * 0.08)
                morale_loss = 25
            elif obstacle_type == 'unit' and obstacle_unit:
                # Slammed into another unit
                charge_damage = int(base_charge_damage * 1.2)
                self_damage = int(self.soldiers * 0.07)
                collateral_damage = int(base_charge_damage * 0.3)
                collateral_unit = obstacle_unit
                morale_loss = 20
        
        # Calculate casualties (capped by available soldiers)
        defender_casualties = min(charge_damage, target.soldiers)
        attacker_casualties = min(self_damage, self.soldiers)
        
        # Calculate casualty percentages
        attacker_casualty_percent = (attacker_casualties / self.max_soldiers) * 100 if self.max_soldiers > 0 else 0
        defender_casualty_percent = (defender_casualties / target.max_soldiers) * 100 if target.max_soldiers > 0 else 0
        
        result = {
            'can_charge': True,
            'can_push': can_push,
            'obstacle_type': obstacle_type,
            'charge_damage': charge_damage,
            'self_damage': self_damage,
            'defender_casualties': defender_casualties,
            'attacker_casualties': attacker_casualties,
            'attacker_casualty_percent': round(attacker_casualty_percent, 1),
            'defender_casualty_percent': round(defender_casualty_percent, 1),
            'morale_loss': morale_loss
        }
        
        if collateral_unit:
            collateral_casualties = min(collateral_damage, collateral_unit.soldiers)
            collateral_casualty_percent = (collateral_casualties / collateral_unit.max_soldiers) * 100 if collateral_unit.max_soldiers > 0 else 0
            result.update({
                'collateral_unit': collateral_unit,
                'collateral_damage': collateral_damage,
                'collateral_casualties': collateral_casualties,
                'collateral_casualty_percent': round(collateral_casualty_percent, 1)
            })
            
        return result
    
    def execute_charge(self, target, game_state):
        """Execute cavalry charge against target"""
        can_charge, reason = self.can_charge(target, game_state)
        if not can_charge:
            return False, reason
        
        # Consume will through property
        self.will -= 40
        self.has_used_special = True
        
        # Initialize message variable
        message = ""
        
        # Calculate push direction
        push_dir_x = target.x - self.x
        push_dir_y = target.y - self.y
        push_x = target.x + push_dir_x
        push_y = target.y + push_dir_y
        
        # Check what's behind the target
        obstacle_type = None
        obstacle_unit = None
        can_push = True
        
        # Check map edge
        if not (0 <= push_x < game_state.board_width and 0 <= push_y < game_state.board_height):
            can_push = False
            obstacle_type = 'wall'
        # Check castles
        elif any(castle.contains_position(push_x, push_y) for castle in game_state.castles):
            can_push = False
            obstacle_type = 'wall'
        # Check terrain
        elif game_state.terrain_map and not game_state.terrain_map.is_passable(push_x, push_y, target.knight_class):
            can_push = False
            obstacle_type = 'terrain'
        else:
            # Check for units
            for knight in game_state.knights:
                if knight.x == push_x and knight.y == push_y and not knight.is_garrisoned:
                    obstacle_unit = knight
                    can_push = False
                    obstacle_type = 'unit'
                    break
        
        # Calculate base charge damage
        base_charge_damage = int(self.soldiers * 0.8)  # 80% of cavalry as base damage
        
        # Apply damage based on obstacle type
        if not can_push:
            if obstacle_type == 'wall':
                # Crushing charge against wall/castle
                charge_damage = int(base_charge_damage * 1.5)
                self_damage = int(self.soldiers * 0.1)
                target.take_casualties(charge_damage, game_state)
                if hasattr(target, 'morale'):
                    target.morale = max(0, target.morale - 30)
                if hasattr(target, 'cohesion'):
                    from game.combat_config import CombatConfig
                    target.cohesion = max(0, target.cohesion - (30 * CombatConfig.CHARGE_COHESION_MULTIPLIER))
                self.take_casualties(self_damage, game_state)
                message = f"Devastating charge! {target.name} crushed against the wall!"
                
            elif obstacle_type == 'terrain':
                # Trapped by terrain
                charge_damage = int(base_charge_damage * 1.3)
                self_damage = int(self.soldiers * 0.08)
                target.take_casualties(charge_damage, game_state)
                if hasattr(target, 'morale'):
                    target.morale = max(0, target.morale - 25)
                if hasattr(target, 'cohesion'):
                    from game.combat_config import CombatConfig
                    target.cohesion = max(0, target.cohesion - (25 * CombatConfig.CHARGE_COHESION_MULTIPLIER))
                self.take_casualties(self_damage, game_state)
                message = f"Crushing charge! {target.name} trapped by terrain!"
                
            elif obstacle_type == 'unit' and obstacle_unit:
                # Slammed into another unit
                charge_damage = int(base_charge_damage * 1.2)
                self_damage = int(self.soldiers * 0.07)
                collateral_damage = int(base_charge_damage * 0.3)
                
                # Apply damages
                target.take_casualties(charge_damage, game_state)
                if hasattr(target, 'morale'):
                    target.morale = max(0, target.morale - 20)
                if hasattr(target, 'cohesion'):
                    from game.combat_config import CombatConfig
                    target.cohesion = max(0, target.cohesion - (20 * CombatConfig.CHARGE_COHESION_MULTIPLIER))
                self.take_casualties(self_damage, game_state)
                
                # Collateral damage to the unit behind
                obstacle_unit.take_casualties(collateral_damage, game_state)
                if hasattr(obstacle_unit, 'morale'):
                    obstacle_unit.morale = max(0, obstacle_unit.morale - 15)
                if hasattr(obstacle_unit, 'cohesion'):
                    from game.combat_config import CombatConfig
                    obstacle_unit.cohesion = max(0, obstacle_unit.cohesion - (15 * CombatConfig.CHARGE_COHESION_MULTIPLIER))
                
                message = f"Thunderous charge! {target.name} slammed into {obstacle_unit.name}!"
        else:
            # Normal charge with push
            charge_damage = base_charge_damage
            self_damage = int(self.soldiers * 0.05)
            
            target.take_casualties(charge_damage, game_state)
            if hasattr(target, 'morale'):
                target.morale = max(0, target.morale - 15)
            if hasattr(target, 'cohesion'):
                from game.combat_config import CombatConfig
                target.cohesion = max(0, target.cohesion - (15 * CombatConfig.CHARGE_COHESION_MULTIPLIER))
            self.take_casualties(self_damage, game_state)
            
            # Execute push
            target.x = push_x
            target.y = push_y
            
            message = f"Successful charge! {target.name} pushed back!"
        
        # Check if target routed
        if target.soldiers <= 0:
            message += f" {target.name} destroyed!"
        elif not target.is_routing:
            from game.combat_config import CombatConfig
            shock_bonus = 0.0
            if hasattr(target, 'morale'):
                shock_bonus += max(0.0, CombatConfig.ROUTING_MORALE_THRESHOLD - target.morale)
            if hasattr(target, 'cohesion'):
                shock_bonus += max(0.0, CombatConfig.ROUTING_COHESION_THRESHOLD - target.cohesion)
            if target.check_routing(game_state, shock_bonus=shock_bonus):
                message += f" {target.name} is routing!"
        
        return True, message

    def clone_for_simulation(self):
        """Create a lightweight clone of this unit for AI simulation"""
        import copy
        # Create a new instance without calling __init__
        cls = self.__class__
        clone = cls.__new__(cls)
        
        # Copy essential primitive state
        clone.name = self.name
        clone.unit_class = self.unit_class
        clone.position = UnitPosition(self.x, self.y)
        clone.player_id = self.player_id
        clone.action_points = self.action_points
        clone.max_action_points = self.max_action_points
        
        # Copy turn state flags
        clone.has_moved = self.has_moved
        clone.has_acted = self.has_acted
        clone.has_used_special = self.has_used_special
        clone.selected = False # AI clones shouldn't be selected
        
        # Copy essential flags
        clone.is_routing = self.is_routing
        clone.is_disrupted = self.is_disrupted
        clone.is_garrisoned = self.is_garrisoned
        clone.is_engaged_in_combat = self.is_engaged_in_combat
        
        # Copy ZOC and engagement state
        clone.in_enemy_zoc = self.in_enemy_zoc
        clone.engaged_with = self.engaged_with # Reference to original unit (acceptable for simulation checks)
        clone.garrison_location = self.garrison_location
        
        # Copy temporary modifiers
        clone.temp_damage_multiplier = self.temp_damage_multiplier
        clone.temp_vulnerability = self.temp_vulnerability
        
        # Shallow copy components that might be modified
        # Note: StatsComponent needs to be cloned because HP/Morale changes
        clone.stats = copy.copy(self.stats)
        # Stats inside StatsComponent also needs to be cloned
        if hasattr(self.stats, 'stats'):
            clone.stats.stats = copy.copy(self.stats.stats)
            
        # Behaviors and Generals can be shared (read-only in simulation usually)
        # but we need to ensure they point to the NEW unit
        clone.behaviors = self.behaviors.copy()
        clone.generals = self.generals # Shared for speed
        clone.facing = copy.copy(self.facing) if hasattr(self, 'facing') else None
        
        return clone
