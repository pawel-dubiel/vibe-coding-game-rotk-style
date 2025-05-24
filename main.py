import pygame
import sys
from game.game_state import GameState
from game.renderer import Renderer
from game.input_handler import InputHandler
from game.ui.battle_setup import BattleSetupScreen
from game.ui.game_mode_select import GameModeSelectScreen
from game.ui.main_menu import MainMenu, PauseMenu, MenuOption

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("Castle Knights")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game states
        self.in_main_menu = True
        self.in_mode_select = False
        self.in_setup = False
        self.in_game = False
        self.paused = False
        
        # UI screens
        self.main_menu = MainMenu(self.screen)
        self.pause_menu = PauseMenu(self.screen)
        self.game_mode_screen = GameModeSelectScreen(self.screen)
        self.battle_setup_screen = BattleSetupScreen(self.screen)
        
        # Game configuration
        self.vs_ai = True  # Default to single player
        
        self.game_state = None
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
        
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            if self.in_main_menu:
                self._handle_main_menu()
            elif self.in_mode_select:
                self._handle_mode_select()
            elif self.in_setup:
                self._handle_battle_setup()
            elif self.in_game:
                self._handle_game(dt)
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def _handle_main_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                option = self.main_menu.handle_event(event)
                if option == MenuOption.NEW_GAME:
                    self.in_main_menu = False
                    self.in_mode_select = True
                elif option == MenuOption.LOAD_GAME:
                    # Placeholder for load game functionality
                    print("Load Game - Not implemented yet")
                elif option == MenuOption.OPTIONS:
                    # Placeholder for options menu
                    print("Options - Not implemented yet")
                elif option == MenuOption.QUIT:
                    self.running = False
        
        self.screen.fill((0, 0, 0))
        self.main_menu.draw()
    
    def _handle_mode_select(self):
        """Handle game mode selection screen"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Go back to main menu
                self.in_mode_select = False
                self.in_main_menu = True
                self.game_mode_screen.reset()
            else:
                if self.game_mode_screen.handle_event(event):
                    if self.game_mode_screen.ready:
                        # Mode selected, save the choice and move to battle setup
                        self.vs_ai = self.game_mode_screen.get_vs_ai()
                        self.battle_setup_screen.vs_ai = self.vs_ai
                        self.in_mode_select = False
                        self.in_setup = True
                        self.game_mode_screen.reset()
                    else:
                        # ESC was pressed, go back to main menu
                        self.in_mode_select = False
                        self.in_main_menu = True
                        self.game_mode_screen.reset()
        
        self.game_mode_screen.draw()
    
    def _handle_battle_setup(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Go back to mode select
                self.in_setup = False
                self.in_mode_select = True
                self.battle_setup_screen.ready = False
            else:
                self.battle_setup_screen.handle_event(event)
        
        if self.battle_setup_screen.ready:
            battle_config = self.battle_setup_screen.get_battle_config()
            self.game_state = GameState(battle_config, vs_ai=self.vs_ai)
            self.in_setup = False
            self.in_game = True
            self.battle_setup_screen.ready = False
        else:
            self.battle_setup_screen.draw()
    
    def _handle_game(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Toggle pause menu
                self.paused = not self.paused
                if self.paused:
                    self.pause_menu.show()
                else:
                    self.pause_menu.hide()
            elif self.paused:
                option = self.pause_menu.handle_event(event)
                if option == MenuOption.RESUME:
                    self.paused = False
                    self.pause_menu.hide()
                elif option == MenuOption.NEW_GAME:
                    self.paused = False
                    self.in_game = False
                    self.in_mode_select = True
                    self.pause_menu.hide()
                elif option == MenuOption.SAVE_GAME:
                    print("Save Game - Not implemented yet")
                elif option == MenuOption.LOAD_GAME:
                    print("Load Game - Not implemented yet")
                elif option == MenuOption.OPTIONS:
                    print("Options - Not implemented yet")
                elif option == MenuOption.QUIT:
                    self.running = False
            else:
                self.input_handler.handle_event(event, self.game_state)
        
        if not self.paused:
            self.game_state.update(dt)
        
        self.renderer.render(self.game_state)
        
        if self.paused:
            self.pause_menu.draw()

if __name__ == "__main__":
    game = Game()
    game.run()