import pygame
from typing import Optional, Tuple
from game.campaign.campaign_state import Army, Country


class ArmyInfoModal:
    def __init__(self, width: int = 400, height: int = 400):
        self.width = width
        self.height = height
        self.visible = False
        self.army: Optional[Army] = None
        self.country: Optional[Country] = None
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)
        
        # Colors
        self.bg_color = (40, 40, 40, 240)
        self.border_color = (180, 180, 180)
        self.text_color = (255, 255, 255)
        self.label_color = (200, 200, 200)
        self.close_button_color = (200, 50, 50)
        self.close_button_hover_color = (255, 100, 100)
        
        # Close button
        self.close_button_size = 30
        self.close_button_rect = None
        self.close_button_hovered = False
        self.just_shown = False  # Prevent immediate closing on same frame
        
        # Calculate position (will be centered on screen)
        self.rect = None
        
    def show(self, army: Army, country: Country, screen_size: Tuple[int, int]):
        """Show the modal with army information"""
        self.visible = True
        self.army = army
        self.country = country
        self.just_shown = True  # Set flag to prevent immediate closing
        
        # Center the modal on screen
        x = (screen_size[0] - self.width) // 2
        y = (screen_size[1] - self.height) // 2
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        # Position close button
        self.close_button_rect = pygame.Rect(
            self.rect.right - self.close_button_size - 10,
            self.rect.top + 10,
            self.close_button_size,
            self.close_button_size
        )
        
    def hide(self):
        """Hide the modal"""
        self.visible = False
        self.army = None
        self.country = None
        self.just_shown = False
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events. Returns True if event was consumed"""
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            if self.close_button_rect:
                self.close_button_hovered = self.close_button_rect.collidepoint(event.pos)
            return self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check close button first - always allow closing via X button
                if self.close_button_rect and self.close_button_rect.collidepoint(event.pos):
                    self.hide()
                    return True
                
                # Check if click is outside modal
                if not self.rect.collidepoint(event.pos):
                    # Don't close from outside clicks if just shown this frame
                    if not self.just_shown:
                        self.hide()
                        return True
                return self.rect.collidepoint(event.pos)
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
                
        return False
        
    def draw(self, screen: pygame.Surface):
        """Draw the modal"""
        if not self.visible or not self.army or not self.country:
            return
        
        # Clear the just_shown flag after first draw
        if self.just_shown:
            self.just_shown = False
            
        # Draw semi-transparent overlay
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw modal background directly on screen
        pygame.draw.rect(screen, (40, 40, 40), self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Draw close button
        close_color = self.close_button_hover_color if self.close_button_hovered else self.close_button_color
        pygame.draw.rect(screen, close_color, self.close_button_rect)
        pygame.draw.line(screen, self.text_color,
                        (self.close_button_rect.left + 8, self.close_button_rect.top + 8),
                        (self.close_button_rect.right - 8, self.close_button_rect.bottom - 8), 2)
        pygame.draw.line(screen, self.text_color,
                        (self.close_button_rect.right - 8, self.close_button_rect.top + 8),
                        (self.close_button_rect.left + 8, self.close_button_rect.bottom - 8), 2)
        
        # Draw content
        y_offset = self.rect.top + 20
        
        # Title
        title_text = self.title_font.render(f"Army {self.army.id}", True, self.text_color)
        title_rect = title_text.get_rect(centerx=self.rect.centerx, y=y_offset)
        screen.blit(title_text, title_rect)
        y_offset += 50
        
        # Country
        self._draw_info_line(screen, "Country:", self.country.name, y_offset)
        y_offset += 30
        
        # Draw separator line
        pygame.draw.line(screen, self.border_color,
                        (self.rect.left + 20, y_offset), (self.rect.right - 20, y_offset), 1)
        y_offset += 20
        
        # Army composition
        info_items = [
            ("Knights:", f"{self.army.knights} units"),
            ("Archers:", f"{self.army.archers} units"),
            ("Cavalry:", f"{self.army.cavalry} units"),
            ("Total Strength:", f"{self.army.knights + self.army.archers + self.army.cavalry} units"),
        ]
        
        for label, value in info_items:
            self._draw_info_line(screen, label, value, y_offset)
            y_offset += 30
            
        # Draw separator line
        pygame.draw.line(screen, self.border_color,
                        (self.rect.left + 20, y_offset), (self.rect.right - 20, y_offset), 1)
        y_offset += 20
        
        # Movement info
        movement_text = f"{self.army.movement_points}/{self.army.max_movement_points}"
        self._draw_info_line(screen, "Movement Points:", movement_text, y_offset)
        y_offset += 30
        
        # Position
        position_text = f"Hex ({self.army.position.q}, {self.army.position.r})"
        self._draw_info_line(screen, "Position:", position_text, y_offset)
        y_offset += 30
            
        # Instructions
        y_offset = self.rect.bottom - 60
        instruction_text = self.small_font.render("Click outside or press ESC to close", True, self.label_color)
        instruction_rect = instruction_text.get_rect(centerx=self.rect.centerx, y=y_offset)
        screen.blit(instruction_text, instruction_rect)
        
    def _draw_info_line(self, surface: pygame.Surface, label: str, value: str, y_offset: int):
        """Helper to draw an information line with label and value"""
        label_text = self.font.render(label, True, self.label_color)
        value_text = self.font.render(str(value), True, self.text_color)
        
        surface.blit(label_text, (self.rect.left + 30, y_offset))
        surface.blit(value_text, (self.rect.left + 200, y_offset))