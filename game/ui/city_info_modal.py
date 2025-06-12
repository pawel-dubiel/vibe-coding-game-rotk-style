import pygame
from typing import Optional, Tuple
from game.campaign.campaign_state import City, Country


class CityInfoModal:
    def __init__(self, width: int = 400, height: int = 500):
        self.width = width
        self.height = height
        self.visible = False
        self.city: Optional[City] = None
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
        
    def show(self, city: City, country: Country, screen_size: Tuple[int, int]):
        """Show the modal with city information"""
        self.visible = True
        self.city = city
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
        self.city = None
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
        if not self.visible or not self.city or not self.country:
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
        title_text = self.title_font.render(self.city.name, True, self.text_color)
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
        
        # City information
        info_items = [
            ("Income:", f"{self.city.income} gold/turn"),
            ("Population:", f"{self.city.population:,}"),
            ("Castle Level:", f"{self.city.castle_level}"),
            ("Specialization:", self.city.specialization or "None"),
        ]
        
        for label, value in info_items:
            self._draw_info_line(screen, label, value, y_offset)
            y_offset += 30
            
        # Draw separator line
        pygame.draw.line(screen, self.border_color,
                        (self.rect.left + 20, y_offset), (self.rect.right - 20, y_offset), 1)
        y_offset += 20
        
        # Additional city details
        if self.city.description:
            desc_label = self.font.render("Description:", True, self.label_color)
            screen.blit(desc_label, (self.rect.left + 30, y_offset))
            y_offset += 30
            
            # Wrap description text
            words = self.city.description.split()
            lines = []
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if self.small_font.size(test_line)[0] > self.width - 60:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
                else:
                    current_line.append(word)
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines[:3]:  # Limit to 3 lines
                text_surface = self.small_font.render(line, True, self.text_color)
                screen.blit(text_surface, (self.rect.left + 50, y_offset))
                y_offset += 25
            
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