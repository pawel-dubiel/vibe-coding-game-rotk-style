"""Test archer attack functionality"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.test_utils.mock_game_state import MockGameState

class TestArcherAttack:
    """Test archer attack behavior"""
    
    def setup_method(self):
        """Set up test environment"""
        self.game_state = MockGameState(board_width=20, board_height=20)
        
    def test_archer_can_attack(self):
        """Test that archers can attack"""
        # Create archer
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        archer.player_id = 1
        self.game_state.add_knight(archer)
        
        # Verify archer has attack behavior
        assert 'attack' in archer.behaviors
        assert archer.can_attack()
        
    def test_archer_attack_range(self):
        """Test archer has 3 range"""
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        archer.player_id = 1
        self.game_state.add_knight(archer)
        
        # Check attack behavior range
        attack_behavior = archer.behaviors['attack']
        assert attack_behavior.attack_range == 3
        
    def test_archer_can_attack_at_range(self):
        """Test archer can attack targets at range"""
        # Create archer and enemy
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        archer.player_id = 1
        enemy = UnitFactory.create_warrior("Enemy Warrior", 13, 10)
        enemy.player_id = 2
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(enemy)
        
        # Check can get valid targets at range 3
        attack_behavior = archer.behaviors['attack']
        valid_targets = attack_behavior.get_valid_targets(archer, self.game_state)
        
        assert enemy in valid_targets
        
    def test_archer_cannot_attack_beyond_range(self):
        """Test archer cannot attack beyond range 3"""
        # Create archer and enemy
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        archer.player_id = 1
        enemy = UnitFactory.create_warrior("Enemy Warrior", 14, 10)  # 4 tiles away
        enemy.player_id = 2
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(enemy)
        
        # Check cannot target beyond range
        attack_behavior = archer.behaviors['attack']
        valid_targets = attack_behavior.get_valid_targets(archer, self.game_state)
        
        assert enemy not in valid_targets
        
    def test_archer_attack_execution(self):
        """Test archer can execute attacks"""
        # Create archer and enemy
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        archer.player_id = 1
        enemy = UnitFactory.create_warrior("Enemy Warrior", 12, 10)
        enemy.player_id = 2
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(enemy)
        
        # Execute attack
        attack_behavior = archer.behaviors['attack']
        initial_enemy_soldiers = enemy.soldiers
        
        result = attack_behavior.execute(archer, self.game_state, enemy)
        
        assert result['success'] == True
        assert result['damage'] > 0
        assert archer.has_acted == True
        assert archer.action_points < archer.max_action_points
        
    def test_archer_attack_ap_cost(self):
        """Test archer attacks cost 2 AP"""
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        attack_behavior = archer.behaviors['attack']
        
        assert attack_behavior.get_ap_cost(archer) == 2
        
    def test_archer_no_counter_damage_in_melee(self):
        """Test archers don't counter-attack in melee"""
        # Create warrior and archer
        warrior = UnitFactory.create_warrior("Test Warrior", 10, 10)
        warrior.player_id = 1
        archer = UnitFactory.create_archer("Enemy Archer", 11, 10)
        archer.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(archer)
        
        # Warrior attacks archer
        attack_behavior = warrior.behaviors['attack']
        result = attack_behavior.execute(warrior, self.game_state, archer)
        
        assert result['success'] == True
        assert result['counter_damage'] == 0  # Archer should not counter
        
    def test_archer_attack_with_diagonal_range(self):
        """Test archer can attack diagonally at range 3"""
        # Create archer and enemy
        archer = UnitFactory.create_archer("Test Archer", 10, 10)
        archer.player_id = 1
        # Enemy at (12, 12) is 2 diagonal steps away (Chebyshev distance = 2)
        enemy = UnitFactory.create_warrior("Enemy Warrior", 12, 12)
        enemy.player_id = 2
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(enemy)
        
        attack_behavior = archer.behaviors['attack']
        valid_targets = attack_behavior.get_valid_targets(archer, self.game_state)
        
        assert enemy in valid_targets
        
        # Enemy at (13, 13) is 3 diagonal steps away (Chebyshev distance = 3)
        enemy2 = UnitFactory.create_warrior("Enemy Warrior 2", 13, 13)
        enemy2.player_id = 2
        self.game_state.add_knight(enemy2)
        
        valid_targets = attack_behavior.get_valid_targets(archer, self.game_state)
        assert enemy2 in valid_targets
        
        # Enemy at (14, 14) is 4 diagonal steps away (Chebyshev distance = 4) - out of range
        enemy3 = UnitFactory.create_warrior("Enemy Warrior 3", 14, 14)
        enemy3.player_id = 2
        self.game_state.add_knight(enemy3)
        
        valid_targets = attack_behavior.get_valid_targets(archer, self.game_state)
        assert enemy3 not in valid_targets
        
    def test_multiple_unit_types_attack_behavior(self):
        """Test that all unit types have appropriate attack behaviors"""
        # Test each unit type
        units = [
            (UnitFactory.create_warrior("Warrior", 0, 0), 1, 4),  # range 1, cost 4
            (UnitFactory.create_archer("Archer", 0, 0), 3, 2),    # range 3, cost 2
            (UnitFactory.create_cavalry("Cavalry", 0, 0), 1, 3),  # range 1, cost 3
            (UnitFactory.create_mage("Mage", 0, 0), 2, 2),        # range 2, cost 2
        ]
        
        for unit, expected_range, expected_cost in units:
            assert 'attack' in unit.behaviors
            assert unit.can_attack()
            attack_behavior = unit.behaviors['attack']
            assert attack_behavior.attack_range == expected_range
            assert attack_behavior.get_ap_cost(unit) == expected_cost

if __name__ == "__main__":
    # Run tests manually
    test = TestArcherAttack()
    
    print("Running archer attack tests...")
    
    # Test 1
    test.setup_method()
    test.test_archer_can_attack()
    print("✓ test_archer_can_attack passed")
    
    # Test 2
    test.setup_method()
    test.test_archer_attack_range()
    print("✓ test_archer_attack_range passed")
    
    # Test 3
    test.setup_method()
    test.test_archer_can_attack_at_range()
    print("✓ test_archer_can_attack_at_range passed")
    
    # Test 4
    test.setup_method()
    test.test_archer_cannot_attack_beyond_range()
    print("✓ test_archer_cannot_attack_beyond_range passed")
    
    # Test 5
    test.setup_method()
    test.test_archer_attack_execution()
    print("✓ test_archer_attack_execution passed")
    
    # Test 6
    test.setup_method()
    test.test_archer_attack_ap_cost()
    print("✓ test_archer_attack_ap_cost passed")
    
    # Test 7
    test.setup_method()
    test.test_archer_no_counter_damage_in_melee()
    print("✓ test_archer_no_counter_damage_in_melee passed")
    
    # Test 8
    test.setup_method()
    test.test_archer_attack_with_diagonal_range()
    print("✓ test_archer_attack_with_diagonal_range passed")
    
    # Test 9
    test.setup_method()
    test.test_multiple_unit_types_attack_behavior()
    print("✓ test_multiple_unit_types_attack_behavior passed")
    
    print("\nAll tests passed!")