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
        
        # Scrolling
        self.scroll_offset = 0
        self.max_visible_slots = 6  # Show 6 slots at a time
        self.dragging_scrollbar = False
        self.drag_offset = 0
        
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
            'input_active': (70, 70, 70),
            'scrollbar_bg': (40, 40, 40),
            'scrollbar': (80, 80, 80)
        }
        
        self.slot_rects = []
        self.button_rects = {}
        self._setup_layout()
        
    def _setup_layout(self):
        """Setup UI layout"""
        screen_width, screen_height = self.screen.get_size()
        
        # Save slots layout
        self.slot_width = 600
        self.slot_height = 60
        self.slot_spacing = 10
        self.start_y = 150
        
        # Calculate dimensions
        self.list_x = (screen_width - self.slot_width) // 2
        self.list_y = self.start_y
        self.list_height = self.max_visible_slots * (self.slot_height + self.slot_spacing)
        
        # Scrollbar
        self.scrollbar_width = 20
        self.scrollbar_x = self.list_x + self.slot_width + 10
        self.scrollbar_y = self.list_y
        self.scrollbar_height = self.list_height
        
        # Create clipping rectangle for slot list
        self.clip_rect = pygame.Rect(
            self.list_x - 10,
            self.list_y - 10,
            self.slot_width + 40,
            self.list_height + 20
        )
        
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
        
    def _is_scrollbar_visible(self) -> bool:
        """Check if scrollbar should be visible"""
        return 10 > self.max_visible_slots  # We have 10 total slots
        
    def _get_max_scroll(self) -> int:
        """Get maximum scroll offset"""
        total_height = 10 * (self.slot_height + self.slot_spacing)
        visible_height = self.max_visible_slots * (self.slot_height + self.slot_spacing)
        return max(0, total_height - visible_height)
        
    def _get_scrollbar_rect(self) -> pygame.Rect:
        """Calculate scrollbar handle rectangle"""
        if not self._is_scrollbar_visible():
            return pygame.Rect(0, 0, 0, 0)
            
        # Calculate handle size and position
        max_scroll = self._get_max_scroll()
        if max_scroll == 0:
            handle_height = self.scrollbar_height
            handle_y = self.scrollbar_y
        else:
            visible_ratio = self.list_height / (10 * (self.slot_height + self.slot_spacing))
            handle_height = int(self.scrollbar_height * visible_ratio)
            handle_height = max(30, handle_height)  # Minimum handle size
            
            scroll_ratio = self.scroll_offset / max_scroll
            available_space = self.scrollbar_height - handle_height
            handle_y = self.scrollbar_y + int(available_space * scroll_ratio)
            
        return pygame.Rect(self.scrollbar_x, handle_y, self.scrollbar_width, handle_height)
        
    def _scroll_to_position(self, y: int):
        """Scroll to a specific Y position based on scrollbar"""
        relative_y = y - self.scrollbar_y
        available_space = self.scrollbar_height - self._get_scrollbar_rect().height
        
        if available_space > 0:
            scroll_ratio = relative_y / available_space
            max_scroll = self._get_max_scroll()
            self.scroll_offset = int(max_scroll * scroll_ratio)
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        
    def show(self, action: SaveLoadAction):
        """Show the menu with specified action"""
        self.visible = True
        self.action = action
        self.selected_slot = None
        self.confirm_overwrite = False
        self.confirm_delete = False
        self.save_name_input = ""
        self.input_active = False
        self.scroll_offset = 0
        self.dragging_scrollbar = False
        
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
                        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if event.button == 1:  # Left click
                # Check slot clicks
                if self.clip_rect.collidepoint(mouse_pos):
                    relative_y = mouse_pos[1] - self.list_y + self.scroll_offset
                    slot_index = relative_y // (self.slot_height + self.slot_spacing)
                    
                    if 0 <= slot_index < 10:
                        self.selected_slot = slot_index + 1
                        
                        # For save action, check if slot is occupied
                        if self.action == SaveLoadAction.SAVE:
                            slots = self.save_manager.get_save_slots()
                            if slots[slot_index] is not None:
                                self.confirm_overwrite = True
                                
                # Check scrollbar
                if self._is_scrollbar_visible():
                    scrollbar_rect = self._get_scrollbar_rect()
                    if scrollbar_rect.collidepoint(mouse_pos):
                        self.dragging_scrollbar = True
                        self.drag_offset = mouse_pos[1] - scrollbar_rect.y
                        
            elif event.button == 4:  # Mouse wheel up
                self.scroll_offset = max(0, self.scroll_offset - (self.slot_height + self.slot_spacing))
            elif event.button == 5:  # Mouse wheel down
                max_scroll = self._get_max_scroll()
                self.scroll_offset = min(max_scroll, self.scroll_offset + (self.slot_height + self.slot_spacing))
                    
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
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_scrollbar = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_scrollbar:
                mouse_pos = pygame.mouse.get_pos()
                new_y = mouse_pos[1] - self.drag_offset
                self._scroll_to_position(new_y)
                    
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
        
        # Set clipping for save slot list
        self.screen.set_clip(self.clip_rect)
        
        # Draw save slots
        slots = self.save_manager.get_save_slots()
        mouse_pos = pygame.mouse.get_pos()
        
        for i, slot_data in enumerate(slots):
            slot_num = i + 1
            
            # Calculate position with scroll offset
            slot_y = self.list_y + i * (self.slot_height + self.slot_spacing) - self.scroll_offset
            
            # Skip if outside visible area
            if slot_y + self.slot_height < self.list_y or slot_y > self.list_y + self.list_height:
                continue
                
            rect = pygame.Rect(self.list_x, slot_y, self.slot_width, self.slot_height)
            
            # Determine slot color
            if self.selected_slot == slot_num:
                color = self.colors['slot_selected']
            elif rect.collidepoint(mouse_pos) and self.clip_rect.collidepoint(mouse_pos):
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
            pygame.draw.rect(self.screen, self.colors['text'], handle_rect, 1)
                
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