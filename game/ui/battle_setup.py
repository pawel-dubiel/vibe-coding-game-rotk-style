import pygame
from typing import Tuple, Optional, Dict, Callable
from enum import Enum


class BattleSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BattleSetupScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 72)
        self.info_font = pygame.font.Font(None, 32)
        self.selected_size: Optional[BattleSize] = None
        self.ready = False
        self.vs_ai = True  # Will be set by main game
        
        self.battle_configs = {
            BattleSize.SMALL: {
                "description": "Small Battle",
                "knights": 3,
                "castles": 1,
                "board_size": (15, 15)
            },
            BattleSize.MEDIUM: {
                "description": "Medium Battle",
                "knights": 5,
                "castles": 2,
                "board_size": (20, 20)
            },
            BattleSize.LARGE: {
                "description": "Large Battle",
                "knights": 8,
                "castles": 3,
                "board_size": (25, 25)
            }
        }
        
        self._setup_buttons()
    
    def _setup_buttons(self):
        screen_width, screen_height = self.screen.get_size()
        button_width = 300
        button_height = 100
        button_spacing = 50
        
        total_height = len(BattleSize) * button_height + (len(BattleSize) - 1) * button_spacing
        start_y = (screen_height - total_height) // 2
        
        self.buttons = {}
        for i, size in enumerate(BattleSize):
            x = (screen_width - button_width) // 2
            y = start_y + i * (button_height + button_spacing)
            self.buttons[size] = pygame.Rect(x, y, button_width, button_height)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for size, rect in self.buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_size = size
                    self.ready = True
                    return True
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                return True
        
        return False
    
    def draw(self):
        self.screen.fill((50, 50, 50))
        
        title_text = self.title_font.render("Choose Battle Size", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Show selected game mode
        mode_text = "Single Player (vs AI)" if self.vs_ai else "Multiplayer (vs Human)"
        mode_surface = self.info_font.render(f"Mode: {mode_text}", True, (200, 200, 200))
        mode_rect = mode_surface.get_rect(center=(self.screen.get_width() // 2, 120))
        self.screen.blit(mode_surface, mode_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for size, rect in self.buttons.items():
            config = self.battle_configs[size]
            
            color = (100, 150, 100) if rect.collidepoint(mouse_pos) else (80, 80, 80)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 3)
            
            text = self.font.render(config["description"], True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
            
            info_font = pygame.font.Font(None, 24)
            info_text = f"Knights: {config['knights']} | Castles: {config['castles']} | Board: {config['board_size'][0]}x{config['board_size'][1]}"
            info_surface = info_font.render(info_text, True, (180, 180, 180))
            info_rect = info_surface.get_rect(center=(rect.centerx, rect.bottom + 20))
            self.screen.blit(info_surface, info_rect)
        
        pygame.display.flip()
    
    def get_battle_config(self) -> Optional[Dict]:
        if self.selected_size:
            return self.battle_configs[self.selected_size]
        return None