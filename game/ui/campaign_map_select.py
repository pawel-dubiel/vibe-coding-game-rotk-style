import pygame
import os
import json
from typing import Optional, List, Dict


class CampaignMapSelectScreen:
    """Screen for selecting a campaign map"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.visible = False
        self.selected_map: Optional[str] = None
        self.ready = False
        
        self.colors = {
            'background': (30, 30, 30),
            'panel': (50, 50, 50),
            'button': (70, 70, 70),
            'button_hover': (100, 100, 100),
            'text': (255, 255, 255),
            'text_secondary': (180, 180, 180),
            'border': (200, 200, 200),
            'selected': (100, 150, 200)
        }
        
        # Available maps
        self.available_maps: List[Dict] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.maps_per_page = 6
        
        # Load available maps
        self._load_available_maps()
        
        # UI elements
        self._setup_ui()
    
    def _load_available_maps(self):
        """Load available campaign maps from data directory"""
        campaign_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'game', 'campaign', 'data'
        )
        
        self.available_maps = []
        
        if os.path.exists(campaign_data_dir):
            for filename in sorted(os.listdir(campaign_data_dir)):
                if filename.endswith('.json'):
                    filepath = os.path.join(campaign_data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Extract map info
                        map_info = data.get('map', {})
                        map_entry = {
                            'filename': filename,
                            'filepath': filepath,
                            'name': self._generate_map_name(filename),
                            'width': map_info.get('width', 0),
                            'height': map_info.get('height', 0),
                            'hex_size_km': map_info.get('hex_size_km', 30),
                            'cities_count': len(data.get('cities', {})),
                            'countries_count': len(data.get('countries', {}))
                        }
                        
                        self.available_maps.append(map_entry)
                        
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        print(f"Error loading map {filename}: {e}")
        
        # Add default map if no maps found
        if not self.available_maps:
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'game', 'campaign', 'data', 'medieval_europe.json'
            )
            if os.path.exists(default_path):
                try:
                    with open(default_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    map_info = data.get('map', {})
                    self.available_maps.append({
                        'filename': 'medieval_europe.json',
                        'filepath': default_path,
                        'name': 'Medieval Europe (Default)',
                        'width': map_info.get('width', 180),
                        'height': map_info.get('height', 192),
                        'hex_size_km': map_info.get('hex_size_km', 30),
                        'cities_count': len(data.get('cities', {})),
                        'countries_count': len(data.get('countries', {}))
                    })
                except Exception as e:
                    print(f"Error loading default map: {e}")
    
    def _generate_map_name(self, filename: str) -> str:
        """Generate a human-readable name from filename"""
        name = filename.replace('.json', '').replace('_', ' ')
        
        # Parse map filename format: map_WESTw_EASTe_SOUTHs_NORTHn_SIZEkm_WIDTHxHEIGHT
        if name.startswith('map '):
            parts = name.split(' ')
            if len(parts) >= 7:
                try:
                    west = parts[1].replace('w', '')
                    east = parts[2].replace('e', '')
                    south = parts[3].replace('s', '')
                    north = parts[4].replace('n', '')
                    size = parts[5].replace('km', '')
                    dimensions = parts[6]
                    
                    return f"Map {west}°W-{east}°E, {south}°S-{north}°N ({size}km/hex, {dimensions})"
                except (IndexError, ValueError):
                    pass
        
        return name.title()
    
    def _setup_ui(self):
        """Setup UI elements"""
        screen_width, screen_height = self.screen.get_size()
        
        # Panel dimensions
        self.panel_width = 800
        self.panel_height = 600
        self.panel_x = (screen_width - self.panel_width) // 2
        self.panel_y = (screen_height - self.panel_height) // 2
        
        # Button dimensions
        self.button_width = 200
        self.button_height = 40
        
        # Select button
        self.select_button = pygame.Rect(
            self.panel_x + self.panel_width - self.button_width - 20,
            self.panel_y + self.panel_height - self.button_height - 20,
            self.button_width,
            self.button_height
        )
        
        # Cancel button
        self.cancel_button = pygame.Rect(
            self.panel_x + 20,
            self.panel_y + self.panel_height - self.button_height - 20,
            self.button_width,
            self.button_height
        )
        
        # Map list area
        self.list_area = pygame.Rect(
            self.panel_x + 20,
            self.panel_y + 60,
            self.panel_width - 40,
            self.panel_height - 140
        )
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Dict]:
        """Handle events"""
        if not self.visible:
            return None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check buttons
            if self.select_button.collidepoint(mouse_pos) and self.available_maps:
                selected_map = self.available_maps[self.selected_index]
                self.selected_map = selected_map['filepath']
                self.ready = True
                return {'action': 'select_map', 'map': selected_map}
            
            elif self.cancel_button.collidepoint(mouse_pos):
                return {'action': 'cancel'}
            
            # Check map list
            elif self.list_area.collidepoint(mouse_pos):
                relative_y = mouse_pos[1] - self.list_area.y
                item_height = 80
                clicked_index = relative_y // item_height + self.scroll_offset
                
                if 0 <= clicked_index < len(self.available_maps):
                    self.selected_index = clicked_index
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return {'action': 'cancel'}
            elif event.key == pygame.K_RETURN and self.available_maps:
                selected_map = self.available_maps[self.selected_index]
                self.selected_map = selected_map['filepath']
                self.ready = True
                return {'action': 'select_map', 'map': selected_map}
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                self._ensure_visible()
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.available_maps) - 1, self.selected_index + 1)
                self._ensure_visible()
        
        elif event.type == pygame.MOUSEWHEEL:
            if self.list_area.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, min(
                    len(self.available_maps) - self.maps_per_page,
                    self.scroll_offset - event.y
                ))
        
        return None
    
    def _ensure_visible(self):
        """Ensure selected item is visible in the list"""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.maps_per_page:
            self.scroll_offset = self.selected_index - self.maps_per_page + 1
        
        self.scroll_offset = max(0, min(
            len(self.available_maps) - self.maps_per_page,
            self.scroll_offset
        ))
    
    def draw(self):
        """Draw the screen"""
        if not self.visible:
            return
        
        # Draw semi-transparent background
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill(self.colors['background'])
        self.screen.blit(overlay, (0, 0))
        
        # Draw main panel
        panel_rect = pygame.Rect(
            self.panel_x, self.panel_y,
            self.panel_width, self.panel_height
        )
        pygame.draw.rect(self.screen, self.colors['panel'], panel_rect)
        pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 3)
        
        # Draw title
        title_text = self.title_font.render("Select Campaign Map", True, self.colors['text'])
        title_rect = title_text.get_rect(center=(self.panel_x + self.panel_width // 2, self.panel_y + 30))
        self.screen.blit(title_text, title_rect)
        
        # Draw map list
        self._draw_map_list()
        
        # Draw buttons
        self._draw_buttons()
    
    def _draw_map_list(self):
        """Draw the list of available maps"""
        if not self.available_maps:
            # No maps available
            text = self.font.render("No campaign maps found", True, self.colors['text_secondary'])
            text_rect = text.get_rect(center=self.list_area.center)
            self.screen.blit(text, text_rect)
            return
        
        # Clip to list area
        pygame.draw.rect(self.screen, (40, 40, 40), self.list_area)
        pygame.draw.rect(self.screen, self.colors['border'], self.list_area, 2)
        
        # Draw visible maps
        item_height = 80
        visible_count = min(self.maps_per_page, len(self.available_maps) - self.scroll_offset)
        
        for i in range(visible_count):
            map_index = self.scroll_offset + i
            map_info = self.available_maps[map_index]
            
            item_y = self.list_area.y + i * item_height
            item_rect = pygame.Rect(self.list_area.x, item_y, self.list_area.width, item_height)
            
            # Highlight selected item
            if map_index == self.selected_index:
                pygame.draw.rect(self.screen, self.colors['selected'], item_rect)
            
            # Draw map info
            name_text = self.font.render(map_info['name'], True, self.colors['text'])
            self.screen.blit(name_text, (item_rect.x + 10, item_rect.y + 10))
            
            info_text = f"{map_info['width']}×{map_info['height']} hexes, {map_info['hex_size_km']}km/hex"
            size_text = self.small_font.render(info_text, True, self.colors['text_secondary'])
            self.screen.blit(size_text, (item_rect.x + 10, item_rect.y + 35))
            
            content_text = f"{map_info['countries_count']} countries, {map_info['cities_count']} cities"
            content_surface = self.small_font.render(content_text, True, self.colors['text_secondary'])
            self.screen.blit(content_surface, (item_rect.x + 10, item_rect.y + 55))
            
            # Draw separator
            if i < visible_count - 1:
                pygame.draw.line(
                    self.screen, self.colors['border'],
                    (item_rect.x + 5, item_rect.bottom),
                    (item_rect.right - 5, item_rect.bottom)
                )
        
        # Draw scrollbar if needed
        if len(self.available_maps) > self.maps_per_page:
            self._draw_scrollbar()
    
    def _draw_scrollbar(self):
        """Draw scrollbar for the map list"""
        scrollbar_width = 10
        scrollbar_x = self.list_area.right - scrollbar_width
        scrollbar_height = self.list_area.height
        
        # Background
        scrollbar_bg = pygame.Rect(scrollbar_x, self.list_area.y, scrollbar_width, scrollbar_height)
        pygame.draw.rect(self.screen, (60, 60, 60), scrollbar_bg)
        
        # Thumb
        total_items = len(self.available_maps)
        visible_ratio = self.maps_per_page / total_items
        thumb_height = int(scrollbar_height * visible_ratio)
        
        scroll_ratio = self.scroll_offset / (total_items - self.maps_per_page) if total_items > self.maps_per_page else 0
        thumb_y = self.list_area.y + int((scrollbar_height - thumb_height) * scroll_ratio)
        
        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
        pygame.draw.rect(self.screen, self.colors['button_hover'], thumb_rect)
    
    def _draw_buttons(self):
        """Draw action buttons"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Select button
        select_color = self.colors['button_hover'] if self.select_button.collidepoint(mouse_pos) else self.colors['button']
        select_enabled = len(self.available_maps) > 0
        if not select_enabled:
            select_color = (50, 50, 50)
        
        pygame.draw.rect(self.screen, select_color, self.select_button)
        pygame.draw.rect(self.screen, self.colors['border'], self.select_button, 2)
        
        select_text_color = self.colors['text'] if select_enabled else (100, 100, 100)
        select_text = self.font.render("Select", True, select_text_color)
        select_text_rect = select_text.get_rect(center=self.select_button.center)
        self.screen.blit(select_text, select_text_rect)
        
        # Cancel button
        cancel_color = self.colors['button_hover'] if self.cancel_button.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(self.screen, cancel_color, self.cancel_button)
        pygame.draw.rect(self.screen, self.colors['border'], self.cancel_button, 2)
        
        cancel_text = self.font.render("Cancel", True, self.colors['text'])
        cancel_text_rect = cancel_text.get_rect(center=self.cancel_button.center)
        self.screen.blit(cancel_text, cancel_text_rect)
    
    def show(self):
        """Show the screen"""
        self.visible = True
        self.ready = False
        self.selected_index = 0
        self.scroll_offset = 0
        # Reload maps in case new ones were added
        self._load_available_maps()
    
    def hide(self):
        """Hide the screen"""
        self.visible = False
    
    def get_selected_map(self) -> Optional[str]:
        """Get the selected map filepath"""
        return self.selected_map
