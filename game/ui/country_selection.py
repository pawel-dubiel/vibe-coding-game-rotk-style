import pygame
from typing import Optional, Dict, Any
import json
import os


class CountrySelectionScreen:
    """Screen for selecting a country to play in campaign mode"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 72)
        self.desc_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        
        self.visible = False
        self.selected_country = None
        self.countries = {}
        self.country_buttons = {}
        self.back_button = None
        self.start_button = None
        self.current_map_file = None  # Store the current map file
        
        # Colors
        self.colors = {
            'background': (30, 30, 30),
            'button': (70, 70, 70),
            'button_hover': (100, 100, 100),
            'button_selected': (150, 150, 50),
            'text': (255, 255, 255),
            'border': (200, 200, 200),
            'description': (200, 200, 200)
        }
        
        # Load default country data (will be updated when map is selected)
        self._load_country_data()
        self._setup_ui()
        
    def _load_country_data(self, map_file: str = None):
        """Load country data from JSON file"""
        try:
            if map_file:
                data_path = map_file
            else:
                # Fallback to default
                data_path = os.path.join(os.path.dirname(__file__), '..', 'campaign', 'data', 'medieval_europe.json')
                if not os.path.exists(data_path):
                    data_path = os.path.join(os.path.dirname(__file__), '..', 'campaign', 'medieval_europe.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.countries = data['countries']
        except FileNotFoundError:
            print("Warning: medieval_europe.json not found, using default countries")
            self.countries = {
                'poland': {
                    'name': 'Kingdom of Poland',
                    'color': [220, 20, 60],
                    'description': 'A rising power in Eastern Europe.'
                }
            }
            
    def _setup_ui(self):
        """Setup UI elements"""
        screen_width, screen_height = self.screen.get_size()
        
        # Country selection area
        countries_per_row = 3
        button_width = 250
        button_height = 200
        button_spacing = 20
        
        # Calculate layout
        total_width = countries_per_row * button_width + (countries_per_row - 1) * button_spacing
        start_x = (screen_width - total_width) // 2
        start_y = 150
        
        # Create country buttons
        country_list = list(self.countries.items())
        for i, (country_id, country_data) in enumerate(country_list):
            row = i // countries_per_row
            col = i % countries_per_row
            
            x = start_x + col * (button_width + button_spacing)
            y = start_y + row * (button_height + button_spacing)
            
            self.country_buttons[country_id] = pygame.Rect(x, y, button_width, button_height)
        
        # Control buttons
        self.back_button = pygame.Rect(50, screen_height - 80, 100, 50)
        self.start_button = pygame.Rect(screen_width - 150, screen_height - 80, 100, 50)
        
    def handle_event(self, event: pygame.event.Event) -> Optional[Dict[str, Any]]:
        """Handle screen events"""
        if not self.visible:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check country buttons
            for country_id, rect in self.country_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_country = country_id
                    return None
            
            # Check control buttons
            if self.back_button.collidepoint(mouse_pos):
                return {'action': 'back'}
            
            if self.start_button.collidepoint(mouse_pos) and self.selected_country:
                return {
                    'action': 'start_campaign',
                    'country': self.selected_country,
                    'country_data': self.countries[self.selected_country]
                }
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return {'action': 'back'}
            elif event.key == pygame.K_RETURN and self.selected_country:
                return {
                    'action': 'start_campaign',
                    'country': self.selected_country,
                    'country_data': self.countries[self.selected_country]
                }
        
        return None
    
    def draw(self):
        """Draw the country selection screen"""
        if not self.visible:
            return
            
        # Clear screen
        self.screen.fill(self.colors['background'])
        
        # Draw title
        title_text = self.title_font.render("Choose Your Kingdom", True, self.colors['text'])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw country buttons
        mouse_pos = pygame.mouse.get_pos()
        
        for country_id, rect in self.country_buttons.items():
            country_data = self.countries[country_id]
            
            # Determine button color
            if country_id == self.selected_country:
                color = self.colors['button_selected']
            elif rect.collidepoint(mouse_pos):
                color = self.colors['button_hover']
            else:
                color = self.colors['button']
            
            # Draw button background
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.colors['border'], rect, 3)
            
            # Draw country flag/color
            flag_rect = pygame.Rect(rect.x + 10, rect.y + 10, 30, 20)
            flag_color = tuple(country_data['color'])
            pygame.draw.rect(self.screen, flag_color, flag_rect)
            pygame.draw.rect(self.screen, self.colors['border'], flag_rect, 2)
            
            # Draw country name
            name_surface = self.font.render(country_data['name'], True, self.colors['text'])
            name_rect = name_surface.get_rect(centerx=rect.centerx, y=rect.y + 45)
            self.screen.blit(name_surface, name_rect)
            
            # Draw description
            desc_lines = self._wrap_text(country_data.get('description', ''), rect.width - 20)
            y_offset = rect.y + 80
            for line in desc_lines:
                line_surface = self.desc_font.render(line, True, self.colors['description'])
                line_rect = line_surface.get_rect(centerx=rect.centerx, y=y_offset)
                self.screen.blit(line_surface, line_rect)
                y_offset += 25
            
            # Draw starting resources if selected
            if country_id == self.selected_country:
                self._draw_country_details(rect, country_data)
        
        # Draw control buttons
        self._draw_button(self.back_button, "Back", mouse_pos)
        
        # Start button (only enabled if country selected)
        start_enabled = self.selected_country is not None
        self._draw_button(self.start_button, "Start", mouse_pos, enabled=start_enabled)
        
        # Draw instructions
        if not self.selected_country:
            instruction_text = "Select a kingdom to see details and start your campaign"
            instruction_surface = self.desc_font.render(instruction_text, True, self.colors['description'])
            instruction_rect = instruction_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 120))
            self.screen.blit(instruction_surface, instruction_rect)
    
    def _draw_country_details(self, rect: pygame.Rect, country_data: Dict[str, Any]):
        """Draw detailed country information"""
        # Draw a details panel to the side or overlay
        details_x = rect.right + 20
        details_y = rect.y
        details_width = 200
        details_height = rect.height
        
        # Adjust if panel would go off screen
        if details_x + details_width > self.screen.get_width():
            details_x = rect.x - details_width - 20
        
        # Draw details background
        details_rect = pygame.Rect(details_x, details_y, details_width, details_height)
        pygame.draw.rect(self.screen, (50, 50, 50), details_rect)
        pygame.draw.rect(self.screen, self.colors['border'], details_rect, 2)
        
        # Draw starting resources
        y_offset = details_y + 10
        title_surface = self.small_font.render("Starting Forces:", True, self.colors['text'])
        self.screen.blit(title_surface, (details_x + 10, y_offset))
        y_offset += 25
        
        if 'starting_resources' in country_data:
            resources = country_data['starting_resources']
            
            # Gold
            if 'gold' in resources:
                gold_text = f"Gold: {resources['gold']}"
                gold_surface = self.small_font.render(gold_text, True, (255, 215, 0))
                self.screen.blit(gold_surface, (details_x + 10, y_offset))
                y_offset += 20
            
            # Army units
            if 'army_units' in resources:
                units = resources['army_units']
                for unit_type, count in units.items():
                    unit_text = f"{unit_type.title()}: {count}"
                    unit_surface = self.small_font.render(unit_text, True, self.colors['text'])
                    self.screen.blit(unit_surface, (details_x + 10, y_offset))
                    y_offset += 20
    
    def _draw_button(self, rect: pygame.Rect, text: str, mouse_pos: tuple, enabled: bool = True):
        """Draw a button"""
        if enabled:
            if rect.collidepoint(mouse_pos):
                color = self.colors['button_hover']
            else:
                color = self.colors['button']
            text_color = self.colors['text']
        else:
            color = (50, 50, 50)
            text_color = (128, 128, 128)
        
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.colors['border'], rect, 2)
        
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _wrap_text(self, text: str, max_width: int) -> list:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.desc_font.render(test_line, True, self.colors['text'])
            
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def show(self):
        """Show the country selection screen"""
        self.visible = True
        self.selected_country = None
    
    def hide(self):
        """Hide the country selection screen"""
        self.visible = False
        self.selected_country = None
    
    def set_map_file(self, map_file: str):
        """Set the map file and reload countries"""
        self.current_map_file = map_file
        self._load_country_data(map_file)
        self._setup_ui()  # Rebuild UI with new countries
        self.selected_country = None  # Reset selection