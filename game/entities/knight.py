"""Minimal Knight class for legacy compatibility"""
from enum import Enum
from game.hex_utils import HexGrid

class KnightClass(Enum):
    """Unit class types"""
    WARRIOR = "Warrior"
    ARCHER = "Archer"
    CAVALRY = "Cavalry"
    MAGE = "Mage"


class Knight:
    """Legacy Knight class - use Unit with behaviors for new code
    
    This class exists only for backward compatibility with tests and
    legacy code. All game logic should use Unit instances created by
    UnitFactory, which properly implement the behavior pattern.
    """
    
    def __init__(self, name, knight_class, x, y):
        self.name = name
        self.knight_class = knight_class
        self.x = x
        self.y = y
        
        # Basic properties needed for compatibility
        self.player_id = None
        self.selected = False
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False
        self.is_garrisoned = False
        self.garrison_location = None
        
        # Combat state
        self.in_enemy_zoc = False
        self.is_routing = False
        self.engaged_with = None
        self.is_engaged_in_combat = False
        
        # Set default values based on class
        self._init_class_defaults()
        
    def _init_class_defaults(self):
        """Initialize class-specific defaults"""
        # Action points
        ap_by_class = {
            KnightClass.WARRIOR: 8,
            KnightClass.ARCHER: 7,
            KnightClass.CAVALRY: 10,
            KnightClass.MAGE: 6
        }
        self.max_action_points = ap_by_class.get(self.knight_class, 7)
        self.action_points = self.max_action_points
        
        # Unit composition
        soldiers_by_class = {
            KnightClass.WARRIOR: 100,
            KnightClass.ARCHER: 80,
            KnightClass.CAVALRY: 50,
            KnightClass.MAGE: 30
        }
        self.max_soldiers = soldiers_by_class.get(self.knight_class, 100)
        self.soldiers = self.max_soldiers
        
        # Combat stats
        self.morale = 100
        self.will = 100
        self.max_will = 100
        
        # Movement range
        range_by_class = {
            KnightClass.WARRIOR: 3,
            KnightClass.ARCHER: 4,
            KnightClass.CAVALRY: 6,
            KnightClass.MAGE: 3
        }
        self.movement_range = range_by_class.get(self.knight_class, 3)
        
        # Other combat properties
        attack_by_class = {
            KnightClass.WARRIOR: 1.0,
            KnightClass.ARCHER: 1.5,
            KnightClass.CAVALRY: 2.0,
            KnightClass.MAGE: 3.0
        }
        self.base_attack_per_soldier = attack_by_class.get(self.knight_class, 1.0)
        
        defense_by_class = {
            KnightClass.WARRIOR: 15,
            KnightClass.ARCHER: 5,
            KnightClass.CAVALRY: 10,
            KnightClass.MAGE: 5
        }
        self.base_defense = defense_by_class.get(self.knight_class, 10)
        
        width_by_class = {
            KnightClass.WARRIOR: 20,
            KnightClass.ARCHER: 30,
            KnightClass.CAVALRY: 15,
            KnightClass.MAGE: 10
        }
        self.formation_width = width_by_class.get(self.knight_class, 20)
        
    @property
    def health(self):
        """Compatibility property for health"""
        return self.soldiers
        
    @property
    def max_health(self):
        """Compatibility property for max health"""
        return self.max_soldiers
        
    @property
    def defense(self):
        """Defense value with morale modifier"""
        return self.base_defense * (self.morale / 100)
        
    def has_zone_of_control(self):
        """Check if unit exerts Zone of Control"""
        # Match the logic from Unit class
        strength_percent = self.soldiers / self.max_soldiers
        return strength_percent >= 0.6 and not self.is_routing and not self.is_garrisoned
        
    def is_in_enemy_zoc(self, game_state):
        """Check if this unit is in enemy Zone of Control"""
        hex_grid = HexGrid()
        my_hex = hex_grid.offset_to_axial(self.x, self.y)
        
        for knight in game_state.knights:
            if knight.player_id != self.player_id and knight.has_zone_of_control():
                enemy_hex = hex_grid.offset_to_axial(knight.x, knight.y)
                if my_hex.distance_to(enemy_hex) == 1:  # Adjacent in hex grid
                    return True, knight
        return False, None
        
    def can_disengage_from_zoc(self):
        """Check if unit can break from Zone of Control"""
        # Only cavalry can disengage, and only if not routing
        return self.knight_class == KnightClass.CAVALRY and not self.is_routing
        
    def take_casualties(self, casualties):
        """Apply casualties to the unit"""
        self.soldiers = max(0, self.soldiers - casualties)
        
        # Morale loss based on casualties
        casualty_percent = casualties / self.max_soldiers
        self.morale = max(0, self.morale - casualty_percent * 20)
        
        return self.soldiers <= 0  # Return True if unit is destroyed
        
    def end_turn(self):
        """Reset for new turn"""
        self.action_points = self.max_action_points
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False
        # Regenerate some will each turn
        self.will = min(self.max_will, self.will + 20)
        
    # Minimal method stubs for compatibility
    # These should NOT be used in production code - use Unit with behaviors instead
    
    def can_move(self):
        """Check if unit can move - LEGACY: Use Unit with MovementBehavior"""
        if self.action_points < 1 or self.has_moved:
            return False
        if self.is_routing:
            return True
        if self.in_enemy_zoc and not self.can_disengage_from_zoc():
            return False
        return True
        
    def can_attack(self):
        """Check if unit can attack - LEGACY: Use Unit with AttackBehavior"""
        ap_needed = {
            KnightClass.WARRIOR: 4,
            KnightClass.ARCHER: 2,
            KnightClass.CAVALRY: 3,
            KnightClass.MAGE: 2
        }.get(self.knight_class, 3)
        
        return self.action_points >= ap_needed and not self.has_acted
        
    def move(self, new_x, new_y):
        """Move unit - LEGACY: Use Unit with MovementBehavior"""
        self.x = new_x
        self.y = new_y
        self.has_moved = True
        
    def consume_move_ap(self):
        """Consume AP for movement - LEGACY: Use Unit with MovementBehavior"""
        self.action_points -= 1
        self.has_moved = True
        
    def consume_attack_ap(self):
        """Consume AP for attack - LEGACY: Use Unit with AttackBehavior"""
        ap_cost = {
            KnightClass.WARRIOR: 4,
            KnightClass.ARCHER: 2,
            KnightClass.CAVALRY: 3,
            KnightClass.MAGE: 2
        }.get(self.knight_class, 3)
        
        self.action_points -= ap_cost
        self.has_acted = True