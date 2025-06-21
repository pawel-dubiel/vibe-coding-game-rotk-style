import pygame
from typing import Optional, List, Dict, Any, Tuple
from game.campaign.campaign_state import City, Army, CampaignState


class CampaignContextMenu:
    """Context menu for campaign mode - handles city and army actions"""
    
    def __init__(self):
        self.visible = False
        self.x = 0
        self.y = 0
        self.options = []
        self.selected_option = None
        self.target_city: Optional[City] = None
        self.target_army: Optional[Army] = None
        self.campaign_state: Optional[CampaignState] = None
        
        self.width = 180
        self.option_height = 30
        self.font = pygame.font.Font(None, 20)
        
        self.colors = {
            'background': (60, 60, 60),
            'hover': (80, 80, 80),
            'text': (255, 255, 255),
            'disabled': (100, 100, 100),
            'border': (100, 100, 100)
        }
    
    def show_for_city(self, x: int, y: int, city: City, campaign_state: CampaignState, has_army: bool = False):
        """Show context menu for a city"""
        self.visible = True
        self.x = x
        self.y = y
        self.target_city = city
        self.target_army = None
        self.campaign_state = campaign_state
        self.options = self._get_city_actions(city, campaign_state, has_army)
        
        # Adjust position if menu would go off screen
        screen = pygame.display.get_surface()
        if screen:
            screen_height = screen.get_height()
            screen_width = screen.get_width()
            menu_height = len(self.options) * self.option_height
            
            if self.y + menu_height > screen_height - 20:
                self.y = screen_height - 20 - menu_height
            if self.x + self.width > screen_width - 20:
                self.x = screen_width - 20 - self.width
    
    def show_for_army(self, x: int, y: int, army: Army, campaign_state: CampaignState, has_city: bool = False):
        """Show context menu for an army"""
        self.visible = True
        self.x = x
        self.y = y
        self.target_army = army
        self.target_city = None
        self.campaign_state = campaign_state
        self.options = self._get_army_actions(army, campaign_state, has_city)
        
        # Adjust position if menu would go off screen
        screen = pygame.display.get_surface()
        if screen:
            screen_height = screen.get_height()
            screen_width = screen.get_width()
            menu_height = len(self.options) * self.option_height
            
            if self.y + menu_height > screen_height - 20:
                self.y = screen_height - 20 - menu_height
            if self.x + self.width > screen_width - 20:
                self.x = screen_width - 20 - self.width
    
    def hide(self):
        """Hide the context menu"""
        self.visible = False
        self.selected_option = None
        self.target_city = None
        self.target_army = None
        self.campaign_state = None
    
    def _get_city_actions(self, city: City, campaign_state: CampaignState, has_army: bool = False) -> List[Dict[str, Any]]:
        """Get available actions for a city"""
        actions = []
        
        # Check if city belongs to current player
        is_player_city = city.country == campaign_state.current_country
        
        # Always show info
        actions.append({
            'text': 'City Information',
            'action': 'show_info',
            'enabled': True
        })
        
        if is_player_city:
            # Check if we can recruit
            treasury = campaign_state.country_treasury.get(campaign_state.current_country, 0)
            if treasury >= 100:  # Basic recruitment cost
                actions.append({
                    'text': 'Recruit Army (100g)',
                    'action': 'recruit',
                    'enabled': True
                })
            else:
                actions.append({
                    'text': 'Recruit Army (100g)',
                    'action': 'recruit',
                    'enabled': False
                })
            
            # Check if there's an army at this city's position
            army_at_city = None
            for army in self.campaign_state.armies.values():
                if army.position == city.position and army.country == self.campaign_state.current_country:
                    army_at_city = army
                    break
                    
            if army_at_city:
                actions.append({
                    'text': 'Select Army',
                    'action': 'select_army',
                    'enabled': True
                })
        
        # Add switch to army option if army is also present
        if has_army:
            actions.append({
                'text': 'Switch to Army (TAB)',
                'action': 'switch_to_army',
                'enabled': True
            })
        
        actions.append({
            'text': 'Cancel',
            'action': 'cancel',
            'enabled': True
        })
        
        return actions
    
    def _get_army_actions(self, army: Army, campaign_state: CampaignState, has_city: bool = False) -> List[Dict[str, Any]]:
        """Get available actions for an army"""
        actions = []
        
        is_player_army = army.country == campaign_state.current_country
        
        if is_player_army:
            actions.append({
                'text': 'Select Army',
                'action': 'select_army',
                'enabled': True
            })
        
        actions.append({
            'text': 'Army Information',
            'action': 'show_info',
            'enabled': True
        })
        
        # Add switch to city option if city is also present
        if has_city:
            actions.append({
                'text': 'Switch to City (TAB)',
                'action': 'switch_to_city',
                'enabled': True
            })
        
        actions.append({
            'text': 'Cancel',
            'action': 'cancel',
            'enabled': True
        })
        
        return actions
    
    def handle_click(self, x: int, y: int) -> Optional[str]:
        """Handle mouse click on menu"""
        if not self.visible:
            return None
        
        # Check if click is outside menu
        if x < self.x or x > self.x + self.width:
            self.hide()
            return None
        
        relative_y = y - self.y
        if relative_y < 0 or relative_y > len(self.options) * self.option_height:
            self.hide()
            return None
        
        # Check which option was clicked
        option_index = relative_y // self.option_height
        if 0 <= option_index < len(self.options):
            option = self.options[option_index]
            if option['enabled']:
                action = option['action']
                self.hide()
                return action
        
        return None
    
    def get_hover_option(self, x: int, y: int) -> Optional[int]:
        """Get the index of the option being hovered over"""
        if not self.visible:
            return None
        
        if x < self.x or x > self.x + self.width:
            return None
        
        relative_y = y - self.y
        if relative_y < 0 or relative_y > len(self.options) * self.option_height:
            return None
        
        return relative_y // self.option_height
    
    def render(self, screen: pygame.Surface):
        """Render the context menu"""
        if not self.visible:
            return
        
        menu_height = len(self.options) * self.option_height
        
        # Draw background
        pygame.draw.rect(screen, self.colors['background'],
                        (self.x, self.y, self.width, menu_height))
        pygame.draw.rect(screen, self.colors['border'],
                        (self.x, self.y, self.width, menu_height), 2)
        
        # Get current mouse position for hover effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_index = self.get_hover_option(mouse_x, mouse_y)
        
        # Draw options
        for i, option in enumerate(self.options):
            y_pos = self.y + i * self.option_height
            
            # Draw hover background
            if hover_index == i and option['enabled']:
                pygame.draw.rect(screen, self.colors['hover'],
                               (self.x, y_pos, self.width, self.option_height))
            
            # Draw text
            text_color = self.colors['text'] if option['enabled'] else self.colors['disabled']
            text = self.font.render(option['text'], True, text_color)
            text_rect = text.get_rect(midleft=(self.x + 10, y_pos + self.option_height // 2))
            screen.blit(text, text_rect)
            
            # Draw separator line
            if i < len(self.options) - 1:
                pygame.draw.line(screen, self.colors['border'],
                               (self.x + 5, y_pos + self.option_height),
                               (self.x + self.width - 5, y_pos + self.option_height), 1)