"""Test multiplayer mode functionality"""
import unittest
from game.game_state import GameState
from game.ui.game_mode_select import GameModeSelectScreen, GameMode
import pygame

class TestMultiplayerMode(unittest.TestCase):
    """Test multiplayer vs single player mode selection and functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        pygame.init()
        self.screen = pygame.display.set_mode((100, 100))  # Minimal screen for testing
        
    def tearDown(self):
        """Clean up after tests"""
        pygame.quit()
        
    def test_game_state_single_player_mode(self):
        """Test GameState creation in single player mode (vs AI)"""
        battle_config = {
            'board_size': (10, 10),
            'knights': 2,
            'castles': 1
        }
        
        # Single player mode
        game_state = GameState(battle_config, vs_ai=True)
        self.assertTrue(game_state.vs_ai)
        self.assertIsNotNone(game_state.ai_player)
        self.assertEqual(game_state.ai_player.player_id, 2)
        
    def test_game_state_multiplayer_mode(self):
        """Test GameState creation in multiplayer mode (no AI)"""
        battle_config = {
            'board_size': (10, 10),
            'knights': 2,
            'castles': 1
        }
        
        # Multiplayer mode
        game_state = GameState(battle_config, vs_ai=False)
        self.assertFalse(game_state.vs_ai)
        self.assertIsNone(game_state.ai_player)
        
    def test_game_mode_screen_single_player_selection(self):
        """Test game mode screen single player selection"""
        mode_screen = GameModeSelectScreen(self.screen)
        
        # Simulate single player selection
        mode_screen.selected_mode = GameMode.SINGLE_PLAYER
        mode_screen.ready = True
        
        self.assertTrue(mode_screen.get_vs_ai())
        
    def test_game_mode_screen_multiplayer_selection(self):
        """Test game mode screen multiplayer selection"""
        mode_screen = GameModeSelectScreen(self.screen)
        
        # Simulate multiplayer selection
        mode_screen.selected_mode = GameMode.MULTIPLAYER
        mode_screen.ready = True
        
        self.assertFalse(mode_screen.get_vs_ai())
        
    def test_game_mode_screen_reset(self):
        """Test game mode screen reset functionality"""
        mode_screen = GameModeSelectScreen(self.screen)
        
        # Set some state
        mode_screen.selected_mode = GameMode.SINGLE_PLAYER
        mode_screen.ready = True
        
        # Reset
        mode_screen.reset()
        
        self.assertIsNone(mode_screen.selected_mode)
        self.assertFalse(mode_screen.ready)
        
    def test_multiplayer_turn_mechanics(self):
        """Test that multiplayer mode doesn't auto-advance turns"""
        battle_config = {
            'board_size': (10, 10),
            'knights': 2,
            'castles': 1
        }
        
        # Create multiplayer game
        game_state = GameState(battle_config, vs_ai=False)
        
        # Start at player 1
        self.assertEqual(game_state.current_player, 1)
        
        # In multiplayer, both players are human, so no AI thinking
        self.assertFalse(game_state.ai_thinking)
        
        # Manual turn advancement should work
        game_state.end_turn()
        self.assertEqual(game_state.current_player, 2)
        self.assertFalse(game_state.ai_thinking)  # Still no AI
        
        # Turn back to player 1
        game_state.end_turn()
        self.assertEqual(game_state.current_player, 1)
        
    def test_multiplayer_unit_selection(self):
        """Test that both players can select their units in multiplayer mode"""
        battle_config = {
            'board_size': (10, 10),
            'knights': 2,
            'castles': 1
        }
        
        # Create multiplayer game
        game_state = GameState(battle_config, vs_ai=False)
        
        # Player 1 should be able to select their units
        self.assertEqual(game_state.current_player, 1)
        player1_units = [k for k in game_state.knights if k.player_id == 1]
        self.assertTrue(len(player1_units) > 0)
        
        # Select player 1 unit
        unit = player1_units[0]
        result = game_state.select_knight(unit.x * 64, unit.y * 64)
        self.assertTrue(result)
        self.assertIsNotNone(game_state.selected_knight)
        self.assertEqual(game_state.selected_knight.player_id, 1)
        
        # End turn and switch to player 2
        game_state.end_turn()
        self.assertEqual(game_state.current_player, 2)
        self.assertFalse(game_state.ai_thinking)  # No AI in multiplayer
        
        # Player 2 should be able to select their units
        player2_units = [k for k in game_state.knights if k.player_id == 2]
        self.assertTrue(len(player2_units) > 0)
        
        # Select player 2 unit
        unit = player2_units[0]
        result = game_state.select_knight(unit.x * 64, unit.y * 64)
        self.assertTrue(result)
        self.assertIsNotNone(game_state.selected_knight)
        self.assertEqual(game_state.selected_knight.player_id, 2)

if __name__ == '__main__':
    unittest.main()