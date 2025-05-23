"""UI component for displaying general information"""
import pygame
from typing import Optional, List, Tuple
from game.entities.unit import Unit
from game.components.generals import General, GeneralAbilityType

class GeneralDisplay:
    """Display general information for a selected unit"""
    
    def __init__(self, x: int, y: int, width: int = 300, height: int = 200):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 24)
        self.visible = False
        self.selected_unit: Optional[Unit] = None
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.ability_colors = {
            GeneralAbilityType.PASSIVE: (100, 200, 100),
            GeneralAbilityType.ACTIVE: (100, 150, 255),
            GeneralAbilityType.TRIGGERED: (255, 200, 100)
        }
        
    def show(self, unit: Unit):
        """Show the display for the given unit"""
        self.selected_unit = unit
        self.visible = True
        
    def hide(self):
        """Hide the display"""
        self.visible = False
        self.selected_unit = None
        
    def render(self, screen: pygame.Surface):
        """Render the general display"""
        if not self.visible or not self.selected_unit:
            return
            
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Title
        title_text = self.title_font.render("Generals", True, self.text_color)
        title_rect = title_text.get_rect(centerx=self.rect.centerx, y=self.rect.y + 10)
        screen.blit(title_text, title_rect)
        
        # Display generals
        y_offset = 40
        generals = self.selected_unit.generals.generals
        
        if not generals:
            no_gen_text = self.font.render("No generals assigned", True, self.text_color)
            screen.blit(no_gen_text, (self.rect.x + 10, self.rect.y + y_offset))
            return
            
        for i, general in enumerate(generals):
            # General name and title
            gen_text = f"{general.name} - {general.title}"
            name_surf = self.font.render(gen_text, True, self.text_color)
            screen.blit(name_surf, (self.rect.x + 10, self.rect.y + y_offset))
            y_offset += 25
            
            # Level and experience
            level_text = f"Level {general.level} ({general.experience}/{general.level * 100} XP)"
            level_surf = self.font.render(level_text, True, (200, 200, 200))
            screen.blit(level_surf, (self.rect.x + 20, self.rect.y + y_offset))
            y_offset += 20
            
            # Abilities
            for ability in general.abilities:
                color = self.ability_colors.get(ability.ability_type, self.text_color)
                ability_text = f"• {ability.name}"
                
                # Add cooldown or cost info
                if ability.ability_type == GeneralAbilityType.ACTIVE:
                    if ability.cooldown > 0:
                        ability_text += f" (CD: {ability.cooldown})"
                    else:
                        ability_text += f" ({ability.get_will_cost()} Will)"
                        
                ability_surf = self.font.render(ability_text, True, color)
                screen.blit(ability_surf, (self.rect.x + 30, self.rect.y + y_offset))
                y_offset += 18
                
            y_offset += 10  # Space between generals
            
            # Don't overflow the display
            if y_offset > self.rect.height - 30:
                break
                
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click - returns True if click was inside display"""
        if self.visible and self.rect.collidepoint(x, y):
            return True
        return False
        
class GeneralActionMenu:
    """Menu for selecting general active abilities"""
    
    def __init__(self):
        self.visible = False
        self.unit: Optional[Unit] = None
        self.abilities: List[Tuple[General, Any]] = []
        self.rect = pygame.Rect(0, 0, 250, 100)
        self.font = pygame.font.Font(None, 20)
        
        # Colors
        self.bg_color = (50, 50, 50)
        self.border_color = (150, 150, 150)
        self.text_color = (255, 255, 255)
        self.hover_color = (100, 100, 150)
        self.selected_index = -1
        
    def show(self, unit: Unit, x: int, y: int):
        """Show the menu at the given position"""
        self.unit = unit
        self.abilities = unit.generals.get_active_abilities(unit)
        
        if not self.abilities:
            return
            
        # Calculate menu size
        height = len(self.abilities) * 25 + 20
        self.rect = pygame.Rect(x, y, 250, height)
        
        # Ensure menu stays on screen
        screen = pygame.display.get_surface()
        if self.rect.right > screen.get_width():
            self.rect.x = screen.get_width() - self.rect.width
        if self.rect.bottom > screen.get_height():
            self.rect.y = screen.get_height() - self.rect.height
            
        self.visible = True
        
    def hide(self):
        """Hide the menu"""
        self.visible = False
        self.unit = None
        self.abilities = []
        self.selected_index = -1
        
    def render(self, screen: pygame.Surface):
        """Render the menu"""
        if not self.visible:
            return
            
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Draw abilities
        y_offset = 10
        mouse_pos = pygame.mouse.get_pos()
        
        for i, (general, ability) in enumerate(self.abilities):
            # Check if mouse is over this item
            item_rect = pygame.Rect(
                self.rect.x + 5,
                self.rect.y + y_offset,
                self.rect.width - 10,
                20
            )
            
            if item_rect.collidepoint(mouse_pos):
                self.selected_index = i
                pygame.draw.rect(screen, self.hover_color, item_rect)
            
            # Draw ability name and cost
            text = f"{ability.name} ({ability.get_will_cost()} Will)"
            text_surf = self.font.render(text, True, self.text_color)
            screen.blit(text_surf, (self.rect.x + 10, self.rect.y + y_offset))
            
            y_offset += 25
            
    def handle_click(self, x: int, y: int) -> Optional[Tuple[General, Any]]:
        """Handle click - returns selected ability if any"""
        if not self.visible:
            return None
            
        if self.rect.collidepoint(x, y):
            if 0 <= self.selected_index < len(self.abilities):
                return self.abilities[self.selected_index]
                
        self.hide()
        return None