"""Test scenario selection menu"""
import pygame
from typing import Optional, Tuple
from game.test_scenarios import TestScenarios, ScenarioType

class TestScenarioMenu:
    """Menu for selecting test scenarios"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 64)
        self.desc_font = pygame.font.Font(None, 28)
        self.visible = False
        self.selected_scenario: Optional[ScenarioType] = None
        self.hovered_index = 0
        
        self.test_scenarios = TestScenarios()
        self.scenario_list = self.test_scenarios.get_all_scenarios()
        
        self.colors = {
            'background': (30, 30, 30),
            'panel': (50, 50, 50),
            'button': (70, 70, 70),
            'button_hover': (100, 100, 100),
            'button_selected': (120, 80, 40),
            'text': (255, 255, 255),
            'text_dim': (180, 180, 180),
            'border': (200, 200, 200)
        }
        
        self.scenario_rects = []
        self._setup_layout()
        
    def _setup_layout(self):
        """Setup the menu layout"""
        screen_width, screen_height = self.screen.get_size()
        
        # Panel dimensions
        panel_width = int(screen_width * 0.8)
        panel_height = int(screen_height * 0.8)
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2
        
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Scenario list area
        list_x = panel_x + 20
        list_y = panel_y + 100
        list_width = panel_width - 40
        item_height = 80
        
        self.scenario_rects = []
        for i in range(len(self.scenario_list)):
            rect = pygame.Rect(list_x, list_y + i * (item_height + 10), 
                             list_width, item_height)
            self.scenario_rects.append(rect)
            
    def show(self):
        """Show the menu"""
        self.visible = True
        self.selected_scenario = None
        self.hovered_index = 0
        
    def hide(self):
        """Hide the menu"""
        self.visible = False
        
    def handle_event(self, event: pygame.event.Event) -> Optional[ScenarioType]:
        """Handle input events"""
        if not self.visible:
            return None
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return None
            elif event.key == pygame.K_UP:
                self.hovered_index = max(0, self.hovered_index - 1)
            elif event.key == pygame.K_DOWN:
                self.hovered_index = min(len(self.scenario_list) - 1, self.hovered_index + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if 0 <= self.hovered_index < len(self.scenario_list):
                    self.selected_scenario = self.scenario_list[self.hovered_index][0]
                    return self.selected_scenario
                    
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.scenario_rects):
                if rect.collidepoint(mouse_pos):
                    self.hovered_index = i
                    
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.scenario_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_scenario = self.scenario_list[i][0]
                    return self.selected_scenario
                    
        return None
        
    def draw(self):
        """Draw the menu"""
        if not self.visible:
            return
            
        # Draw semi-transparent background
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill(self.colors['background'])
        self.screen.blit(overlay, (0, 0))
        
        # Draw main panel
        pygame.draw.rect(self.screen, self.colors['panel'], self.panel_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.panel_rect, 3)
        
        # Draw title
        title_text = self.title_font.render("Select Test Scenario", True, self.colors['text'])
        title_rect = title_text.get_rect(centerx=self.panel_rect.centerx, 
                                       y=self.panel_rect.y + 20)
        self.screen.blit(title_text, title_rect)
        
        # Draw scenarios
        for i, (scenario_type, scenario) in enumerate(self.scenario_list):
            rect = self.scenario_rects[i]
            
            # Background
            if i == self.hovered_index:
                color = self.colors['button_hover']
            else:
                color = self.colors['button']
                
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.colors['border'], rect, 2)
            
            # Scenario name
            name_text = self.font.render(scenario.name, True, self.colors['text'])
            name_rect = name_text.get_rect(x=rect.x + 15, y=rect.y + 10)
            self.screen.blit(name_text, name_rect)
            
            # Scenario description
            desc_text = self.desc_font.render(scenario.description, True, self.colors['text_dim'])
            desc_rect = desc_text.get_rect(x=rect.x + 15, y=rect.y + 45)
            self.screen.blit(desc_text, desc_rect)
            
        # Draw instructions
        inst_text = self.desc_font.render("Use arrow keys or mouse to select, Enter to confirm, ESC to cancel", 
                                        True, self.colors['text_dim'])
        inst_rect = inst_text.get_rect(centerx=self.panel_rect.centerx, 
                                      y=self.panel_rect.bottom - 40)
        self.screen.blit(inst_text, inst_rect)