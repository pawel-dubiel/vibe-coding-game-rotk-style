"""Adapter to make new Unit class compatible with existing Knight interface"""
from typing import Optional, List, Tuple, TYPE_CHECKING
from game.entities.unit import Unit
from game.entities.knight import Knight, KnightClass

if TYPE_CHECKING:
    from game.game_state import GameState

class KnightAdapter(Knight):
    """Adapter that wraps a Unit to provide Knight interface"""
    
    def __init__(self, unit: Unit):
        # Don't call parent __init__ to avoid duplication
        self.unit = unit
        
        # Map properties
        self.name = unit.name
        self.knight_class = unit.unit_class
        self.x = unit.x
        self.y = unit.y
        
        # These will be delegated to unit
        self._selected = unit.selected
        self._player_id = unit.player_id
        
    # Delegate properties to unit
    @property
    def x(self):
        return self.unit.x
        
    @x.setter
    def x(self, value):
        self.unit.x = value
        
    @property
    def y(self):
        return self.unit.y
        
    @y.setter
    def y(self, value):
        self.unit.y = value
        
    @property
    def selected(self):
        return self.unit.selected
        
    @selected.setter
    def selected(self, value):
        self.unit.selected = value
        
    @property
    def player_id(self):
        return self.unit.player_id
        
    @player_id.setter
    def player_id(self, value):
        self.unit.player_id = value
        
    @property
    def soldiers(self):
        return self.unit.soldiers
        
    @soldiers.setter
    def soldiers(self, value):
        self.unit.stats.stats.current_soldiers = value
        
    @property
    def max_soldiers(self):
        return self.unit.max_soldiers
        
    @property
    def health(self):
        return self.unit.health
        
    @property
    def max_health(self):
        return self.unit.max_health
        
    @property
    def action_points(self):
        return self.unit.action_points
        
    @action_points.setter
    def action_points(self, value):
        self.unit.action_points = value
        
    @property
    def max_action_points(self):
        return self.unit.max_action_points
        
    @property
    def morale(self):
        return self.unit.morale
        
    @morale.setter
    def morale(self, value):
        self.unit.morale = value
        
    @property
    def will(self):
        return self.unit.will
        
    @will.setter
    def will(self, value):
        self.unit.will = value
        
    @property
    def max_will(self):
        return self.unit.max_will
        
    @property
    def has_moved(self):
        return self.unit.has_moved
        
    @has_moved.setter
    def has_moved(self, value):
        self.unit.has_moved = value
        
    @property
    def has_acted(self):
        return self.unit.has_acted
        
    @has_acted.setter
    def has_acted(self, value):
        self.unit.has_acted = value
        
    @property
    def has_used_special(self):
        return self.unit.has_used_special
        
    @has_used_special.setter
    def has_used_special(self, value):
        self.unit.has_used_special = value
        
    @property
    def is_garrisoned(self):
        return self.unit.is_garrisoned
        
    @is_garrisoned.setter
    def is_garrisoned(self, value):
        self.unit.is_garrisoned = value
        
    @property
    def garrison_location(self):
        return self.unit.garrison_location
        
    @garrison_location.setter
    def garrison_location(self, value):
        self.unit.garrison_location = value
        
    @property
    def in_enemy_zoc(self):
        return self.unit.in_enemy_zoc
        
    @in_enemy_zoc.setter
    def in_enemy_zoc(self, value):
        self.unit.in_enemy_zoc = value
        
    @property
    def is_routing(self):
        return self.unit.is_routing
        
    @is_routing.setter
    def is_routing(self, value):
        self.unit.is_routing = value
        
    @property
    def engaged_with(self):
        return self.unit.engaged_with
        
    @engaged_with.setter
    def engaged_with(self, value):
        self.unit.engaged_with = value
        
    # Delegate methods
    def can_move(self):
        return self.unit.can_move()
        
    def can_attack(self):
        return self.unit.can_attack()
        
    def take_casualties(self, amount):
        return self.unit.take_casualties(amount)
        
    def end_turn(self):
        self.unit.end_turn()
        
    def has_zone_of_control(self):
        return self.unit.has_zone_of_control()
        
    def is_in_enemy_zoc(self, game_state):
        return self.unit.is_in_enemy_zoc(game_state)
        
    def get_possible_moves(self, board_width, board_height, terrain_map=None, game_state=None):
        """Get possible moves using movement behavior"""
        if 'move' not in self.unit.behaviors:
            return []
            
        # Create a minimal game state if needed
        if game_state is None and terrain_map is not None:
            class MinimalGameState:
                pass
            game_state = MinimalGameState()
            game_state.board_width = board_width
            game_state.board_height = board_height
            game_state.terrain_map = terrain_map
            game_state.knights = []
            
        return self.unit.behaviors['move'].get_possible_moves(self.unit, game_state)
        
    def consume_move_ap(self):
        """Consume AP for movement"""
        if 'move' in self.unit.behaviors:
            self.unit.action_points -= self.unit.behaviors['move'].get_ap_cost()
            self.unit.has_moved = True
            
    def consume_attack_ap(self):
        """Consume AP for attack"""
        if 'attack' in self.unit.behaviors:
            self.unit.action_points -= self.unit.behaviors['attack'].get_ap_cost()
            self.unit.has_acted = True
            
    def calculate_damage(self, target, attacker_terrain=None, target_terrain=None):
        """Calculate damage using attack behavior"""
        if 'attack' in self.unit.behaviors:
            behavior = self.unit.behaviors['attack']
            # Convert target if it's an adapter
            target_unit = target.unit if isinstance(target, KnightAdapter) else target
            return behavior.calculate_damage(self.unit, target_unit, attacker_terrain, target_terrain)
        return 0
        
    def calculate_counter_damage(self, attacker, attacker_terrain=None, defender_terrain=None):
        """Calculate counter damage using attack behavior"""
        if 'attack' in self.unit.behaviors:
            behavior = self.unit.behaviors['attack']
            # Convert attacker if it's an adapter
            attacker_unit = attacker.unit if isinstance(attacker, KnightAdapter) else attacker
            return behavior.calculate_counter_damage(self.unit, attacker_unit, defender_terrain, attacker_terrain)
        return 0
        
    def can_charge(self, target, game_state):
        """Check if can charge using cavalry charge behavior"""
        if 'cavalry_charge' not in self.unit.behaviors:
            return False, "Not cavalry"
            
        if not self.unit.behaviors['cavalry_charge'].can_execute(self.unit, game_state):
            return False, "Cannot charge"
            
        # Additional checks from behavior
        distance = abs(self.x - target.x) + abs(self.y - target.y)
        if distance != 1:
            return False, "Target not adjacent"
            
        return True, "Can charge"
        
    def execute_charge(self, target, game_state):
        """Execute charge using cavalry charge behavior"""
        if 'cavalry_charge' not in self.unit.behaviors:
            return False, "Not cavalry"
            
        # Convert target if needed
        target_unit = target.unit if isinstance(target, KnightAdapter) else target
        
        result = self.unit.behaviors['cavalry_charge'].execute(self.unit, game_state, target=target_unit)
        
        if result['success']:
            # Apply damage to primary target
            target.take_casualties(result['damage'])
            target.morale = max(0, target.morale - result['morale_damage'])
            self.take_casualties(result['self_damage'])
            
            # Handle collateral damage if any
            if 'collateral_unit' in result and result['collateral_unit']:
                collateral_unit = result['collateral_unit']
                collateral_damage = result['collateral_damage']
                
                # Apply collateral damage
                if hasattr(collateral_unit, 'take_casualties'):
                    collateral_unit.take_casualties(collateral_damage)
                    # Also apply some morale damage from the chaos
                    if hasattr(collateral_unit, 'morale'):
                        collateral_unit.morale = max(0, collateral_unit.morale - 10)
            
            # Handle push
            if result['push']:
                target.x, target.y = result['push_to']
                
            return True, result['message']
            
        return False, result.get('reason', 'Charge failed')
        
    def get_effective_soldiers(self, terrain=None):
        """Get effective soldiers"""
        return self.unit.stats.get_effective_soldiers(terrain)
        
    # Additional compatibility properties
    @property
    def base_defense(self):
        return self.unit.stats.stats.base_defense
        
    @property
    def defense(self):
        """Defense value with morale modifier"""
        return self.base_defense * (self.morale / 100)
        
    @property
    def formation_width(self):
        return self.unit.stats.stats.formation_width