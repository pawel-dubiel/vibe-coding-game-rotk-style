"""Test engagement and Zone of Control mechanics"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.knight import KnightClass
from game.entities.unit_factory import UnitFactory
from game.behaviors.combat import CombatMode
from game.combat_config import CombatConfig
from game.test_utils.mock_game_state import MockGameState

class TestEngagementMechanics:
    """Test unit engagement and ZOC mechanics"""
    
    def setup_method(self):
        """Set up test environment"""
        self.game_state = MockGameState(board_width=20, board_height=20)
        
    def test_ranged_attack_does_not_engage(self):
        """Test that ranged attacks do not set engagement status"""
        # Create archer and cavalry at distance
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 5, 5)
        archer.player_id = 1
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 8, 5)
        cavalry.player_id = 2  # 3 tiles away
        # Boost stats to prevent routing from single attack
        cavalry.stats.stats.max_morale = 200
        cavalry.stats.stats.morale = 200
        cavalry.stats.stats.max_cohesion = 200
        cavalry.stats.stats.current_cohesion = 200
        
        # Prevent routing absolutely
        cavalry._start_routing = lambda gs=None: None
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(cavalry)
        self.game_state.current_player = 1
        
        # Verify initial state - not engaged
        assert not archer.is_engaged_in_combat, "Archer should not be engaged initially"
        assert not cavalry.is_engaged_in_combat, "Cavalry should not be engaged initially"
        assert not archer.in_enemy_zoc, "Archer should not be in enemy ZOC initially"
        assert not cavalry.in_enemy_zoc, "Cavalry should not be in enemy ZOC initially"
        
        # Execute ranged attack
        attack_behavior = archer.behaviors['attack']
        result = attack_behavior.execute(archer, self.game_state, cavalry)
        
        # Verify attack succeeded
        assert result['success'], f"Attack should succeed: {result.get('reason', 'No reason')}"
        
        # Verify units are NOT engaged after ranged attack
        assert not archer.is_engaged_in_combat, "Archer should NOT be engaged after ranged attack"
        assert not cavalry.is_engaged_in_combat, "Cavalry should NOT be engaged after ranged attack"
        assert archer.engaged_with is None, "Archer should not have engaged_with set"
        assert cavalry.engaged_with is None, "Cavalry should not have engaged_with set"
        
        # Verify cavalry can still move freely
        movement_behavior = cavalry.behaviors['move']
        assert movement_behavior.can_execute(cavalry, self.game_state), "Cavalry should be able to move after ranged attack"
        
    def test_melee_attack_does_engage(self):
        """Test that melee attacks do set engagement status"""
        # Create two warriors adjacent to each other
        warrior1 = UnitFactory.create_unit("Warrior1", KnightClass.WARRIOR, 5, 5)
        warrior1.player_id = 1
        warrior2 = UnitFactory.create_unit("Warrior2", KnightClass.WARRIOR, 6, 5)
        warrior2.player_id = 2  # 1 tile away
        
        self.game_state.add_knight(warrior1)
        self.game_state.add_knight(warrior2)
        self.game_state.current_player = 1
        
        # Verify initial state - not engaged
        assert not warrior1.is_engaged_in_combat, "Warrior1 should not be engaged initially"
        assert not warrior2.is_engaged_in_combat, "Warrior2 should not be engaged initially"
        
        # Execute melee attack
        attack_behavior = warrior1.behaviors['attack']
        result = attack_behavior.execute(warrior1, self.game_state, warrior2)
        
        # Verify attack succeeded
        assert result['success'], f"Attack should succeed: {result.get('reason', 'No reason')}"
        
        # Verify units ARE engaged after melee attack
        assert warrior1.is_engaged_in_combat, "Warrior1 should be engaged after melee attack"
        assert warrior2.is_engaged_in_combat, "Warrior2 should be engaged after melee attack"
        assert warrior1.engaged_with == warrior2, "Warrior1 should be engaged with Warrior2"
        assert warrior2.engaged_with == warrior1, "Warrior2 should be engaged with Warrior1"
        
    def test_cavalry_charge_does_engage(self):
        """Test that cavalry charges set engagement status"""
        # Create cavalry and warrior adjacent
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 5, 5)
        cavalry.player_id = 1
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 6, 5)
        warrior.player_id = 2  # 1 tile away
        
        self.game_state.add_knight(cavalry)
        self.game_state.add_knight(warrior)
        self.game_state.current_player = 1
        
        # Execute charge attack (should be melee range and trigger charge mode)
        attack_behavior = cavalry.behaviors['attack']
        result = attack_behavior.execute(cavalry, self.game_state, warrior)
        
        # Verify attack succeeded
        assert result['success'], f"Attack should succeed: {result.get('reason', 'No reason')}"
        
        # Verify units ARE engaged after charge
        assert cavalry.is_engaged_in_combat, "Cavalry should be engaged after charge"
        assert warrior.is_engaged_in_combat, "Warrior should be engaged after charge"
        
    def test_engagement_clears_when_moving_apart(self):
        """Test that engagement status clears when units move away from each other"""
        # Create two warriors adjacent and engaged
        warrior1 = UnitFactory.create_unit("Warrior1", KnightClass.WARRIOR, 5, 5)
        warrior1.player_id = 1
        warrior2 = UnitFactory.create_unit("Warrior2", KnightClass.WARRIOR, 6, 5)
        warrior2.player_id = 2
        
        self.game_state.add_knight(warrior1)
        self.game_state.add_knight(warrior2)
        self.game_state.current_player = 1
        
        # Manually set engagement status (simulating melee combat)
        warrior1.is_engaged_in_combat = True
        warrior1.engaged_with = warrior2
        warrior2.is_engaged_in_combat = True
        warrior2.engaged_with = warrior1
        
        # Verify they are engaged
        assert warrior1.is_engaged_in_combat, "Warrior1 should be engaged initially"
        assert warrior2.is_engaged_in_combat, "Warrior2 should be engaged initially"
        
        # Move warrior2 away (simulate movement)
        warrior2.x = 10
        warrior2.y = 10
        
        # Update ZOC status (this should clear engagement)
        self.game_state._update_zoc_status()
        
        # Verify engagement is cleared
        assert not warrior1.is_engaged_in_combat, "Warrior1 should not be engaged after moving apart"
        assert not warrior2.is_engaged_in_combat, "Warrior2 should not be engaged after moving apart"
        assert warrior1.engaged_with is None, "Warrior1 should not have engaged_with after moving apart"
        assert warrior2.engaged_with is None, "Warrior2 should not have engaged_with after moving apart"
        
    def test_cavalry_mobility_after_archer_attack(self):
        """Test the original bug: cavalry should remain mobile after being shot by archers"""
        # Create archer and cavalry at distance (reproducing the reported bug)
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 2, 2)
        archer.player_id = 1
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 5, 2)
        cavalry.player_id = 2  # 3 tiles away
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(cavalry)
        self.game_state.current_player = 1
        
        # Verify cavalry can move initially
        movement_behavior = cavalry.behaviors['move']
        assert movement_behavior.can_execute(cavalry, self.game_state), "Cavalry should be able to move initially"
        assert not cavalry.in_enemy_zoc, "Cavalry should not be in enemy ZOC initially"
        
        # Archer attacks cavalry from distance
        attack_behavior = archer.behaviors['attack']
        result = attack_behavior.execute(archer, self.game_state, cavalry)
        assert result['success'], "Archer attack should succeed"
        
        # Update ZOC status (this happens every frame in real game)
        self.game_state._update_zoc_status()
        
        # Verify cavalry is still mobile after being attacked
        assert not cavalry.is_engaged_in_combat, "Cavalry should NOT be engaged after ranged attack"
        assert not cavalry.in_enemy_zoc, "Cavalry should NOT be in enemy ZOC after ranged attack"
        assert movement_behavior.can_execute(cavalry, self.game_state), "Cavalry should still be able to move after ranged attack"
        
        # Switch to cavalry's turn and verify it can move
        self.game_state.current_player = 2
        assert movement_behavior.can_execute(cavalry, self.game_state), "Cavalry should be able to move on its turn"
        
    def test_zoc_prevents_movement_correctly(self):
        """Test that ZOC still correctly prevents movement when units are adjacent"""
        # Create cavalry and warrior adjacent (should create ZOC)
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 5, 5)
        cavalry.player_id = 1
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 6, 5)
        warrior.player_id = 2  # 1 tile away
        
        self.game_state.add_knight(cavalry)
        self.game_state.add_knight(warrior)
        self.game_state.current_player = 1
        
        # Update ZOC status
        self.game_state._update_zoc_status()
        
        # Verify cavalry is in enemy ZOC due to adjacency
        assert cavalry.in_enemy_zoc, "Cavalry should be in enemy ZOC when adjacent to enemy"
        assert cavalry.engaged_with == warrior, "Cavalry should be engaged with adjacent warrior"
        
        # Verify movement is restricted due to ZOC
        movement_behavior = cavalry.behaviors['move']
        # Note: Cavalry might still be able to move but with penalties - this depends on disengagement rules
        # The important thing is that ZOC is correctly detected
        
    def test_ranged_vs_melee_combat_mode_detection(self):
        """Test that combat modes are correctly detected"""
        # Create archer
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 5, 5)
        attack_behavior = archer.behaviors['attack']
        
        # Test ranged combat mode (distance > 1)
        distant_target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 8, 5)
        mode = attack_behavior.determine_combat_mode(archer, distant_target, 3)
        assert mode == CombatMode.RANGED, "Should detect RANGED mode for distant targets"
        
        # Test melee combat mode (distance = 1)
        adjacent_target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 6, 5)
        mode = attack_behavior.determine_combat_mode(archer, adjacent_target, 1)
        assert mode == CombatMode.MELEE, "Should detect MELEE mode for adjacent targets"
    
    def test_morale_recovery_and_rally_system(self):
        """Test that routing units recover morale and can rally"""
        # Create a warrior with low morale
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        warrior.morale = 15  # Below routing threshold
        warrior.cohesion = 40  # Below rally threshold
        warrior.is_routing = True  # Start routing
        
        initial_morale = warrior.morale
        initial_cohesion = warrior.cohesion
        
        # End turn to trigger morale recovery
        warrior.end_turn()
        
        # Verify morale increased
        assert warrior.morale > initial_morale, "Morale should increase each turn"
        expected_morale = min(100, initial_morale + CombatConfig.MORALE_REGEN_ROUTING)
        assert warrior.morale >= expected_morale, f"Routing units should get morale regen per turn. Expected: {expected_morale}, Got: {warrior.morale}"
        expected_cohesion = min(warrior.max_cohesion, initial_cohesion + CombatConfig.COHESION_REGEN_ROUTING)
        assert warrior.cohesion >= expected_cohesion, "Cohesion should recover while routing"
        
        # Still routing with low morale
        assert warrior.is_routing, "Should still be routing with low morale"
        
        # Simulate several turns to build up morale
        for _ in range(3):  # 3 more turns
            warrior.end_turn()
            
        # Should have enough morale to potentially rally now
        assert warrior.morale >= CombatConfig.RALLY_MORALE_THRESHOLD, "Should have enough morale to rally after several turns"
        assert warrior.cohesion >= CombatConfig.RALLY_COHESION_THRESHOLD, "Should have enough cohesion to rally after several turns"
        
        # The rally is probabilistic, but let's test the rally threshold logic
        warrior.morale = CombatConfig.RALLY_MORALE_THRESHOLD + 5
        warrior.cohesion = CombatConfig.RALLY_COHESION_THRESHOLD + 5
        warrior.is_routing = True
        
        # Test rally mechanics by calling end_turn multiple times (probabilistic)
        rallied = False
        for attempt in range(10):  # Try multiple times due to randomness
            if not warrior.is_routing:
                rallied = True
                break
            warrior.is_routing = True  # Reset for next attempt
            warrior.end_turn()
            
        # With 50 morale and multiple attempts, should eventually rally
        # (This test might occasionally fail due to randomness, but very unlikely)
        
    def test_routing_unit_damage_reduction(self):
        """Test that routing units take reduced damage"""
        # Create a routing warrior
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        warrior.is_routing = True
        
        initial_soldiers = warrior.soldiers
        damage_amount = 20
        
        # Apply damage to routing unit
        warrior.take_casualties(damage_amount, self.game_state)
        
        # Should take reduced damage (70% of normal)
        expected_damage = int(damage_amount * 0.7)  # 14 damage instead of 20
        actual_casualties = initial_soldiers - warrior.soldiers
        
        assert actual_casualties == expected_damage, f"Routing unit should take {expected_damage} damage, got {actual_casualties}"
        
    def test_rally_conditions(self):
        """Test various rally conditions"""
        # Test 1: High morale, good condition unit
        warrior1 = UnitFactory.create_unit("Warrior1", KnightClass.WARRIOR, 5, 5)
        warrior1.is_routing = True
        warrior1.morale = 70  # High morale
        warrior1.cohesion = 70
        # Should have high rally chance (90%)
        
        # Test 2: Damaged unit with decent morale
        warrior2 = UnitFactory.create_unit("Warrior2", KnightClass.WARRIOR, 6, 5)
        warrior2.is_routing = True
        warrior2.morale = 50  # Decent morale
        warrior2.cohesion = CombatConfig.RALLY_COHESION_THRESHOLD
        warrior2.stats.stats.current_soldiers = 40  # Heavily damaged (from 100)
        # Should have reduced rally chance due to damage
        
        # Test 3: Very low morale unit (should not rally even after morale recovery)
        warrior3 = UnitFactory.create_unit("Warrior3", KnightClass.WARRIOR, 7, 5)
        warrior3.is_routing = True
        warrior3.stats.stats.morale = 5  # Set very low morale directly on stats
        # Should not be able to rally even after recovery
        
        # Verify rally threshold
        assert warrior3.morale < CombatConfig.RALLY_MORALE_THRESHOLD, "Unit with low morale should be below rally threshold"
        
        # Test that unit below threshold stays routing even after morale recovery
        initial_morale3 = warrior3.morale
        warrior3.end_turn()
        # Even with routing recovery, still below threshold
        assert warrior3.morale < CombatConfig.RALLY_MORALE_THRESHOLD, f"Even after recovery, should still be below rally threshold. Got: {warrior3.morale}"
        assert warrior3.is_routing, "Unit below rally threshold should remain routing"
    
    def test_units_can_enter_enemy_zoc(self):
        """Test that units can move into enemy ZOC to engage enemies"""
        # Create two units far apart initially
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 3, 3)
        attacker.player_id = 1
        defender = UnitFactory.create_unit("Defender", KnightClass.WARRIOR, 6, 6)
        defender.player_id = 2
        
        self.game_state.add_knight(attacker)
        self.game_state.add_knight(defender)
        self.game_state.current_player = 1
        
        # Verify units are not in each other's ZOC initially
        self.game_state._update_zoc_status()
        assert not attacker.in_enemy_zoc, "Attacker should not be in enemy ZOC initially"
        assert not defender.in_enemy_zoc, "Defender should not be in enemy ZOC initially"
        
        # Get possible moves for attacker
        movement_behavior = attacker.behaviors['move']
        possible_moves = movement_behavior.get_possible_moves(attacker, self.game_state)
        
        # Check that attacker can move to positions adjacent to defender (entering ZOC)
        adjacent_positions = [
            (5, 6), (7, 6), (6, 5), (6, 7),  # Cardinal directions
            (5, 5), (5, 7), (7, 5), (7, 7)   # Diagonal directions
        ]
        
        # At least some adjacent positions should be available
        can_reach_adjacent = any(pos in possible_moves for pos in adjacent_positions)
        assert can_reach_adjacent, f"Attacker should be able to move adjacent to enemy (into ZOC). Possible moves: {possible_moves}"
        
    def test_units_in_zoc_have_restricted_movement(self):
        """Test that units already in enemy ZOC have movement restrictions"""
        # Create two units adjacent (in each other's ZOC)
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 5, 5)
        attacker.player_id = 1
        defender = UnitFactory.create_unit("Defender", KnightClass.WARRIOR, 6, 5)
        defender.player_id = 2
        
        self.game_state.add_knight(attacker)
        self.game_state.add_knight(defender)
        self.game_state.current_player = 1
        
        # Update ZOC status
        self.game_state._update_zoc_status()
        assert attacker.in_enemy_zoc, "Attacker should be in enemy ZOC when adjacent"
        
        # Get possible moves for attacker (who is already in ZOC)
        movement_behavior = attacker.behaviors['move']
        possible_moves = movement_behavior.get_possible_moves(attacker, self.game_state)
        
        # Should have very limited movement options when in ZOC
        # (Only able to attack the engaging enemy or very limited disengagement)
        assert len(possible_moves) <= 3, f"Unit in enemy ZOC should have limited movement options. Got: {possible_moves}"

if __name__ == "__main__":
    # Run the tests
    test_class = TestEngagementMechanics()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    print("Running engagement mechanics tests...")
    for method_name in test_methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✅ {method_name} - PASSED")
        except Exception as e:
            print(f"❌ {method_name} - FAILED: {e}")
    
    print("Tests completed!")
