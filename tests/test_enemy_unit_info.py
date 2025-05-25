"""Tests for enemy unit information display"""
import pygame
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass

# Initialize pygame for tests
pygame.init()


class TestEnemyUnitInfo:
    """Test showing enemy unit info when clicked"""
    
    def test_enemy_info_unit_property_exists(self):
        """Test that game state has enemy_info_unit property"""
        game_state = MockGameState()
        assert hasattr(game_state, 'enemy_info_unit')
        assert game_state.enemy_info_unit is None
    
    def test_clicking_enemy_sets_info(self):
        """Test that clicking enemy unit sets enemy_info_unit"""
        game_state = MockGameState()
        friendly = UnitFactory.create_unit("Friendly", KnightClass.WARRIOR, 0, 0, add_generals=False)
        friendly.player_id = 1
        enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 5, 5, add_generals=False)
        enemy.player_id = 2
        game_state.add_knight(friendly)
        game_state.add_knight(enemy)
        
        # Simulate clicking on enemy
        game_state.enemy_info_unit = enemy
        
        assert game_state.enemy_info_unit == enemy
        assert game_state.enemy_info_unit.player_id != game_state.current_player
    
    def test_clicking_friendly_clears_enemy_info(self):
        """Test that clicking friendly unit clears enemy info"""
        game_state = MockGameState()
        friendly = UnitFactory.create_unit("Friendly", KnightClass.WARRIOR, 0, 0, add_generals=False)
        friendly.player_id = 1
        enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 5, 5, add_generals=False)
        enemy.player_id = 2
        game_state.add_knight(friendly)
        game_state.add_knight(enemy)
        
        # Set enemy info
        game_state.enemy_info_unit = enemy
        
        # Select friendly unit
        game_state.selected_knight = friendly
        game_state.enemy_info_unit = None
        
        assert game_state.enemy_info_unit is None
        assert game_state.selected_knight == friendly
    
    def test_enemy_info_persists_until_cleared(self):
        """Test that enemy info persists until explicitly cleared"""
        game_state = MockGameState()
        enemy1 = UnitFactory.create_unit("Enemy 1", KnightClass.WARRIOR, 5, 5, add_generals=False)
        enemy1.player_id = 2
        enemy2 = UnitFactory.create_unit("Enemy 2", KnightClass.ARCHER, 6, 6, add_generals=False)
        enemy2.player_id = 2
        game_state.add_knight(enemy1)
        game_state.add_knight(enemy2)
        
        # Click first enemy
        game_state.enemy_info_unit = enemy1
        assert game_state.enemy_info_unit == enemy1
        
        # Click second enemy
        game_state.enemy_info_unit = enemy2
        assert game_state.enemy_info_unit == enemy2
        
        # Info should persist
        assert game_state.enemy_info_unit is not None
    
    def test_enemy_info_shows_all_unit_stats(self):
        """Test that enemy info includes all important unit stats"""
        game_state = MockGameState()
        enemy = UnitFactory.create_unit("Enemy Knight", KnightClass.CAVALRY, 5, 5, add_generals=False)
        enemy.player_id = 2
        enemy.is_disrupted = True
        game_state.add_knight(enemy)
        
        # Add a general to the enemy
        from game.components.general_factory import GeneralFactory
        general = GeneralFactory.create_general("Veteran Officer")
        enemy.generals.add_general(general)
        
        game_state.enemy_info_unit = enemy
        
        # Verify we can access all important stats
        assert hasattr(enemy, 'name')
        assert hasattr(enemy, 'knight_class')
        assert hasattr(enemy, 'soldiers')
        assert hasattr(enemy, 'max_soldiers')
        assert hasattr(enemy, 'morale')
        assert hasattr(enemy, 'will')
        assert hasattr(enemy, 'action_points')
        assert hasattr(enemy, 'is_disrupted')
        assert hasattr(enemy, 'generals')
        assert len(enemy.generals.generals) > 0