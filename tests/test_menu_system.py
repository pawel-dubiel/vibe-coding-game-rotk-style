import unittest
import pygame
from game.ui.main_menu import MainMenu, PauseMenu, MenuOption


class TestMenuSystem(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
    
    def tearDown(self):
        pygame.quit()
    
    def test_main_menu_creation(self):
        """Test main menu initializes correctly"""
        menu = MainMenu(self.screen)
        
        # Check initial state
        self.assertTrue(menu.visible)
        self.assertIsNone(menu.selected_option)
        
        # Check buttons are created
        self.assertIn(MenuOption.NEW_GAME, menu.buttons)
        self.assertIn(MenuOption.LOAD_GAME, menu.buttons)
        self.assertIn(MenuOption.OPTIONS, menu.buttons)
        self.assertIn(MenuOption.QUIT, menu.buttons)
        
        # Check button states
        self.assertTrue(menu.button_states[MenuOption.NEW_GAME])
        self.assertTrue(menu.button_states[MenuOption.LOAD_GAME])
        self.assertTrue(menu.button_states[MenuOption.OPTIONS])
        self.assertTrue(menu.button_states[MenuOption.QUIT])
        self.assertFalse(menu.button_states[MenuOption.SAVE_GAME])
        self.assertFalse(menu.button_states[MenuOption.RESUME])
    
    def test_pause_menu_creation(self):
        """Test pause menu has different button configuration"""
        menu = PauseMenu(self.screen)
        
        # Check pause menu specific buttons
        self.assertIn(MenuOption.RESUME, menu.buttons)
        self.assertIn(MenuOption.SAVE_GAME, menu.buttons)
        
        # Check button states
        self.assertTrue(menu.button_states[MenuOption.RESUME])
        self.assertTrue(menu.button_states[MenuOption.SAVE_GAME])
    
    def test_menu_visibility(self):
        """Test menu show/hide functionality"""
        menu = MainMenu(self.screen)
        
        # Initially visible
        self.assertTrue(menu.visible)
        
        # Test hide
        menu.hide()
        self.assertFalse(menu.visible)
        
        # Test show
        menu.show()
        self.assertTrue(menu.visible)
    
    def test_mouse_click_handling(self):
        """Test menu responds to mouse clicks"""
        menu = MainMenu(self.screen)
        
        # Get the New Game button rect
        new_game_rect = menu.buttons[MenuOption.NEW_GAME]
        
        # Create mouse click event at button center
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'button': 1,
            'pos': new_game_rect.center
        })
        
        # Mock pygame.mouse.get_pos to return button center
        original_get_pos = pygame.mouse.get_pos
        pygame.mouse.get_pos = lambda: new_game_rect.center
        
        try:
            result = menu.handle_event(click_event)
            self.assertEqual(result, MenuOption.NEW_GAME)
            self.assertEqual(menu.selected_option, MenuOption.NEW_GAME)
        finally:
            pygame.mouse.get_pos = original_get_pos
    
    def test_escape_key_handling(self):
        """Test menu responds to escape key"""
        menu = MainMenu(self.screen)
        
        # Create escape key event
        escape_event = pygame.event.Event(pygame.KEYDOWN, {
            'key': pygame.K_ESCAPE
        })
        
        result = menu.handle_event(escape_event)
        self.assertEqual(result, MenuOption.QUIT)
    
    def test_disabled_button_click(self):
        """Test clicking disabled button returns None"""
        menu = PauseMenu(self.screen)
        
        # Disable save game button for testing
        menu.button_states[MenuOption.SAVE_GAME] = False
        save_rect = menu.buttons[MenuOption.SAVE_GAME]
        
        # Create mouse click event at button center
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'button': 1,
            'pos': save_rect.center
        })
        
        # Mock pygame.mouse.get_pos
        original_get_pos = pygame.mouse.get_pos
        pygame.mouse.get_pos = lambda: save_rect.center
        
        try:
            result = menu.handle_event(click_event)
            self.assertIsNone(result)
        finally:
            pygame.mouse.get_pos = original_get_pos
    
    def test_button_text_mapping(self):
        """Test button text is correctly mapped"""
        menu = MainMenu(self.screen)
        
        self.assertEqual(menu._get_button_text(MenuOption.NEW_GAME), "New Game")
        self.assertEqual(menu._get_button_text(MenuOption.LOAD_GAME), "Load Game")
        self.assertEqual(menu._get_button_text(MenuOption.SAVE_GAME), "Save Game")
        self.assertEqual(menu._get_button_text(MenuOption.OPTIONS), "Options")
        self.assertEqual(menu._get_button_text(MenuOption.RESUME), "Resume")
        self.assertEqual(menu._get_button_text(MenuOption.QUIT), "Quit")


if __name__ == '__main__':
    unittest.main()