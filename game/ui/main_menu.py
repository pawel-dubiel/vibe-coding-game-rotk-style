import pygame
from typing import Callable, Dict, Optional
from enum import Enum


class MenuOption(Enum):
    NEW_GAME = "new_game"
    LOAD_GAME = "load_game"
    SAVE_GAME = "save_game"
    OPTIONS = "options"
    RESUME = "resume"
    QUIT = "quit"


class MainMenu:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 96)
        self.selected_option: Optional[MenuOption] = None
        self.visible = True
        
        self.colors = {
            'background': (30, 30, 30),
            'button': (70, 70, 70),
            'button_hover': (100, 100, 100),
            'button_disabled': (50, 50, 50),
            'text': (255, 255, 255),
            'text_disabled': (128, 128, 128),
            'border': (200, 200, 200)
        }
        
        self.buttons: Dict[MenuOption, pygame.Rect] = {}
        self.button_states: Dict[MenuOption, bool] = {
            MenuOption.NEW_GAME: True,
            MenuOption.LOAD_GAME: True,
            MenuOption.SAVE_GAME: False,  # Disabled in main menu
            MenuOption.OPTIONS: True,
            MenuOption.RESUME: False,  # Only available in pause menu
            MenuOption.QUIT: True
        }
        
        self._setup_buttons()
    
    def _setup_buttons(self):
        screen_width, screen_height = self.screen.get_size()
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Main menu buttons
        menu_options = [
            MenuOption.NEW_GAME,
            MenuOption.LOAD_GAME,
            MenuOption.OPTIONS,
            MenuOption.QUIT
        ]
        
        total_height = len(menu_options) * button_height + (len(menu_options) - 1) * button_spacing
        start_y = (screen_height - total_height) // 2 + 50  # Offset for title
        
        for i, option in enumerate(menu_options):
            x = (screen_width - button_width) // 2
            y = start_y + i * (button_height + button_spacing)
            self.buttons[option] = pygame.Rect(x, y, button_width, button_height)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[MenuOption]:
        if not self.visible:
            return None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for option, rect in self.buttons.items():
                if rect.collidepoint(mouse_pos) and self.button_states[option]:
                    self.selected_option = option
                    return option
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return MenuOption.QUIT
        
        return None
    
    def draw(self):
        if not self.visible:
            return
        
        # Draw semi-transparent background
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill(self.colors['background'])
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title_text = self.title_font.render("Castle Knights", True, self.colors['text'])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        
        for option, rect in self.buttons.items():
            if not self.button_states[option]:
                color = self.colors['button_disabled']
                text_color = self.colors['text_disabled']
            elif rect.collidepoint(mouse_pos):
                color = self.colors['button_hover']
                text_color = self.colors['text']
            else:
                color = self.colors['button']
                text_color = self.colors['text']
            
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.colors['border'], rect, 3)
            
            # Button text
            text = self._get_button_text(option)
            text_surface = self.font.render(text, True, text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def _get_button_text(self, option: MenuOption) -> str:
        text_map = {
            MenuOption.NEW_GAME: "New Game",
            MenuOption.LOAD_GAME: "Load Game",
            MenuOption.SAVE_GAME: "Save Game",
            MenuOption.OPTIONS: "Options",
            MenuOption.RESUME: "Resume",
            MenuOption.QUIT: "Quit"
        }
        return text_map[option]
    
    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False


class PauseMenu(MainMenu):
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        
        # Adjust button states for pause menu
        self.button_states[MenuOption.RESUME] = True
        self.button_states[MenuOption.SAVE_GAME] = True
        
        # Re-setup buttons for pause menu
        self._setup_pause_buttons()
    
    def _setup_pause_buttons(self):
        screen_width, screen_height = self.screen.get_size()
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Pause menu buttons
        menu_options = [
            MenuOption.RESUME,
            MenuOption.NEW_GAME,
            MenuOption.SAVE_GAME,
            MenuOption.LOAD_GAME,
            MenuOption.OPTIONS,
            MenuOption.QUIT
        ]
        
        total_height = len(menu_options) * button_height + (len(menu_options) - 1) * button_spacing
        start_y = (screen_height - total_height) // 2
        
        self.buttons.clear()
        for i, option in enumerate(menu_options):
            x = (screen_width - button_width) // 2
            y = start_y + i * (button_height + button_spacing)
            self.buttons[option] = pygame.Rect(x, y, button_width, button_height)
    
    def draw(self):
        if not self.visible:
            return
        
        # Draw semi-transparent background
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill(self.colors['background'])
        self.screen.blit(overlay, (0, 0))
        
        # Draw "Paused" title
        title_text = self.title_font.render("Paused", True, self.colors['text'])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        
        for option, rect in self.buttons.items():
            if not self.button_states[option]:
                color = self.colors['button_disabled']
                text_color = self.colors['text_disabled']
            elif rect.collidepoint(mouse_pos):
                color = self.colors['button_hover']
                text_color = self.colors['text']
            else:
                color = self.colors['button']
                text_color = self.colors['text']
            
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.colors['border'], rect, 3)
            
            # Button text
            text = self._get_button_text(option)
            text_surface = self.font.render(text, True, text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)