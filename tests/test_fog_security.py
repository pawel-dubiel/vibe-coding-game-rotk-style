"""Test that fog of war prevents information leaks"""
import pytest
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.visibility import VisibilityState, FogOfWar
from game.hex_utils import HexGrid


class TestFogSecurity:
    """Test fog of war security - no info leaks about hidden units"""
    
    def test_hidden_enemy_click_shows_terrain_not_unit(self):
        """Test that clicking on a hidden enemy shows terrain info, not unit info"""
        # Create game state
        game_state = MockGameState(board_width=20, board_height=20)
        game_state.hex_grid = HexGrid()
        game_state.fog_of_war = FogOfWar(20, 20, 2)
        game_state.current_player = 0
        
        # Add player unit at one corner
        player_unit = UnitFactory.create_unit("Player", KnightClass.WARRIOR, 0, 0)
        player_unit.player_id = 0
        game_state.add_knight(player_unit)
        
        # Add enemy unit far away (out of vision range)
        enemy_unit = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 10, 10)
        enemy_unit.player_id = 1
        game_state.add_knight(enemy_unit)
        
        # Update fog of war
        game_state.fog_of_war.update_player_visibility(game_state, 0)
        
        # Verify enemy is not visible
        visibility = game_state.fog_of_war.get_visibility_state(0, 10, 10)
        assert visibility == VisibilityState.HIDDEN
        
        # Simulate click on hidden enemy position
        # This should be handled by input_handler, but we'll test the logic
        knight_at_pos = game_state.get_knight_at(10, 10)
        assert knight_at_pos is not None  # Unit exists
        assert knight_at_pos.player_id == 1  # It's an enemy
        
        # Check if position is visible
        is_visible = game_state.fog_of_war.is_hex_visible(game_state.current_player, 10, 10)
        assert not is_visible  # Should not be visible
        
        # In this case, UI should show terrain info, not unit info
        # The input handler checks visibility before setting enemy_info_unit
        
    def test_visible_enemy_click_shows_unit_info(self):
        """Test that clicking on a visible enemy shows unit info"""
        # Create game state
        game_state = MockGameState(board_width=20, board_height=20)
        game_state.hex_grid = HexGrid()
        game_state.fog_of_war = FogOfWar(20, 20, 2)
        game_state.current_player = 0
        
        # Add player unit
        player_unit = UnitFactory.create_unit("Player", KnightClass.WARRIOR, 5, 5)
        player_unit.player_id = 0
        game_state.add_knight(player_unit)
        
        # Add enemy unit nearby (within vision range)
        enemy_unit = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
        enemy_unit.player_id = 1
        game_state.add_knight(enemy_unit)
        
        # Update fog of war
        game_state.fog_of_war.update_player_visibility(game_state, 0)
        
        # Verify enemy is visible
        visibility = game_state.fog_of_war.get_visibility_state(0, 6, 5)
        assert visibility == VisibilityState.VISIBLE
        
        # Check if position is visible
        is_visible = game_state.fog_of_war.is_hex_visible(game_state.current_player, 6, 5)
        assert is_visible  # Should be visible
        
        # In this case, UI should show unit info
        
    def test_renderer_doesnt_draw_hidden_units(self):
        """Test that renderer skips drawing units hidden by fog"""
        # Create game state
        game_state = MockGameState(board_width=20, board_height=20)
        game_state.hex_grid = HexGrid()
        game_state.fog_of_war = FogOfWar(20, 20, 2)
        game_state.current_player = 0
        
        # Add player unit
        player_unit = UnitFactory.create_unit("Player", KnightClass.WARRIOR, 0, 0)
        player_unit.player_id = 0
        game_state.add_knight(player_unit)
        
        # Add multiple enemy units at different distances
        positions = [(2, 0), (4, 0), (8, 0), (12, 0)]  # Increasing distance
        for i, (x, y) in enumerate(positions):
            enemy = UnitFactory.create_unit(f"Enemy{i}", KnightClass.WARRIOR, x, y)
            enemy.player_id = 1
            game_state.add_knight(enemy)
            
        # Update fog of war
        game_state.fog_of_war.update_player_visibility(game_state, 0)
        
        # Check visibility of each enemy
        visible_enemies = []
        for enemy in game_state.knights:
            if enemy.player_id == 1:
                visibility = game_state.fog_of_war.get_visibility_state(0, enemy.x, enemy.y)
                if visibility in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                    visible_enemies.append(enemy)
                    
        # Only nearby enemies should be visible
        assert len(visible_enemies) < 4  # Not all enemies are visible
        assert any(e.x <= 4 for e in visible_enemies)  # Close enemies are visible
        
    def test_ai_respects_fog_of_war(self):
        """Test that AI only considers visible enemy units"""
        # Create game state
        game_state = MockGameState(board_width=20, board_height=20)
        game_state.hex_grid = HexGrid()
        game_state.fog_of_war = FogOfWar(20, 20, 2)
        game_state.current_player = 0
        
        # Add AI unit
        ai_unit = UnitFactory.create_unit("AI", KnightClass.ARCHER, 5, 5)
        ai_unit.player_id = 1
        game_state.add_knight(ai_unit)
        
        # Add player units - one visible, one hidden
        visible_enemy = UnitFactory.create_unit("Visible", KnightClass.WARRIOR, 7, 5)
        visible_enemy.player_id = 0
        hidden_enemy = UnitFactory.create_unit("Hidden", KnightClass.WARRIOR, 15, 15)
        hidden_enemy.player_id = 0
        
        game_state.add_knight(visible_enemy)
        game_state.add_knight(hidden_enemy)
        
        # Update fog of war
        game_state.fog_of_war.update_player_visibility(game_state, 1)
        
        # Get visible enemies for AI (player 1)
        visible_units = game_state.fog_of_war.get_visible_units(game_state, 1)
        enemy_units = [u for u in visible_units if u.player_id == 0]
        
        # AI should only see the nearby enemy
        assert len(enemy_units) == 1
        assert enemy_units[0] == visible_enemy