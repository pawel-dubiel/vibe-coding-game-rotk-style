import pygame
import sys
from game.game_state import GameState
from game.renderer import Renderer
from game.input_handler import InputHandler
from game.ui.battle_setup import BattleSetupScreen

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("Castle Knights")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.battle_setup_screen = BattleSetupScreen(self.screen)
        self.in_setup = True
        
        self.game_state = None
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
        
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            if self.in_setup:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    else:
                        self.battle_setup_screen.handle_event(event)
                
                if self.battle_setup_screen.ready:
                    battle_config = self.battle_setup_screen.get_battle_config()
                    self.game_state = GameState(battle_config)
                    self.in_setup = False
                else:
                    self.battle_setup_screen.draw()
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    else:
                        self.input_handler.handle_event(event, self.game_state)
                
                self.game_state.update(dt)
                self.renderer.render(self.game_state)
                pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()