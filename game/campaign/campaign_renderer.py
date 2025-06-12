import pygame
import math
from typing import Dict, Optional, Tuple
from game.campaign.campaign_state import CampaignState, Army, Country, City
from game.hex_utils import HexCoord, HexGrid
from game.hex_layout import HexLayout
from game.terrain import TerrainType


class CampaignRenderer:
    """Renders the campaign map"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Camera position for map scrolling (will be centered based on map size)
        self.camera_x = 0  # Will be set when campaign state is available
        self.camera_y = 0  # Will be set when campaign state is available
        self.zoom = 1.0
        self.initial_camera_set = False
        
        # Performance caches
        self._hex_corner_offsets = self._calculate_hex_corner_offsets()
        self._pixel_cache = {}
        self._cache_valid_for_hex_size = None
        self._terrain_color_cache = {}
        self._border_color_cache = {}
        self._text_cache = {}
        self._last_camera_state = None
        self._cached_visible_range = None
        
        # Color configuration
        self.default_colors = {
            'poland': (220, 20, 60),  # Crimson
            'holy_roman_empire': (255, 215, 0),  # Gold
            'france': (0, 0, 139),  # Dark Blue
            'england': (255, 0, 0),  # Red
            'hungary': (0, 128, 0),  # Green
            'denmark': (139, 0, 0),  # Dark Red
        }
        
        # Map background color
        self.map_color = (139, 119, 101)  # Light brown
        self.water_color = (64, 164, 223)  # Light blue
        
        # Campaign terrain colors (elevation-based classification)
        self.terrain_colors = {
            # Plains and lowlands (0-200m)
            'PLAINS': (144, 238, 144),          # Light green
            
            # Forest types
            'FOREST': (34, 139, 34),            # Forest green
            'DEEP_FOREST': (0, 100, 0),         # Dark green
            
            # Elevation-based terrain (200m+)
            'HILLS': (205, 133, 63),            # Peru/brown (200-600m)
            'MOUNTAINS': (139, 137, 137),       # Dark gray (600-2500m)
            'HIGH_MOUNTAINS': (105, 105, 105),  # Dim gray (2500m+)
            
            # Water bodies
            'WATER': (64, 164, 223),            # Light blue
            'DEEP_WATER': (25, 25, 112),        # Midnight blue
            
            # Wetlands
            'SWAMPS': (107, 142, 35),           # Olive drab
            
            # Arid regions  
            'DESERT': (238, 203, 173),          # Navajo white
            
            # Cold regions
            'SNOW': (255, 250, 250),            # Snow
            'GLACIAL': (176, 224, 230),         # Powder blue
        }
        
        # Load terrain textures if available
        self.terrain_textures = {}
        self._load_terrain_textures()
        
    def _calculate_hex_corner_offsets(self):
        """Pre-calculate hex corner offsets relative to center (flat-top hexagon)"""
        offsets = []
        angle_offset = 30  # Match HexLayout's angle offset for flat-top hexagons
        for i in range(6):
            angle_deg = 60 * i + angle_offset  # Same as HexLayout
            angle_rad = math.pi / 180 * angle_deg
            offset_x = math.cos(angle_rad)
            offset_y = math.sin(angle_rad)
            offsets.append((offset_x, offset_y))
        return offsets
        
    def set_initial_camera_position(self, campaign_state: CampaignState):
        """Set the initial camera position to center on the map"""
        if not self.initial_camera_set:
            # Get map dimensions
            map_width = campaign_state.map_width
            map_height = campaign_state.map_height
            hex_layout = campaign_state.hex_layout
            
            # Calculate the center of the map in pixel coordinates
            center_hex_x = map_width // 2
            center_hex_y = map_height // 2
            
            # Convert to pixel coordinates
            center_pixel_x, center_pixel_y = hex_layout.hex_to_pixel(center_hex_x, center_hex_y)
            
            # Center the camera on the map center
            screen_center_x = self.screen.get_width() // 2
            screen_center_y = self.screen.get_height() // 2
            
            self.camera_x = screen_center_x - center_pixel_x
            self.camera_y = screen_center_y - center_pixel_y
            
            self.initial_camera_set = True
            
            print(f"🎯 Camera centered on map: {map_width}×{map_height} hexes")
            print(f"   Center hex: ({center_hex_x}, {center_hex_y})")
            print(f"   Camera position: ({self.camera_x:.1f}, {self.camera_y:.1f})")
    
    def _get_cached_pixel_position(self, q: int, r: int, hex_layout):
        """Get pixel position with caching based on hex size"""
        if self._cache_valid_for_hex_size != hex_layout.hex_size:
            self._pixel_cache.clear()
            self._cache_valid_for_hex_size = hex_layout.hex_size
        
        key = (q, r)
        if key not in self._pixel_cache:
            self._pixel_cache[key] = hex_layout.hex_to_pixel(q, r)
        return self._pixel_cache[key]
    
    def _get_cached_terrain_colors(self, terrain_type):
        """Get terrain and border colors with caching"""
        if terrain_type not in self._terrain_color_cache:
            terrain_name = terrain_type.name if hasattr(terrain_type, 'name') else str(terrain_type)
            base_color = self.terrain_colors.get(terrain_name, self.map_color)
            border_color = tuple(int(c * 0.8) for c in base_color)
            
            self._terrain_color_cache[terrain_type] = base_color
            self._border_color_cache[terrain_type] = border_color
        
        return self._terrain_color_cache[terrain_type], self._border_color_cache[terrain_type]
    
    def _get_cached_text_surface(self, text: str, font, color):
        """Cache rendered text surfaces"""
        key = (text, id(font), color)
        if key not in self._text_cache:
            self._text_cache[key] = font.render(text, True, color)
        return self._text_cache[key]
    
    def _get_hex_corners_cached(self, center_x: float, center_y: float, hex_size: float):
        """Get hex corners using pre-calculated offsets (much faster than trig)"""
        return [(center_x + hex_size * ox, center_y + hex_size * oy) 
                for ox, oy in self._hex_corner_offsets]
    
    def _get_visible_hex_range_cached(self, campaign_state: CampaignState) -> tuple:
        """Cache visible hex range when camera hasn't moved"""
        current_state = (self.camera_x, self.camera_y, self.zoom)
        
        if self._last_camera_state != current_state:
            self._cached_visible_range = self._get_visible_hex_range(campaign_state)
            self._last_camera_state = current_state
        
        return self._cached_visible_range
    
    def _load_terrain_textures(self):
        """Load terrain texture images"""
        import os
        
        terrain_files = {
            'PLAINS': 'plain.png',
            'FOREST': 'forrest.png',  # Note: filename has double 'r'
            'DEEP_FOREST': 'dense-forrest.png',
            'HILLS': 'hills.png',
            'MOUNTAINS': 'mountains.png',
            'HIGH_MOUNTAINS': 'mountains.png',  # Reuse mountains texture for high mountains
            'WATER': 'water.png',
            'DEEP_WATER': 'deep-water.png',
            'SWAMP': 'swamp.png',
            'DESERT': 'desert.png',
            'SNOW': 'snow.png',
            'GLACIAL': 'snow.png',  # Reuse snow texture for glacial
        }
        
        assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
        
        for terrain_type, filename in terrain_files.items():
            filepath = os.path.join(assets_dir, filename)
            if os.path.exists(filepath):
                try:
                    texture = pygame.image.load(filepath)
                    # Scale texture to reasonable size for hex tiles (will be re-scaled during rendering)
                    base_hex_size = 48  # Base texture size
                    texture = pygame.transform.scale(texture, (base_hex_size * 2, base_hex_size * 2))
                    self.terrain_textures[terrain_type] = texture
                except Exception as e:
                    print(f"Failed to load texture {filename}: {e}")
        
    def render(self, campaign_state: CampaignState):
        """Render the hex-based campaign map"""
        # Set initial camera position if not done yet
        self.set_initial_camera_position(campaign_state)
        
        # Clear screen
        self.screen.fill(self.map_color)
        
        # Draw terrain first
        self._draw_terrain(campaign_state)
        
        # Draw hex grid overlay
        self._draw_hex_grid(campaign_state)
        
        # Draw cities
        for city in campaign_state.cities.values():
            self._draw_city_hex(city, campaign_state.hex_layout, campaign_state.countries)
            
        # Draw armies
        for army in campaign_state.armies.values():
            self._draw_army_hex(army, campaign_state.hex_layout, campaign_state.countries)
            
        # Draw UI overlay
        self._draw_ui_overlay(campaign_state)
        
    def _get_visible_hex_range(self, campaign_state: CampaignState) -> tuple:
        """Calculate visible hex range for performance optimization using proper hex spacing"""
        visible_margin = 50  # Reduced margin for better performance
        screen_width, screen_height = self.screen.get_size()
        hex_layout = campaign_state.hex_layout
        
        # Use proper hex spacing from layout
        col_spacing = hex_layout.col_spacing  # sqrt(3) * hex_size
        row_spacing = hex_layout.row_spacing  # 1.5 * hex_size
        
        # Calculate visible range based on camera position and proper spacing
        min_q = max(0, int((-self.camera_x - visible_margin) / col_spacing))
        max_q = min(campaign_state.map_width, int((-self.camera_x + screen_width + visible_margin) / col_spacing) + 2)
        min_r = max(0, int((-self.camera_y - visible_margin) / row_spacing))
        max_r = min(campaign_state.map_height, int((-self.camera_y + screen_height + visible_margin) / row_spacing) + 2)
        
        return min_q, max_q, min_r, max_r
    
    def _draw_hex_grid(self, campaign_state: CampaignState):
        """Draw the hex grid background"""
        hex_layout = campaign_state.hex_layout
        min_q, max_q, min_r, max_r = self._get_visible_hex_range_cached(campaign_state)
        
        for q in range(min_q, max_q):
            for r in range(min_r, max_r):
                pixel_x, pixel_y = self._get_cached_pixel_position(q, r, hex_layout)
                
                # Apply camera offset
                pixel_x += self.camera_x
                pixel_y += self.camera_y
                    
                # Get hex corners and draw outline (cached trig calculations)
                corners = self._get_hex_corners_cached(pixel_x, pixel_y, hex_layout.hex_size)
                pygame.draw.polygon(self.screen, (100, 90, 80), corners, 1)
        
    def _draw_terrain(self, campaign_state: CampaignState):
        """Draw terrain based on terrain map data"""
        hex_layout = campaign_state.hex_layout
        min_q, max_q, min_r, max_r = self._get_visible_hex_range_cached(campaign_state)
        
        # Draw terrain for visible hexes only
        for q in range(min_q, max_q):
            for r in range(min_r, max_r):
                # Get terrain type for this hex
                terrain_type = campaign_state.terrain_map.get((q, r), None)
                if terrain_type:
                    pixel_x, pixel_y = self._get_cached_pixel_position(q, r, hex_layout)
                    pixel_x += self.camera_x
                    pixel_y += self.camera_y
                        
                    # Get cached terrain colors
                    color, border_color = self._get_cached_terrain_colors(terrain_type)
                    
                    # Draw hex with cached corners
                    corners = self._get_hex_corners_cached(pixel_x, pixel_y, hex_layout.hex_size)
                    
                    # Draw hex with terrain color
                    pygame.draw.polygon(self.screen, color, corners)
                    
                    # Draw subtle border for terrain definition
                    pygame.draw.polygon(self.screen, border_color, corners, 1)
        
        
    def _draw_city_hex(self, city: City, hex_layout: HexLayout, countries: Dict):
        """Draw a city on the hex map"""
        pixel_x, pixel_y = self._get_cached_pixel_position(city.position.q, city.position.r, hex_layout)
        pixel_x += self.camera_x
        pixel_y += self.camera_y
        
        # Only draw if visible
        if (-100 < pixel_x < self.screen.get_width() + 100 and
            -100 < pixel_y < self.screen.get_height() + 100):
            
            # City hex
            corners = self._get_hex_corners_cached(pixel_x, pixel_y, hex_layout.hex_size)
            
            # Get country color
            country_obj = countries.get(city.country, None)
            if country_obj and hasattr(country_obj, 'color'):
                color = tuple(country_obj.color)
            else:
                color = self.default_colors.get(city.country, (200, 200, 200))
                
            pygame.draw.polygon(self.screen, color, corners)
            pygame.draw.polygon(self.screen, (0, 0, 0), corners, 2)
            
            # Castle icon (simplified)
            if city.castle_level > 0:
                castle_size = 8 + city.castle_level * 2
                castle_rect = pygame.Rect(pixel_x - castle_size//2, pixel_y - castle_size//2, 
                                        castle_size, castle_size)
                pygame.draw.rect(self.screen, (100, 100, 100), castle_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), castle_rect, 1)
                
            # City name (cached text rendering)
            name_surface = self._get_cached_text_surface(city.name, self.small_font, (0, 0, 0))
            name_rect = name_surface.get_rect(center=(pixel_x, pixel_y + hex_layout.hex_size + 8))
            self.screen.blit(name_surface, name_rect)
        
    def _draw_army_hex(self, army: Army, hex_layout: HexLayout, countries: Dict = None):
        """Draw an army on the hex map"""
        pixel_x, pixel_y = self._get_cached_pixel_position(army.position.q, army.position.r, hex_layout)
        pixel_x += self.camera_x
        pixel_y += self.camera_y
        
        # Only draw if visible
        if (-100 < pixel_x < self.screen.get_width() + 100 and
            -100 < pixel_y < self.screen.get_height() + 100):
            
            # Army banner
            if countries and army.country in countries:
                country_obj = countries[army.country]
                if hasattr(country_obj, 'color'):
                    color = tuple(country_obj.color)
                else:
                    color = self.default_colors.get(army.country, (128, 128, 128))
            else:
                color = self.default_colors.get(army.country, (128, 128, 128))
            
            # Draw flag shape
            flag_size = hex_layout.hex_size * 0.6
            flag_points = [
                (pixel_x - flag_size * 0.5, pixel_y - flag_size * 0.8),
                (pixel_x + flag_size * 0.5, pixel_y - flag_size * 0.8),
                (pixel_x + flag_size * 0.5, pixel_y),
                (pixel_x, pixel_y + flag_size * 0.4),
                (pixel_x - flag_size * 0.5, pixel_y)
            ]
            pygame.draw.polygon(self.screen, color, flag_points)
            pygame.draw.polygon(self.screen, (0, 0, 0), flag_points, 2)
            
            # Army size indicator (cached text rendering)
            total_units = army.knights + army.archers + army.cavalry
            size_text = str(total_units)
            text_surface = self._get_cached_text_surface(size_text, self.small_font, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(pixel_x, pixel_y - flag_size * 0.4))
            self.screen.blit(text_surface, text_rect)
    
        
    def _draw_ui_overlay(self, campaign_state: CampaignState):
        """Draw UI elements"""
        # Top bar background
        top_bar = pygame.Rect(0, 0, self.screen.get_width(), 60)
        pygame.draw.rect(self.screen, (50, 50, 50), top_bar)
        
        # Current country and turn
        current_country_obj = campaign_state.countries.get(campaign_state.current_country, None)
        country_name = current_country_obj.name if current_country_obj else campaign_state.current_country.title()
        country_text = f"Country: {country_name}"
        turn_text = f"Turn: {campaign_state.turn_number}"
        treasury_text = f"Treasury: {campaign_state.country_treasury.get(campaign_state.current_country, 0)} gold"
        
        country_surface = self._get_cached_text_surface(country_text, self.font, (255, 255, 255))
        turn_surface = self._get_cached_text_surface(turn_text, self.font, (255, 255, 255))
        treasury_surface = self._get_cached_text_surface(treasury_text, self.font, (255, 255, 255))
        
        self.screen.blit(country_surface, (10, 10))
        self.screen.blit(turn_surface, (10, 35))
        self.screen.blit(treasury_surface, (300, 10))
        
        # Map scale info (cached)
        scale_text = f"Scale: {campaign_state.hex_size_km}km/hex • Map: {campaign_state.map_width}x{campaign_state.map_height} hexes"
        scale_surface = self._get_cached_text_surface(scale_text, self.small_font, (200, 200, 200))
        self.screen.blit(scale_surface, (500, 35))
        
        # Selected army info
        if campaign_state.selected_army and campaign_state.selected_army in campaign_state.armies:
            army = campaign_state.armies[campaign_state.selected_army]
            self._draw_army_info(army)
            
        # Instructions
        instructions = [
            "Click on army to select",
            "Right-click to move",
            "ESC - Back to menu",
            "SPACE - End turn"
        ]
        
        y_offset = self.screen.get_height() - 100
        for instruction in instructions:
            inst_surface = self._get_cached_text_surface(instruction, self.small_font, (255, 255, 255))
            self.screen.blit(inst_surface, (10, y_offset))
            y_offset += 20
            
    def _draw_army_info(self, army: Army):
        """Draw selected army information"""
        # Info panel on the right
        panel_width = 200
        panel_height = 150
        panel_x = self.screen.get_width() - panel_width - 10
        panel_y = 70
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (70, 70, 70), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
        # Army details
        info_lines = [
            f"Army: {army.country.title()}",
            f"Knights: {army.knights}",
            f"Archers: {army.archers}",
            f"Cavalry: {army.cavalry}",
            f"Movement: {army.movement_points}/{army.max_movement_points}"
        ]
        
        y_offset = panel_y + 10
        for line in info_lines:
            text_surface = self._get_cached_text_surface(line, self.small_font, (255, 255, 255))
            self.screen.blit(text_surface, (panel_x + 10, y_offset))
            y_offset += 25
            
    def handle_camera_movement(self, keys):
        """Handle camera movement with arrow keys"""
        camera_speed = 10  # Increased speed for larger map
        
        if keys[pygame.K_LEFT]:
            self.camera_x += camera_speed
        if keys[pygame.K_RIGHT]:
            self.camera_x -= camera_speed
        if keys[pygame.K_UP]:
            self.camera_y += camera_speed
        if keys[pygame.K_DOWN]:
            self.camera_y -= camera_speed
            
    def screen_to_hex(self, screen_pos: Tuple[int, int], hex_layout: HexLayout) -> HexCoord:
        """Convert screen coordinates to hex coordinates"""
        world_x = screen_pos[0] - self.camera_x
        world_y = screen_pos[1] - self.camera_y
        
        # Use hex_layout to convert pixel to hex
        col, row = hex_layout.pixel_to_hex(world_x, world_y)
        return HexCoord(col, row)
    
    def hex_to_screen(self, hex_coord: HexCoord, hex_layout: HexLayout) -> Tuple[float, float]:
        """Convert hex coordinates to screen coordinates"""
        # Get world position
        world_x, world_y = hex_layout.hex_to_pixel(hex_coord.q, hex_coord.r)
        # Apply camera transform
        screen_x = world_x + self.camera_x
        screen_y = world_y + self.camera_y
        return (screen_x, screen_y)