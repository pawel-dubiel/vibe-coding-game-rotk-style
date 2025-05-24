"""Game mode selection screen for choosing single player vs multiplayer"""
import pygame
from typing import Optional
from enum import Enum


class GameMode(Enum):
    SINGLE_PLAYER = "single_player"
    MULTIPLAYER = "multiplayer"


class GameModeSelectScreen:
    """Screen for choosing between single player (vs AI) and multiplayer (vs human)"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 72)
        self.info_font = pygame.font.Font(None, 32)
        self.selected_mode: Optional[GameMode] = None
        self.ready = False
        
        self.colors = {
            'background': (50, 50, 50),
            'button': (80, 80, 80),
            'button_hover': (100, 150, 100),
            'text': (255, 255, 255),
            'text_secondary': (200, 200, 200),
            'border': (200, 200, 200)
        }
        
        self.mode_configs = {
            GameMode.SINGLE_PLAYER: {
                "title": "Single Player",
                "description": "Play against computer AI",
                "info": "Perfect for learning and practicing tactics"
            },
            GameMode.MULTIPLAYER: {
                "title": "Multiplayer",
                "description": "Play against another human player",
                "info": "Take turns on the same computer (hot seat)"
            }
        }
        
        self._setup_buttons()
    
    def _setup_buttons(self):
        """Setup button positions and sizes"""
        screen_width, screen_height = self.screen.get_size()
        button_width = 400
        button_height = 120
        button_spacing = 60
        
        modes = list(GameMode)
        total_height = len(modes) * button_height + (len(modes) - 1) * button_spacing
        start_y = (screen_height - total_height) // 2
        
        self.buttons = {}
        for i, mode in enumerate(modes):
            x = (screen_width - button_width) // 2
            y = start_y + i * (button_height + button_spacing)
            self.buttons[mode] = pygame.Rect(x, y, button_width, button_height)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events, return True if mode was selected"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for mode, rect in self.buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_mode = mode
                    self.ready = True
                    return True
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.selected_mode = GameMode.SINGLE_PLAYER
                self.ready = True
                return True
            elif event.key == pygame.K_2:
                self.selected_mode = GameMode.MULTIPLAYER
                self.ready = True
                return True
            elif event.key == pygame.K_ESCAPE:
                # Signal to go back
                return True
        
        return False
    
    def draw(self):
        """Draw the game mode selection screen"""
        self.screen.fill(self.colors['background'])
        
        # Draw title
        title_text = self.title_font.render("Choose Game Mode", True, self.colors['text'])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Draw instruction
        instruction_text = self.info_font.render("Click a mode or press 1/2", True, self.colors['text_secondary'])
        instruction_rect = instruction_text.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        
        for mode, rect in self.buttons.items():
            config = self.mode_configs[mode]
            
            # Button color based on hover
            if rect.collidepoint(mouse_pos):
                color = self.colors['button_hover']
            else:
                color = self.colors['button']
            
            # Draw button background
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.colors['border'], rect, 3)
            
            # Draw button content
            self._draw_button_content(rect, config, mode)
        
        # Draw back instruction
        back_text = self.info_font.render("Press ESC to go back", True, self.colors['text_secondary'])
        back_rect = back_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        self.screen.blit(back_text, back_rect)
    
    def _draw_button_content(self, rect: pygame.Rect, config: dict, mode: GameMode):
        """Draw the content inside a mode button"""
        # Mode title
        title_text = self.font.render(config["title"], True, self.colors['text'])
        title_rect = title_text.get_rect(center=(rect.centerx, rect.centery - 20))
        self.screen.blit(title_text, title_rect)
        
        # Mode description
        desc_text = self.info_font.render(config["description"], True, self.colors['text_secondary'])
        desc_rect = desc_text.get_rect(center=(rect.centerx, rect.centery + 10))
        self.screen.blit(desc_text, desc_rect)
        
        # Additional info
        info_text = pygame.font.Font(None, 24).render(config["info"], True, self.colors['text_secondary'])
        info_rect = info_text.get_rect(center=(rect.centerx, rect.centery + 35))
        self.screen.blit(info_text, info_rect)
        
        # Keyboard shortcut
        key_text = "1" if mode == GameMode.SINGLE_PLAYER else "2"
        key_surface = pygame.font.Font(None, 32).render(f"[{key_text}]", True, self.colors['text'])
        key_rect = key_surface.get_rect(topright=(rect.right - 10, rect.top + 10))
        self.screen.blit(key_surface, key_rect)
    
    def get_vs_ai(self) -> bool:
        """Return True if single player mode (vs AI), False if multiplayer"""
        return self.selected_mode == GameMode.SINGLE_PLAYER
    
    def reset(self):
        """Reset the selection state"""
        self.selected_mode = None
        self.ready = False