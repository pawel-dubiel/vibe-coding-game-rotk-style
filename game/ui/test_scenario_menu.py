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
            'border': (200, 200, 200),
            'scrollbar': (100, 100, 100),
            'scrollbar_bg': (40, 40, 40)
        }
        
        # Scrolling
        self.scroll_offset = 0
        self.max_visible_items = 5  # Show 5 scenarios at once
        self.item_height = 80
        self.item_spacing = 10
        self.dragging_scrollbar = False
        self.drag_offset = 0
        
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
        
        # Scrollable area for scenarios
        self.list_x = panel_x + 20
        self.list_y = panel_y + 100
        self.list_width = panel_width - 60  # Leave room for scrollbar
        self.list_height = panel_height - 160  # Leave room for title and instructions
        
        # Scrollbar
        self.scrollbar_width = 20
        self.scrollbar_x = panel_x + panel_width - 40
        self.scrollbar_y = self.list_y
        self.scrollbar_height = self.list_height
        
        # Calculate visible area
        self.visible_height = self.max_visible_items * (self.item_height + self.item_spacing)
        
        # Create clipping rectangle for scenario list
        self.clip_rect = pygame.Rect(self.list_x, self.list_y, 
                                     self.list_width + self.scrollbar_width, 
                                     min(self.visible_height, self.list_height))
            
    def show(self):
        """Show the menu"""
        self.visible = True
        self.selected_scenario = None
        self.hovered_index = 0
        self.scroll_offset = 0
        
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
                self._ensure_visible()
            elif event.key == pygame.K_DOWN:
                self.hovered_index = min(len(self.scenario_list) - 1, self.hovered_index + 1)
                self._ensure_visible()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if 0 <= self.hovered_index < len(self.scenario_list):
                    self.selected_scenario = self.scenario_list[self.hovered_index][0]
                    return self.selected_scenario
                    
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            # Check scenario items
            if self.clip_rect.collidepoint(mouse_pos):
                relative_y = mouse_pos[1] - self.list_y + self.scroll_offset
                index = relative_y // (self.item_height + self.item_spacing)
                if 0 <= index < len(self.scenario_list):
                    self.hovered_index = index
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if event.button == 1:  # Left click
                # Check scenario items
                if self.clip_rect.collidepoint(mouse_pos):
                    relative_y = mouse_pos[1] - self.list_y + self.scroll_offset
                    index = relative_y // (self.item_height + self.item_spacing)
                    if 0 <= index < len(self.scenario_list):
                        self.selected_scenario = self.scenario_list[index][0]
                        return self.selected_scenario
                        
                # Check scrollbar
                if self._is_scrollbar_visible():
                    scrollbar_rect = self._get_scrollbar_rect()
                    if scrollbar_rect.collidepoint(mouse_pos):
                        self.dragging_scrollbar = True
                        self.drag_offset = mouse_pos[1] - scrollbar_rect.y
                        
            elif event.button == 4:  # Mouse wheel up
                self.scroll_offset = max(0, self.scroll_offset - (self.item_height + self.item_spacing))
            elif event.button == 5:  # Mouse wheel down
                max_scroll = self._get_max_scroll()
                self.scroll_offset = min(max_scroll, self.scroll_offset + (self.item_height + self.item_spacing))
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_scrollbar = False
                
        elif event.type == pygame.MOUSEMOTION and hasattr(self, 'dragging_scrollbar') and self.dragging_scrollbar:
            mouse_pos = pygame.mouse.get_pos()
            # Calculate new scroll position based on mouse position
            scrollbar_track_height = self.scrollbar_height - self._get_scrollbar_handle_height()
            new_y = mouse_pos[1] - self.scrollbar_y - self.drag_offset
            scroll_ratio = new_y / scrollbar_track_height if scrollbar_track_height > 0 else 0
            scroll_ratio = max(0, min(1, scroll_ratio))
            self.scroll_offset = int(scroll_ratio * self._get_max_scroll())
                    
        return None
        
    def _get_max_scroll(self):
        """Get maximum scroll offset"""
        total_height = len(self.scenario_list) * (self.item_height + self.item_spacing)
        return max(0, total_height - self.visible_height)
        
    def _is_scrollbar_visible(self):
        """Check if scrollbar should be visible"""
        return len(self.scenario_list) > self.max_visible_items
        
    def _get_scrollbar_handle_height(self):
        """Calculate scrollbar handle height"""
        if not self._is_scrollbar_visible():
            return 0
        total_height = len(self.scenario_list) * (self.item_height + self.item_spacing)
        ratio = self.visible_height / total_height if total_height > 0 else 1
        return max(30, int(self.scrollbar_height * ratio))
        
    def _get_scrollbar_rect(self):
        """Get scrollbar handle rectangle"""
        handle_height = self._get_scrollbar_handle_height()
        max_scroll = self._get_max_scroll()
        
        if max_scroll > 0:
            scroll_ratio = self.scroll_offset / max_scroll
        else:
            scroll_ratio = 0
            
        handle_y = self.scrollbar_y + int((self.scrollbar_height - handle_height) * scroll_ratio)
        return pygame.Rect(self.scrollbar_x, handle_y, self.scrollbar_width, handle_height)
        
    def _ensure_visible(self):
        """Ensure the hovered item is visible"""
        item_y = self.hovered_index * (self.item_height + self.item_spacing)
        
        # If item is above visible area
        if item_y < self.scroll_offset:
            self.scroll_offset = item_y
            
        # If item is below visible area
        elif item_y + self.item_height > self.scroll_offset + self.visible_height:
            self.scroll_offset = item_y + self.item_height - self.visible_height
            
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
        
        # Set clipping for scenario list
        self.screen.set_clip(self.clip_rect)
        
        # Draw scenarios
        for i, (scenario_type, scenario) in enumerate(self.scenario_list):
            # Calculate position with scroll offset
            item_y = self.list_y + i * (self.item_height + self.item_spacing) - self.scroll_offset
            
            # Skip if outside visible area
            if item_y + self.item_height < self.list_y or item_y > self.list_y + self.visible_height:
                continue
                
            rect = pygame.Rect(self.list_x, item_y, self.list_width, self.item_height)
            
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
            
        # Remove clipping
        self.screen.set_clip(None)
        
        # Draw scrollbar if needed
        if self._is_scrollbar_visible():
            # Scrollbar background
            scrollbar_bg_rect = pygame.Rect(self.scrollbar_x, self.scrollbar_y, 
                                           self.scrollbar_width, self.scrollbar_height)
            pygame.draw.rect(self.screen, self.colors['scrollbar_bg'], scrollbar_bg_rect)
            
            # Scrollbar handle
            handle_rect = self._get_scrollbar_rect()
            pygame.draw.rect(self.screen, self.colors['scrollbar'], handle_rect)
            pygame.draw.rect(self.screen, self.colors['border'], handle_rect, 1)
            
        # Draw instructions
        inst_text = self.desc_font.render("Use arrow keys or mouse to select, scroll wheel to scroll, Enter to confirm, ESC to cancel", 
                                        True, self.colors['text_dim'])
        inst_rect = inst_text.get_rect(centerx=self.panel_rect.centerx, 
                                      y=self.panel_rect.bottom - 40)
        self.screen.blit(inst_text, inst_rect)