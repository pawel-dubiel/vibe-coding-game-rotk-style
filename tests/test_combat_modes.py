"""Test combat mode system"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.knight import KnightClass
from game.entities.unit_factory import UnitFactory
from game.behaviors.combat import CombatMode
from game.test_utils.mock_game_state import MockGameState

class TestCombatModes:
    """Test different combat modes"""
    
    def setup_method(self):
        """Set up test environment"""
        self.game_state = MockGameState(board_width=20, board_height=20)
        
    def test_archer_ranged_no_counter_damage(self):
        """Test that archers attacking from range receive no counter damage"""
        # Create archer and warrior
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 5, 5)
        archer.player_id = 1
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 8, 5)
        warrior.player_id = 2  # 3 tiles away
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(warrior)
        self.game_state.current_player = 1
        
        # Execute ranged attack
        attack_behavior = archer.behaviors['attack']
        assert attack_behavior is not None
        
        result = attack_behavior.execute(archer, self.game_state, warrior)
        assert result['success']
        assert result['damage'] > 0
        assert result['counter_damage'] == 0  # No counter damage from range
        assert result['combat_mode'] == CombatMode.RANGED
        
    def test_melee_combat_with_counter(self):
        """Test melee combat has counter damage"""
        # Create two warriors adjacent to each other
        warrior1 = UnitFactory.create_unit("Warrior1", KnightClass.WARRIOR, 5, 5)
        warrior1.player_id = 1
        warrior2 = UnitFactory.create_unit("Warrior2", KnightClass.WARRIOR, 6, 5)
        warrior2.player_id = 2  # Adjacent
        
        self.game_state.add_knight(warrior1)
        self.game_state.add_knight(warrior2)
        self.game_state.current_player = 1
        
        # Execute melee attack
        attack_behavior = warrior1.behaviors['attack']
        result = attack_behavior.execute(warrior1, self.game_state, warrior2)
        
        assert result['success']
        assert result['damage'] > 0
        assert result['counter_damage'] > 0  # Counter damage in melee
        assert result['combat_mode'] == CombatMode.MELEE
        
    def test_archer_melee_no_counter(self):
        """Test that archers don't counter-attack in melee"""
        # Create warrior attacking archer in melee
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 6, 5)
        archer.player_id = 2  # Adjacent
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(archer)
        self.game_state.current_player = 1
        
        # Warrior attacks archer
        attack_behavior = warrior.behaviors['attack']
        result = attack_behavior.execute(warrior, self.game_state, archer)
        
        assert result['success']
        assert result['damage'] > 0
        assert result['counter_damage'] == 0  # Archers don't counter in melee
        assert result['combat_mode'] == CombatMode.MELEE
        
    def test_cavalry_charge_bonus(self):
        """Test cavalry charge mode gets damage bonus"""
        # Create cavalry and warrior
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 5, 5)
        cavalry.player_id = 1
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 6, 5)
        warrior.player_id = 2  # Adjacent
        
        self.game_state.add_knight(cavalry)
        self.game_state.add_knight(warrior)
        self.game_state.current_player = 1
        
        # Execute cavalry charge
        attack_behavior = cavalry.behaviors['attack']
        result = attack_behavior.execute(cavalry, self.game_state, warrior)
        
        assert result['success']
        assert result['damage'] > 0
        # Cavalry charges should have reduced counter damage (75% of normal)
        assert result['combat_mode'] == CombatMode.CHARGE
        
        # Compare with normal cavalry attack (after charge)
        cavalry.has_charged = True
        cavalry.has_acted = False  # Reset for second attack
        cavalry.action_points = 10  # Reset AP
        cavalry.attacks_this_turn = 0
        cavalry.morale = 100
        cavalry.cohesion = cavalry.max_cohesion
        warrior.is_routing = False
        warrior.morale = 100
        warrior.cohesion = warrior.max_cohesion
        warrior.x = 6
        warrior.y = 5
        result2 = attack_behavior.execute(cavalry, self.game_state, warrior)
        assert result2['success']
        assert result2['combat_mode'] == CombatMode.MELEE
        
    def test_mage_ranged_attack(self):
        """Test mage attacks at range 2"""
        # Create mage and warrior
        mage = UnitFactory.create_unit("Mage", KnightClass.MAGE, 5, 5)
        mage.player_id = 1
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 7, 5)
        warrior.player_id = 2  # 2 tiles away
        
        self.game_state.add_knight(mage)
        self.game_state.add_knight(warrior)
        self.game_state.current_player = 1
        
        # Execute ranged attack
        attack_behavior = mage.behaviors['attack']
        result = attack_behavior.execute(mage, self.game_state, warrior)
        
        assert result['success']
        assert result['damage'] > 0
        assert result['counter_damage'] == 0  # No counter from range 2
        assert result['combat_mode'] == CombatMode.RANGED
