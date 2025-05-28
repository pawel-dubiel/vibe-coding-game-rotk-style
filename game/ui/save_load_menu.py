"""Save and Load game menu UI"""
import pygame
from typing import Optional, List, Callable
from enum import Enum
from game.save_manager import SaveManager, SaveMetadata


class SaveLoadAction(Enum):
    SAVE = "save"
    LOAD = "load"
    DELETE = "delete"
    CANCEL = "cancel"


class SaveLoadMenu:
    """Menu for saving and loading games with multiple slots"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        
        self.save_manager = SaveManager()
        self.visible = False
        self.action = SaveLoadAction.SAVE
        self.selected_slot = None
        self.confirm_overwrite = False
        self.confirm_delete = False
        self.save_name_input = ""
        self.input_active = False
        
        self.colors = {
            'background': (30, 30, 30),
            'slot': (60, 60, 60),
            'slot_hover': (80, 80, 80),
            'slot_selected': (100, 100, 100),
            'empty_slot': (40, 40, 40),
            'text': (255, 255, 255),
            'text_dim': (150, 150, 150),
            'button': (70, 70, 70),
            'button_hover': (100, 100, 100),
            'confirm': (100, 50, 50),
            'cancel': (50, 100, 50),
            'input_bg': (50, 50, 50),
            'input_active': (70, 70, 70)
        }
        
        self.slot_rects = []
        self.button_rects = {}
        self._setup_layout()
        
    def _setup_layout(self):
        """Setup UI layout"""
        screen_width, screen_height = self.screen.get_size()
        
        # Save slots layout
        slot_width = 600
        slot_height = 60
        slot_spacing = 10
        start_y = 150
        
        self.slot_rects = []
        for i in range(10):
            x = (screen_width - slot_width) // 2
            y = start_y + i * (slot_height + slot_spacing)
            self.slot_rects.append(pygame.Rect(x, y, slot_width, slot_height))
            
        # Buttons
        button_width = 120
        button_height = 40
        button_y = screen_height - 100
        
        self.button_rects = {
            'confirm': pygame.Rect(screen_width // 2 - button_width - 20, button_y, button_width, button_height),
            'cancel': pygame.Rect(screen_width // 2 + 20, button_y, button_width, button_height)
        }
        
        # Name input field (for save mode)
        self.input_rect = pygame.Rect(
            (screen_width - 400) // 2,
            button_y - 60,
            400,
            40
        )
        
    def show(self, action: SaveLoadAction):
        """Show the menu with specified action"""
        self.visible = True
        self.action = action
        self.selected_slot = None
        self.confirm_overwrite = False
        self.confirm_delete = False
        self.save_name_input = ""
        self.input_active = False
        
    def hide(self):
        """Hide the menu"""
        self.visible = False
        
    def handle_event(self, event: pygame.event.Event) -> Optional[dict]:
        """Handle input events, returns action dict or None"""
        if not self.visible:
            return None
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return {'action': 'cancel'}
                
            # Handle text input for save name
            if self.input_active and self.action == SaveLoadAction.SAVE:
                if event.key == pygame.K_BACKSPACE:
                    self.save_name_input = self.save_name_input[:-1]
                elif event.key == pygame.K_RETURN:
                    self.input_active = False
                elif len(self.save_name_input) < 30:
                    if event.unicode.isprintable():
                        self.save_name_input += event.unicode
                        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check slot clicks
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_slot = i + 1
                    
                    # For save action, check if slot is occupied
                    if self.action == SaveLoadAction.SAVE:
                        slots = self.save_manager.get_save_slots()
                        if slots[i] is not None:
                            self.confirm_overwrite = True
                    break
                    
            # Check input field click (save mode only)
            if self.action == SaveLoadAction.SAVE and self.input_rect.collidepoint(mouse_pos):
                self.input_active = True
            else:
                self.input_active = False
                
            # Check button clicks
            if self.button_rects['confirm'].collidepoint(mouse_pos):
                if self.selected_slot:
                    if self.confirm_overwrite:
                        # Confirmed overwrite
                        return {
                            'action': 'save',
                            'slot': self.selected_slot,
                            'name': self.save_name_input or None,
                            'overwrite': True
                        }
                    elif self.confirm_delete:
                        # Confirmed delete
                        result = self.save_manager.delete_save(self.selected_slot)
                        self.confirm_delete = False
                        self.selected_slot = None
                        return {'action': 'deleted', 'result': result}
                    else:
                        # Regular action
                        if self.action == SaveLoadAction.SAVE:
                            return {
                                'action': 'save',
                                'slot': self.selected_slot,
                                'name': self.save_name_input or None,
                                'overwrite': False
                            }
                        elif self.action == SaveLoadAction.LOAD:
                            return {
                                'action': 'load',
                                'slot': self.selected_slot
                            }
                        elif self.action == SaveLoadAction.DELETE:
                            self.confirm_delete = True
                            
            elif self.button_rects['cancel'].collidepoint(mouse_pos):
                if self.confirm_overwrite:
                    self.confirm_overwrite = False
                elif self.confirm_delete:
                    self.confirm_delete = False
                else:
                    self.hide()
                    return {'action': 'cancel'}
                    
        return None
        
    def draw(self):
        """Draw the menu"""
        if not self.visible:
            return
            
        # Semi-transparent background
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill(self.colors['background'])
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_text = {
            SaveLoadAction.SAVE: "Save Game",
            SaveLoadAction.LOAD: "Load Game",
            SaveLoadAction.DELETE: "Delete Save"
        }[self.action]
        
        title_surface = self.title_font.render(title_text, True, self.colors['text'])
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title_surface, title_rect)
        
        # Draw save slots
        slots = self.save_manager.get_save_slots()
        mouse_pos = pygame.mouse.get_pos()
        
        for i, (rect, slot_data) in enumerate(zip(self.slot_rects, slots)):
            slot_num = i + 1
            
            # Determine slot color
            if self.selected_slot == slot_num:
                color = self.colors['slot_selected']
            elif rect.collidepoint(mouse_pos):
                color = self.colors['slot_hover']
            elif slot_data is None:
                color = self.colors['empty_slot']
            else:
                color = self.colors['slot']
                
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.colors['text'], rect, 2)
            
            # Slot number
            slot_text = self.font.render(f"Slot {slot_num}", True, self.colors['text'])
            self.screen.blit(slot_text, (rect.x + 10, rect.y + 5))
            
            # Slot content
            if slot_data:
                # Save name
                name_text = self.small_font.render(slot_data.save_name, True, self.colors['text'])
                self.screen.blit(name_text, (rect.x + 120, rect.y + 5))
                
                # Details
                details = f"Turn {slot_data.turn_number} | Player {slot_data.current_player} | "
                details += f"{slot_data.knight_count} units | {slot_data.timestamp}"
                details_text = self.small_font.render(details, True, self.colors['text_dim'])
                self.screen.blit(details_text, (rect.x + 120, rect.y + 30))
            else:
                empty_text = self.small_font.render("Empty", True, self.colors['text_dim'])
                self.screen.blit(empty_text, (rect.x + 120, rect.y + 20))
                
        # Draw save name input (save mode only)
        if self.action == SaveLoadAction.SAVE:
            # Input field
            input_color = self.colors['input_active'] if self.input_active else self.colors['input_bg']
            pygame.draw.rect(self.screen, input_color, self.input_rect)
            pygame.draw.rect(self.screen, self.colors['text'], self.input_rect, 2)
            
            # Label
            label_text = self.small_font.render("Save Name (optional):", True, self.colors['text'])
            self.screen.blit(label_text, (self.input_rect.x, self.input_rect.y - 25))
            
            # Input text
            if self.save_name_input:
                input_surface = self.font.render(self.save_name_input, True, self.colors['text'])
            else:
                input_surface = self.font.render("Turn X", True, self.colors['text_dim'])
            input_rect = input_surface.get_rect(midleft=(self.input_rect.x + 10, self.input_rect.centery))
            self.screen.blit(input_surface, input_rect)
            
        # Draw confirmation dialog if needed
        if self.confirm_overwrite or self.confirm_delete:
            self._draw_confirmation_dialog()
        else:
            # Draw regular buttons
            self._draw_buttons()
            
    def _draw_confirmation_dialog(self):
        """Draw confirmation dialog for overwrite/delete"""
        # Dialog background
        dialog_rect = pygame.Rect(
            self.screen.get_width() // 2 - 200,
            self.screen.get_height() // 2 - 50,
            400,
            100
        )
        pygame.draw.rect(self.screen, self.colors['background'], dialog_rect)
        pygame.draw.rect(self.screen, self.colors['text'], dialog_rect, 2)
        
        # Confirmation text
        if self.confirm_overwrite:
            text = "Overwrite existing save?"
        else:
            text = "Delete this save?"
            
        confirm_text = self.font.render(text, True, self.colors['text'])
        text_rect = confirm_text.get_rect(center=(dialog_rect.centerx, dialog_rect.centery - 20))
        self.screen.blit(confirm_text, text_rect)
        
        # Confirm/Cancel buttons
        mouse_pos = pygame.mouse.get_pos()
        
        # Confirm button
        confirm_rect = self.button_rects['confirm']
        confirm_color = self.colors['confirm'] if confirm_rect.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(self.screen, confirm_color, confirm_rect)
        confirm_text = self.font.render("Confirm", True, self.colors['text'])
        text_rect = confirm_text.get_rect(center=confirm_rect.center)
        self.screen.blit(confirm_text, text_rect)
        
        # Cancel button
        cancel_rect = self.button_rects['cancel']
        cancel_color = self.colors['cancel'] if cancel_rect.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(self.screen, cancel_color, cancel_rect)
        cancel_text = self.font.render("Cancel", True, self.colors['text'])
        text_rect = cancel_text.get_rect(center=cancel_rect.center)
        self.screen.blit(cancel_text, text_rect)
        
    def _draw_buttons(self):
        """Draw action buttons"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Confirm button (only if slot selected)
        if self.selected_slot:
            button_text = {
                SaveLoadAction.SAVE: "Save",
                SaveLoadAction.LOAD: "Load",
                SaveLoadAction.DELETE: "Delete"
            }[self.action]
            
            confirm_rect = self.button_rects['confirm']
            color = self.colors['button_hover'] if confirm_rect.collidepoint(mouse_pos) else self.colors['button']
            pygame.draw.rect(self.screen, color, confirm_rect)
            text = self.font.render(button_text, True, self.colors['text'])
            text_rect = text.get_rect(center=confirm_rect.center)
            self.screen.blit(text, text_rect)
            
        # Cancel button
        cancel_rect = self.button_rects['cancel']
        color = self.colors['button_hover'] if cancel_rect.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(self.screen, color, cancel_rect)
        text = self.font.render("Cancel", True, self.colors['text'])
        text_rect = text.get_rect(center=cancel_rect.center)
        self.screen.blit(text, text_rect)