"""Test enhanced attack system with terrain costs, morale requirements, and progressive morale loss"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.test_utils.mock_game_state import MockGameState
from game.combat_config import CombatConfig
from game.terrain import TerrainType

class TestEnhancedAttackSystem:
    """Test the enhanced attack system with all new features"""
    
    def setup_method(self):
        """Set up test environment"""
        self.game_state = MockGameState(board_width=10, board_height=10)
        
    def test_terrain_based_attack_costs_double_movement(self):
        """Test that attack costs are twice the terrain movement cost"""
        terrain_tests = [
            (TerrainType.PLAINS, 1.0, 4),      # 1.0x movement → 4 base AP (no penalty)
            (TerrainType.HILLS, 2.0, 6),       # 2.0x movement → 4 + 2 penalty = 6 AP
            (TerrainType.FOREST, 2.0, 6),      # 2.0x movement → 4 + 2 penalty = 6 AP  
            (TerrainType.DENSE_FOREST, 3.0, 8), # 3.0x movement → 4 + 4 penalty = 8 AP
            (TerrainType.SWAMP, 3.0, 8),       # 3.0x movement → 4 + 4 penalty = 8 AP
        ]
        
        for terrain_type, movement_cost, expected_ap in terrain_tests:
            # Set terrain
            self.game_state.terrain_map.set_terrain(5, 5, terrain_type)
            
            # Create units
            self.game_state.knights.clear()
            warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)  # Adjacent
            warrior.player_id = 1
            target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
            target.player_id = 2
            
            self.game_state.add_knight(warrior)
            self.game_state.add_knight(target)
            self.game_state.current_player = 1
            
            # Test AP cost
            attack_behavior = warrior.behaviors['attack']
            ap_cost = attack_behavior.get_ap_cost(warrior, target, self.game_state)
            
            assert ap_cost == expected_ap, f"{terrain_type.value}: Expected {expected_ap} AP, got {ap_cost}"
            
    def test_ranged_attacks_reduced_terrain_penalty(self):
        """Test that ranged attacks have reduced terrain penalties"""
        # Set difficult terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.DENSE_FOREST)
        
        # Create archer and target
        self.game_state.knights.clear()
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 3, 5)
        archer.player_id = 1
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        target.stats.stats.attack_per_soldier = 0  # Prevent counter-damage routing randomness
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(target)
        
        # Test ranged attack cost (should be 2 base + 2 terrain = 4 AP instead of 2 + 4 = 6)
        attack_behavior = archer.behaviors['attack']
        ap_cost = attack_behavior.get_ap_cost(archer, target, self.game_state)
        
        assert ap_cost == 4, f"Ranged dense forest attack should cost 4 AP (2 base + 2 terrain), got {ap_cost}"
        
    def test_first_attack_no_morale_requirement(self):
        """Test that first attack has no morale requirement"""
        # Set plains terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
        
        # Create warrior with low morale
        self.game_state.knights.clear()
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
        warrior.player_id = 1
        warrior.morale = 30  # Below 50%
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        target.stats.stats.attack_per_soldier = 0  # Prevent counter-damage routing randomness
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        # First attack should be allowed despite low morale
        attack_behavior = warrior.behaviors['attack']
        can_attack = attack_behavior.can_execute(warrior, self.game_state)
        
        assert can_attack, "First attack should be allowed even with low morale"
        
    def test_second_attack_requires_50_percent_morale(self):
        """Test that second attack requires morale and cohesion thresholds"""
        # Set plains terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
        
        # Create warrior with high AP and moderate morale
        self.game_state.knights.clear()
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
        warrior.player_id = 1
        warrior.action_points = 20  # Plenty of AP
        warrior.morale = CombatConfig.MORALE_ATTACK_THRESHOLD + 10
        warrior.cohesion = CombatConfig.COHESION_ATTACK_THRESHOLD + 10
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        # Execute first attack
        attack_behavior = warrior.behaviors['attack']
        result = attack_behavior.execute(warrior, self.game_state, target)
        assert result['success'], "First attack should succeed"
        
        # Check second attack is allowed with good morale
        can_attack_again = attack_behavior.can_execute(warrior, self.game_state)
        assert can_attack_again, "Second attack should be allowed with good morale/cohesion"
        
        # Reduce morale below threshold
        warrior.morale = CombatConfig.MORALE_ATTACK_THRESHOLD - 10
        
        # Check second attack is now blocked
        can_attack_low_morale = attack_behavior.can_execute(warrior, self.game_state)
        assert not can_attack_low_morale, "Second attack should be blocked with low morale"
        
    def test_progressive_morale_loss_multiple_attacks(self):
        """Test that multiple attacks cause progressive morale/cohesion loss"""
        # Set plains terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
        
        # Create archer with high AP and high morale (ranged to avoid counter damage)
        self.game_state.knights.clear()
        warrior = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 4, 5)
        warrior.player_id = 1
        warrior.action_points = 20  # Plenty of AP for multiple attacks
        warrior.morale = 100  # High morale
        warrior.cohesion = warrior.max_cohesion
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 6, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        initial_morale = warrior.morale
        attack_behavior = warrior.behaviors['attack']
        
        # First attack - no morale loss from multiple attacks
        result1 = attack_behavior.execute(warrior, self.game_state, target)
        assert result1['success'], "First attack should succeed"
        assert warrior.morale == initial_morale, "First attack should not cause morale loss"
        assert warrior.attacks_this_turn == 1, "Should track first attack"
        
        # Second attack - should cause fatigue-based morale/cohesion loss
        # Note: Check base morale since displayed morale includes general bonuses
        target.is_routing = False
        target.morale = target.stats.stats.max_morale
        target.cohesion = target.max_cohesion
        target.x = 6
        target.y = 5
        base_morale_before_second = warrior.stats.stats.morale
        base_cohesion_before_second = warrior.stats.stats.current_cohesion
        result2 = attack_behavior.execute(warrior, self.game_state, target)
        assert result2['success'], "Second attack should succeed"
        base_morale_after_second = warrior.stats.stats.morale
        base_cohesion_after_second = warrior.stats.stats.current_cohesion
        morale_loss_second = base_morale_before_second - base_morale_after_second
        expected_morale_loss = CombatConfig.ATTACK_FATIGUE_MORALE_PER_ATTACK
        expected_cohesion_loss = CombatConfig.ATTACK_FATIGUE_COHESION_PER_ATTACK
        assert morale_loss_second == expected_morale_loss, f"Second attack should cause {expected_morale_loss} base morale loss, got {morale_loss_second}"
        cohesion_loss_second = base_cohesion_before_second - base_cohesion_after_second
        assert cohesion_loss_second == expected_cohesion_loss, f"Second attack should cause {expected_cohesion_loss} cohesion loss, got {cohesion_loss_second}"
        assert warrior.attacks_this_turn == 2, "Should track second attack"
        
        # Third attack - should cause additional fatigue loss
        if warrior.action_points >= 4:  # If enough AP for third attack
            target.is_routing = False
            target.morale = target.stats.stats.max_morale
            target.cohesion = target.max_cohesion
            target.x = 6
            target.y = 5
            base_morale_before_third = warrior.stats.stats.morale
            base_cohesion_before_third = warrior.stats.stats.current_cohesion
            result3 = attack_behavior.execute(warrior, self.game_state, target)
            assert result3['success'], "Third attack should succeed"
            base_morale_after_third = warrior.stats.stats.morale
            base_cohesion_after_third = warrior.stats.stats.current_cohesion
            morale_loss_third = base_morale_before_third - base_morale_after_third
            expected_morale_loss_third = CombatConfig.ATTACK_FATIGUE_MORALE_PER_ATTACK * 2
            expected_cohesion_loss_third = CombatConfig.ATTACK_FATIGUE_COHESION_PER_ATTACK * 2
            assert morale_loss_third == expected_morale_loss_third, f"Third attack should cause {expected_morale_loss_third} base morale loss, got {morale_loss_third}"
            cohesion_loss_third = base_cohesion_before_third - base_cohesion_after_third
            assert cohesion_loss_third == expected_cohesion_loss_third, f"Third attack should cause {expected_cohesion_loss_third} cohesion loss, got {cohesion_loss_third}"
            assert warrior.attacks_this_turn == 3, "Should track third attack"
            
    def test_attack_counter_resets_each_turn(self):
        """Test that attack counter resets at the end of each turn"""
        # Create warrior
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
        warrior.attacks_this_turn = 5  # Simulate multiple attacks
        
        # End turn should reset counter
        warrior.end_turn()
        
        assert warrior.attacks_this_turn == 0, "Attack counter should reset to 0 after end_turn()"
        
    def test_multiple_attacks_consume_correct_ap(self):
        """Test that multiple attacks consume the correct AP each time"""
        # Set hills terrain for +2 AP penalty
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        
        # Create warrior with plenty of AP
        self.game_state.knights.clear()
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
        warrior.player_id = 1
        warrior.action_points = 20  # Plenty of AP
        warrior.morale = 100  # High morale
        warrior.cohesion = warrior.max_cohesion
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        initial_ap = warrior.action_points
        attack_behavior = warrior.behaviors['attack']
        
        # First attack should cost 6 AP (4 base + 2 hills)
        result1 = attack_behavior.execute(warrior, self.game_state, target)
        assert result1['success'], "First attack should succeed"
        ap_after_first = warrior.action_points
        assert initial_ap - ap_after_first == 6, f"First attack should cost 6 AP, consumed {initial_ap - ap_after_first}"
        
        # Second attack should also cost 6 AP
        warrior.morale = 100
        warrior.cohesion = warrior.max_cohesion
        target.is_routing = False
        target.x = 5
        target.y = 5
        result2 = attack_behavior.execute(warrior, self.game_state, target)
        assert result2['success'], "Second attack should succeed"
        ap_after_second = warrior.action_points
        assert ap_after_first - ap_after_second == 6, f"Second attack should cost 6 AP, consumed {ap_after_first - ap_after_second}"
        
    def test_insufficient_ap_prevents_attack(self):
        """Test that insufficient AP prevents attacks"""
        # Set expensive terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.DENSE_FOREST)
        
        # Create warrior with low AP
        self.game_state.knights.clear()
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
        warrior.player_id = 1
        warrior.action_points = 3  # Less than 8 AP needed for dense forest attack
        warrior.morale = 100
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        # Attack should be blocked due to insufficient AP
        attack_behavior = warrior.behaviors['attack']
        can_attack = attack_behavior.can_execute(warrior, self.game_state)
        
        assert not can_attack, "Attack should be blocked when AP < terrain cost (3 < 8)"
        
    def test_different_unit_types_terrain_costs(self):
        """Test that different unit types have correct terrain-based costs"""
        # Set hills terrain (+2 penalty)
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        
        unit_tests = [
            (KnightClass.WARRIOR, 6),  # 4 base + 2 terrain
            (KnightClass.CAVALRY, 5),  # 3 base + 2 terrain
            (KnightClass.MAGE, 4),     # 2 base + 2 terrain
            (KnightClass.ARCHER, 3),   # 2 base + 1 terrain (reduced for ranged)
        ]
        
        for unit_class, expected_cost in unit_tests:
            # Create unit and target
            self.game_state.knights.clear()
            unit = UnitFactory.create_unit("Attacker", unit_class, 4, 5)
            unit.player_id = 1
            target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
            target.player_id = 2
            
            self.game_state.add_knight(unit)
            self.game_state.add_knight(target)
            
            # Test AP cost
            attack_behavior = unit.behaviors['attack']
            ap_cost = attack_behavior.get_ap_cost(unit, target, self.game_state)
            
            assert ap_cost == expected_cost, f"{unit_class.value} on hills should cost {expected_cost} AP, got {ap_cost}"
            
    def test_combat_execution_integration(self):
        """Test full combat execution with all new features"""
        # Set moderate terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.FOREST)
        
        # Create warrior with good stats
        self.game_state.knights.clear()
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
        warrior.player_id = 1
        warrior.action_points = 15  # Enough for multiple attacks
        warrior.morale = 80  # Good morale
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        attack_behavior = warrior.behaviors['attack']
        
        # First attack
        initial_ap = warrior.action_points
        initial_morale = warrior.morale
        
        result1 = attack_behavior.execute(warrior, self.game_state, target)
        assert result1['success'], "First attack should succeed"
        assert warrior.action_points == initial_ap - 6, "Should consume 6 AP (4 base + 2 forest)"
        assert warrior.morale <= initial_morale, "First attack should not increase morale"
        assert warrior.attacks_this_turn == 1, "Should track first attack"
        
        # Second attack (if target still alive and warrior has enough AP/morale)
        if target.soldiers > 0 and warrior.action_points >= 6 and warrior.morale >= 50:
            ap_before_second = warrior.action_points
            warrior.morale = max(warrior.morale, CombatConfig.MORALE_ATTACK_THRESHOLD + 5)
            warrior.cohesion = max(warrior.cohesion, CombatConfig.COHESION_ATTACK_THRESHOLD + 5)
            target.is_routing = False
            target.x = 5
            target.y = 5
            base_morale_before_second = warrior.stats.stats.morale
            result2 = attack_behavior.execute(warrior, self.game_state, target)
            assert result2['success'], "Second attack should succeed"
            assert warrior.action_points == ap_before_second - 6, "Should consume 6 AP again"
            base_morale_after_second = warrior.stats.stats.morale
            morale_loss = base_morale_before_second - base_morale_after_second
            expected_loss = CombatConfig.ATTACK_FATIGUE_MORALE_PER_ATTACK
            assert morale_loss >= expected_loss, f"Second attack should reduce base morale by at least {expected_loss}, got {morale_loss}"
            assert warrior.attacks_this_turn == 2, "Should track second attack"

if __name__ == "__main__":
    # Run the tests
    test_class = TestEnhancedAttackSystem()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    print("Running enhanced attack system tests...")
    for method_name in test_methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✅ {method_name} - PASSED")
        except Exception as e:
            print(f"❌ {method_name} - FAILED: {e}")
    
    print("Tests completed!")
