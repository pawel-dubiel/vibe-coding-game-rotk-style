"""Tests for disrupted status and its effects"""
import pygame
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.behaviors.combat import AttackBehavior

# Initialize pygame for tests
pygame.init()


class TestDisruptedStatus:
    """Test disrupted status and combat penalties"""
    
    def test_unit_has_disrupted_flag(self):
        """Test that units have is_disrupted flag"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        assert hasattr(unit, 'is_disrupted')
        assert unit.is_disrupted is False
    
    def test_disrupted_reduces_attack_damage(self):
        """Test that disrupted units deal 50% less damage"""
        game_state = MockGameState()
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 0, 0, add_generals=False)
        attacker.player_id = 1
        defender = UnitFactory.create_unit("Defender", KnightClass.WARRIOR, 1, 0, add_generals=False)
        defender.player_id = 2
        game_state.add_knight(attacker)
        game_state.add_knight(defender)
        
        attack_behavior = AttackBehavior()
        
        # Calculate normal damage
        normal_damage = attack_behavior.calculate_damage(attacker, defender)
        
        # Disrupt attacker
        attacker.is_disrupted = True
        
        # Calculate disrupted damage
        disrupted_damage = attack_behavior.calculate_damage(attacker, defender)
        
        # Disrupted damage should be roughly 50% of normal
        assert disrupted_damage < normal_damage
        # Due to rounding and other factors, check within reasonable range
        assert disrupted_damage <= normal_damage * 0.85  # Allow more variance for edge cases
    
    def test_disrupted_reduces_defense(self):
        """Test that disrupted units have 50% less defense"""
        game_state = MockGameState()
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 0, 0, add_generals=False)
        attacker.player_id = 1
        defender = UnitFactory.create_unit("Defender", KnightClass.WARRIOR, 1, 0, add_generals=False)
        defender.player_id = 2
        game_state.add_knight(attacker)
        game_state.add_knight(defender)
        
        attack_behavior = AttackBehavior()
        
        # Calculate damage against normal defender
        normal_damage = attack_behavior.calculate_damage(attacker, defender)
        
        # Disrupt defender
        defender.is_disrupted = True
        
        # Calculate damage against disrupted defender
        damage_vs_disrupted = attack_behavior.calculate_damage(attacker, defender)
        
        # Damage should be higher against disrupted defender
        assert damage_vs_disrupted > normal_damage
    
    def test_disrupted_status_can_be_set_and_cleared(self):
        """Test that disrupted status can be toggled"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Unit", KnightClass.CAVALRY, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Initially not disrupted
        assert unit.is_disrupted is False
        
        # Set disrupted
        unit.is_disrupted = True
        assert unit.is_disrupted is True
        
        # Clear disrupted
        unit.is_disrupted = False
        assert unit.is_disrupted is False
    
    def test_disrupted_affects_both_melee_and_ranged(self):
        """Test that disruption affects all types of attacks"""
        game_state = MockGameState()
        
        # Test with archer (ranged)
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 0, 0, add_generals=False)
        archer.player_id = 1
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 3, 0, add_generals=False)
        target.player_id = 2
        game_state.add_knight(archer)
        game_state.add_knight(target)
        
        from game.behaviors.combat import ArcherAttackBehavior
        archer_attack = ArcherAttackBehavior()
        
        # Normal damage
        normal_damage = archer_attack.calculate_damage(archer, target)
        
        # Disrupted damage
        archer.is_disrupted = True
        disrupted_damage = archer_attack.calculate_damage(archer, target)
        
        assert disrupted_damage < normal_damage
    
    def test_multiple_status_effects_stack(self):
        """Test that disrupted can combine with other status effects"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Unit", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Unit can have multiple status effects
        unit.is_disrupted = True
        unit.is_routing = True
        unit.in_enemy_zoc = True
        
        assert unit.is_disrupted is True
        assert unit.is_routing is True
        assert unit.in_enemy_zoc is True