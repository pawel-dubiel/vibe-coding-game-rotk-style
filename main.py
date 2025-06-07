import pygame
import sys
from game.game_state import GameState
from game.rendering import CoreRenderer
from game.input_handler import InputHandler
from game.ui.battle_setup import BattleSetupScreen
from game.ui.game_mode_select import GameModeSelectScreen
from game.ui.main_menu import MainMenu, PauseMenu, MenuOption
from game.ui.test_scenario_menu import TestScenarioMenu
from game.ui.save_load_menu import SaveLoadMenu, SaveLoadAction
from game.ui.campaign_screen import CampaignScreen
from game.ui.country_selection import CountrySelectionScreen
from game.ui.map_editor import MapEditorScreen
from game.test_scenarios import TestScenarios
from game.save_manager import SaveManager

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
        self.in_test_scenarios = False
        self.in_country_selection = False
        self.in_campaign = False
        self.in_map_editor = False
        self.paused = False
        
        # UI screens
        self.main_menu = MainMenu(self.screen)
        self.pause_menu = PauseMenu(self.screen)
        self.game_mode_screen = GameModeSelectScreen(self.screen)
        self.battle_setup_screen = BattleSetupScreen(self.screen)
        self.test_scenario_menu = TestScenarioMenu(self.screen)
        self.save_load_menu = SaveLoadMenu(self.screen)
        self.country_selection_screen = CountrySelectionScreen(self.screen)
        self.campaign_screen = CampaignScreen(self.screen)
        self.map_editor_screen = MapEditorScreen(self.screen)
        
        # Save manager
        self.save_manager = SaveManager()
        
        # Game configuration
        self.vs_ai = True  # Default to single player
        
        self.game_state = None
        self.renderer = CoreRenderer(self.screen)
        self.input_handler = InputHandler()
        
        # Connect input handler and renderer for zoom functionality
        self.renderer.input_handler = self.input_handler
        
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            if self.in_main_menu:
                self._handle_main_menu()
            elif self.in_mode_select:
                self._handle_mode_select()
            elif self.in_setup:
                self._handle_battle_setup()
            elif self.in_test_scenarios:
                self._handle_test_scenarios()
            elif self.in_country_selection:
                self._handle_country_selection()
            elif self.in_campaign:
                self._handle_campaign()
            elif self.in_map_editor:
                self._handle_map_editor()
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
                # Handle save/load menu if visible
                if self.save_load_menu.visible:
                    result = self.save_load_menu.handle_event(event)
                    if result:
                        if result['action'] == 'load':
                            # Load the game
                            load_result = self.save_manager.load_game(result['slot'])
                            if load_result['success']:
                                # Create a minimal battle config
                                battle_config = {
                                    'board_size': (20, 20),
                                    'knights': 0,
                                    'castles': 0
                                }
                                self.game_state = GameState(battle_config)
                                # Connect renderer to game state for zoom consistency
                                self.game_state.renderer = self.renderer
                                self.game_state.restore_after_load(load_result['data'])
                                self.in_main_menu = False
                                self.in_game = True
                                self.save_load_menu.hide()
                                print(load_result['message'])
                            else:
                                print(f"Load failed: {load_result['message']}")
                else:
                    # Handle main menu events
                    option = self.main_menu.handle_event(event)
                    if option == MenuOption.NEW_GAME:
                        self.in_main_menu = False
                        self.in_mode_select = True
                    elif option == MenuOption.CAMPAIGN:
                        self.in_main_menu = False
                        self.in_country_selection = True
                        self.country_selection_screen.show()
                    elif option == MenuOption.MAP_EDITOR:
                        self.in_main_menu = False
                        self.in_map_editor = True
                        self.map_editor_screen.show()
                    elif option == MenuOption.LOAD_GAME:
                        self.save_load_menu.show(SaveLoadAction.LOAD)
                    elif option == MenuOption.OPTIONS:
                        # Placeholder for options menu
                        print("Options - Not implemented yet")
                    elif option == MenuOption.TEST_SCENARIOS:
                        self.in_main_menu = False
                        self.in_test_scenarios = True
                        self.test_scenario_menu.show()
                    elif option == MenuOption.QUIT:
                        self.running = False
        
        self.screen.fill((0, 0, 0))
        self.main_menu.draw()
        
        # Draw save/load menu on top if visible
        if self.save_load_menu.visible:
            self.save_load_menu.draw()
    
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
            # Connect renderer to game state for zoom consistency
            self.game_state.renderer = self.renderer
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
                # Handle save/load menu if visible
                if self.save_load_menu.visible:
                    result = self.save_load_menu.handle_event(event)
                    if result:
                        if result['action'] == 'save':
                            # Save the game
                            self.game_state.prepare_for_save()
                            save_result = self.save_manager.save_game(
                                self.game_state,
                                result['slot'],
                                result.get('name')
                            )
                            print(save_result['message'])
                            if save_result['success']:
                                self.save_load_menu.hide()
                        elif result['action'] == 'load':
                            # Load the game
                            load_result = self.save_manager.load_game(result['slot'])
                            if load_result['success']:
                                # Connect renderer to game state for zoom consistency
                                self.game_state.renderer = self.renderer
                                self.game_state.restore_after_load(load_result['data'])
                                self.save_load_menu.hide()
                                self.paused = False
                                self.pause_menu.hide()
                                print(load_result['message'])
                            else:
                                print(f"Load failed: {load_result['message']}")
                else:
                    # Handle pause menu events
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
                        self.save_load_menu.show(SaveLoadAction.SAVE)
                    elif option == MenuOption.LOAD_GAME:
                        self.save_load_menu.show(SaveLoadAction.LOAD)
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
            
        # Draw save/load menu on top if visible
        if self.save_load_menu.visible:
            self.save_load_menu.draw()
    
    def _handle_test_scenarios(self):
        """Handle test scenario selection screen"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                scenario_type = self.test_scenario_menu.handle_event(event)
                if scenario_type:
                    # Load the selected scenario
                    test_scenarios = TestScenarios()
                    scenario = test_scenarios.get_scenario(scenario_type)
                    
                    # Create a simple battle config for the scenario
                    battle_config = {
                        'board_size': (20, 20),
                        'knights': 0,  # We'll add units manually via scenario
                        'castles': 0
                    }
                    
                    # Create game state
                    self.game_state = GameState(battle_config, vs_ai=False)
                    # Connect renderer to game state for zoom consistency
                    self.game_state.renderer = self.renderer
                    
                    # Setup the scenario
                    scenario.setup(self.game_state)
                    
                    # Start the game
                    self.in_test_scenarios = False
                    self.in_game = True
                    self.test_scenario_menu.hide()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Go back to main menu
                    self.in_test_scenarios = False
                    self.in_main_menu = True
                    self.test_scenario_menu.hide()
        
        self.screen.fill((0, 0, 0))
        self.test_scenario_menu.draw()
    
    def _handle_country_selection(self):
        """Handle country selection screen"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                result = self.country_selection_screen.handle_event(event)
                if result:
                    if result.get('action') == 'back':
                        # Go back to main menu
                        self.in_country_selection = False
                        self.in_main_menu = True
                        self.country_selection_screen.hide()
                    elif result.get('action') == 'start_campaign':
                        # Start campaign with selected country
                        selected_country = result['country']
                        country_data = result['country_data']
                        
                        # Initialize campaign with selected country
                        from game.campaign.campaign_state import CampaignState
                        campaign_state = CampaignState(selected_country, country_data)
                        self.campaign_screen.campaign_state = campaign_state
                        
                        # Transition to campaign
                        self.in_country_selection = False
                        self.in_campaign = True
                        self.country_selection_screen.hide()
                        self.campaign_screen.show()
        
        self.country_selection_screen.draw()
    
    def _handle_map_editor(self):
        """Handle map editor mode"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                result = self.map_editor_screen.handle_event(event)
                if result:
                    if result.get('action') == 'back':
                        # Go back to main menu
                        self.in_map_editor = False
                        self.in_main_menu = True
                        self.map_editor_screen.hide()
        
        self.map_editor_screen.draw()
        
    def _handle_campaign(self):
        """Handle campaign mode"""
        dt = self.clock.get_time() / 1000.0  # Get delta time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                result = self.campaign_screen.handle_event(event)
                if result:
                    if result.get('action') == 'back_to_menu':
                        # Go back to main menu
                        self.in_campaign = False
                        self.in_main_menu = True
                        self.campaign_screen.hide()
                        
        # Update campaign state (for AI turns)
        self.campaign_screen.update(dt)
        
        # Check if a battle should start
        if self.campaign_screen.ready_for_battle:
            battle_config = self.campaign_screen.get_battle_config()
            if battle_config:
                # Pass the full battle config including campaign battle data 
                # (attacker_army, defender_army, etc.) to GameState
                self.game_state = GameState(battle_config, vs_ai=True)
                # Connect renderer to game state
                self.game_state.renderer = self.renderer
                
                # Transition to battle
                self.in_campaign = False
                self.in_game = True
                self.campaign_screen.ready_for_battle = False
                
        self.campaign_screen.draw()

if __name__ == "__main__":
    game = Game()
    game.run()