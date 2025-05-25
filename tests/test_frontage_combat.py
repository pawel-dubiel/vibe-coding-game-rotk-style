"""Tests for frontage in combat calculations"""
import pygame
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType
from game.behaviors.combat import AttackBehavior

# Initialize pygame for tests
pygame.init()


class TestFrontageInCombat:
    """Test frontage calculation in combat strength"""
    
    def test_effective_soldiers_uses_frontage(self):
        """Test that effective soldiers is limited by formation width"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Warriors have 100 soldiers but formation width of 40 (based on actual implementation)
        assert unit.stats.stats.current_soldiers == 100
        assert unit.stats.stats.formation_width == 40
        assert unit.stats.get_effective_soldiers() == 40
    
    def test_terrain_affects_frontage(self):
        """Test that terrain modifies effective frontage"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 5, 5, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Get forest terrain
        forest_terrain = game_state.terrain_map.get_terrain(5, 5)
        if forest_terrain and forest_terrain.type == TerrainType.FOREST:
            # Forest reduces frontage by 30%
            effective = unit.stats.get_effective_soldiers(forest_terrain)
            assert effective == int(40 * 0.7)  # 28 soldiers (40 is base frontage for warriors)
    
    def test_combat_damage_uses_effective_soldiers(self):
        """Test that combat damage calculation uses frontage"""
        game_state = MockGameState()
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 0, 0, add_generals=False)
        attacker.player_id = 1
        defender = UnitFactory.create_unit("Defender", KnightClass.WARRIOR, 1, 0, add_generals=False)
        defender.player_id = 2
        game_state.add_knight(attacker)
        game_state.add_knight(defender)
        
        # Create attack behavior
        attack_behavior = AttackBehavior()
        
        # Calculate damage - should use effective soldiers (40) not total (100)
        damage = attack_behavior.calculate_damage(attacker, defender)
        
        # Damage should be based on 40 soldiers, not 100
        # With attack_per_soldier = 1.0, base damage = 40 * 1.0 = 40
        assert damage < attacker.stats.stats.current_soldiers  # Less than total soldiers
    
    def test_cavalry_charge_uses_frontage(self):
        """Test that cavalry charge damage uses frontage"""
        game_state = MockGameState()
        cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 0, 0, add_generals=False)
        cavalry.player_id = 1
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 1, 0, add_generals=False)
        target.player_id = 2
        game_state.add_knight(cavalry)
        game_state.add_knight(target)
        
        # Get effective soldiers for cavalry
        effective = cavalry.stats.get_effective_soldiers()
        
        # Cavalry has 50 soldiers with formation width of 25
        assert cavalry.stats.stats.current_soldiers == 50
        assert cavalry.stats.stats.formation_width == 25
        assert effective == 25
    
    def test_different_unit_types_have_different_frontage(self):
        """Test that different unit types have appropriate formation widths"""
        game_state = MockGameState()
        
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 1, 0, add_generals=False)
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 2, 0, add_generals=False)
        mage = UnitFactory.create_unit("Mage", KnightClass.MAGE, 3, 0, add_generals=False)
        
        # Check formation widths
        assert warrior.stats.stats.formation_width == 40
        assert archer.stats.stats.formation_width == 40
        assert cavalry.stats.stats.formation_width == 25
        assert mage.stats.stats.formation_width == 15
        
    def test_bridge_terrain_severely_limits_frontage(self):
        """Test that bridge terrain has severe frontage limitations"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Find a bridge tile
        bridge_terrain = None
        for x in range(game_state.board_width):
            for y in range(game_state.board_height):
                terrain = game_state.terrain_map.get_terrain(x, y)
                if terrain and terrain.type.value == "Bridge":
                    bridge_terrain = terrain
                    break
            if bridge_terrain:
                break
        
        if bridge_terrain:
            # Bridge reduces frontage by 50%
            effective = unit.stats.get_effective_soldiers(bridge_terrain)
            assert effective == int(40 * 0.5)  # 20 soldiers