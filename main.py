import pygame
import sys
from game.game_state import GameState
from game.renderer import Renderer
from game.input_handler import InputHandler

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("Castle Knights")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.game_state = GameState()
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
        
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
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