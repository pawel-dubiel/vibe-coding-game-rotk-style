"""
Terrain rendering system.

Handles hex grid drawing, terrain types, fog of war overlays, and terrain assets.
Extracted from the monolithic Renderer class for better separation of concerns.
"""
import pygame
import math
from game.hex_layout import HexLayout
from game.terrain import TerrainType
from game.visibility import VisibilityState
from game.asset_manager import AssetManager


class TerrainRenderer:
    """Specialized renderer for terrain, hex grid, and fog of war."""
    
    def __init__(self, screen, hex_grid, hex_layout: HexLayout):
        self.screen = screen
        self.hex_grid = hex_grid
        self.hex_layout = hex_layout
        self.asset_manager = AssetManager()
        self.font = pygame.font.Font(None, 24)
        
        # Terrain colors
        self.terrain_colors = {
            TerrainType.PLAINS: (120, 150, 80),
            TerrainType.FOREST: (60, 120, 60),
            TerrainType.HILLS: (140, 120, 90),
            TerrainType.WATER: (80, 120, 200),
            TerrainType.BRIDGE: (139, 69, 19),
            TerrainType.SWAMP: (100, 120, 100),
            TerrainType.ROAD: (160, 140, 120),
            TerrainType.LIGHT_FOREST: (80, 140, 80),
            TerrainType.DENSE_FOREST: (40, 100, 40),
            TerrainType.HIGH_HILLS: (160, 140, 110),
            TerrainType.MOUNTAINS: (120, 100, 80),
            TerrainType.DEEP_WATER: (60, 90, 160),
            TerrainType.MARSH: (80, 100, 80),
            TerrainType.DESERT: (200, 180, 120),
            TerrainType.SNOW: (240, 240, 255)
        }
        
        # Default tile colors
        self.tile_light = (120, 100, 80)
        self.tile_dark = (100, 80, 60)
    
    def render_terrain(self, game_state):
        """Render the hex grid terrain with fog of war."""
        # Calculate visible hex range using camera manager for zoom-aware coordinates
        if hasattr(game_state, 'camera_manager'):
            camera_x = game_state.camera_manager.camera_x
            camera_y = game_state.camera_manager.camera_y
            screen_width = game_state.camera_manager.screen_width
            screen_height = game_state.camera_manager.screen_height
            zoom_level = game_state.camera_manager.zoom_level
            
            # Use scaled hex dimensions for proper culling
            hex_width = self.hex_layout.col_spacing
            hex_height = self.hex_layout.row_spacing
            
            start_col = max(0, int(camera_x / hex_width) - 1)
            end_col = min(game_state.board_width, int((camera_x + screen_width / zoom_level) / hex_width) + 2)
            start_row = max(0, int(camera_y / hex_height) - 1)
            end_row = min(game_state.board_height, int((camera_y + screen_height / zoom_level) / hex_height) + 2)
        else:
            # Legacy fallback
            start_col = max(0, int(game_state.camera_x / self.hex_grid.hex_width) - 1)
            end_col = min(game_state.board_width, int((game_state.camera_x + game_state.screen_width) / self.hex_grid.hex_width) + 2)
            start_row = max(0, int(game_state.camera_y / self.hex_grid.hex_height) - 1)
            end_row = min(game_state.board_height, int((game_state.camera_y + game_state.screen_height) / self.hex_grid.hex_height) + 2)
        
        for col in range(start_col, end_col):
            for row in range(start_row, end_row):
                self._render_hex_tile(game_state, col, row)
    
    def _render_hex_tile(self, game_state, col: int, row: int):
        """Render a single hex tile with terrain and fog."""
        # Calculate pixel position
        pixel_x, pixel_y = self.hex_layout.hex_to_pixel(col, row)
        screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
        
        # Get terrain and color
        terrain = game_state.terrain_map.get_terrain(col, row)
        color = self._get_terrain_color(terrain, col, row)
        
        # Get hex corners
        corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
        
        # Try to use asset image, fallback to colored polygon
        terrain_image = self._get_terrain_asset(terrain)
        
        if terrain_image:
            image_rect = terrain_image.get_rect(center=(int(screen_x), int(screen_y)))
            self.screen.blit(terrain_image, image_rect)
            pygame.draw.polygon(self.screen, (0, 0, 0), corners, 1)  # Black outline
        else:
            # Fallback to colored polygon
            pygame.draw.polygon(self.screen, color, corners)
            pygame.draw.polygon(self.screen, (0, 0, 0), corners, 1)  # Black outline
            
            # Add texture patterns for terrains without assets
            self._add_terrain_texture(terrain, screen_x, screen_y, corners)
        
        # Apply fog of war overlay
        self._apply_fog_overlay(game_state, col, row, screen_x, screen_y, corners)
        
        # Draw coordinate labels if enabled
        if getattr(game_state, 'show_coordinates', False):
            self._draw_coordinates(col, row, screen_x, screen_y)
    
    def _get_terrain_color(self, terrain, col: int, row: int) -> tuple:
        """Get the base color for a terrain tile."""
        if terrain:
            return self.terrain_colors.get(terrain.type, self.terrain_colors[TerrainType.PLAINS])
        else:
            # Alternating pattern for default tiles
            return self.tile_light if (col + row) % 2 == 0 else self.tile_dark
    
    def _get_terrain_asset(self, terrain):
        """Get the asset image for a terrain type."""
        if not terrain:
            return None
        
        terrain_asset_map = {
            TerrainType.WATER: "water",
            TerrainType.DEEP_WATER: "deep-water",
            TerrainType.PLAINS: "plain",
            TerrainType.HILLS: "hills",
            TerrainType.LIGHT_FOREST: "light-forrest",
            TerrainType.FOREST: "forrest",
            TerrainType.DENSE_FOREST: "dense-forrest",
            TerrainType.SWAMP: "swamp",
            TerrainType.MOUNTAINS: "mountains",
            TerrainType.HIGH_HILLS: "high-hills",
            TerrainType.SNOW: "snow",
            TerrainType.DESERT: "desert"
        }
        
        asset_name = terrain_asset_map.get(terrain.type)
        if asset_name:
            return self.asset_manager.get_terrain_image(asset_name, self.hex_grid.hex_size)
        
        return None
    
    def _add_terrain_texture(self, terrain, screen_x: float, screen_y: float, corners: list):
        """Add texture patterns for terrains without asset images."""
        if not terrain:
            return
        
        # Add small visual elements to distinguish terrain types
        if terrain.type == TerrainType.FOREST:
            # Draw small trees
            for i in range(3):
                tree_x = screen_x + (i - 1) * 10
                tree_y = screen_y + (i % 2) * 8
                pygame.draw.circle(self.screen, (40, 80, 40), (int(tree_x), int(tree_y)), 3)
        
        elif terrain.type == TerrainType.HILLS:
            # Draw hill contours
            for i in range(2):
                hill_radius = 15 + i * 5
                pygame.draw.circle(self.screen, (160, 140, 110), 
                                 (int(screen_x), int(screen_y)), hill_radius, 1)
        
        elif terrain.type == TerrainType.WATER:
            # Draw wave patterns
            for i in range(3):
                wave_y = screen_y + (i - 1) * 8
                pygame.draw.arc(self.screen, (100, 140, 220),
                              (screen_x - 15, wave_y - 3, 30, 6), 0, math.pi, 1)
        
        elif terrain.type == TerrainType.MOUNTAINS:
            # Draw mountain peaks
            peak_points = [
                (screen_x - 10, screen_y + 8),
                (screen_x - 5, screen_y - 8),
                (screen_x, screen_y + 5),
                (screen_x + 5, screen_y - 8),
                (screen_x + 10, screen_y + 8)
            ]
            pygame.draw.lines(self.screen, (100, 80, 60), False, peak_points, 2)
    
    def _apply_fog_overlay(self, game_state, col: int, row: int, screen_x: float, screen_y: float, corners: list):
        """Apply fog of war overlay based on visibility state."""
        # Check fog of war visibility
        visibility = VisibilityState.VISIBLE  # Default for no fog
        if hasattr(game_state, 'fog_of_war') and game_state.current_player is not None:
            visibility = game_state.fog_of_war.get_visibility_state(game_state.current_player, col, row)
        
        # Apply fog overlay for non-visible hexes
        if visibility != VisibilityState.VISIBLE:
            fog_surface = pygame.Surface((int(self.hex_grid.hex_width), int(self.hex_grid.hex_height)), pygame.SRCALPHA)
            
            # Different alpha values for different visibility states
            if visibility == VisibilityState.HIDDEN:
                fog_color = (40, 40, 40, 200)  # Dark grey, very opaque
            elif visibility == VisibilityState.EXPLORED:
                fog_color = (60, 60, 60, 150)  # Grey, semi-opaque
            else:  # PARTIAL
                fog_color = (80, 80, 80, 100)  # Light grey, less opaque
            
            # Draw fog polygon on the surface
            corners_relative = [(x - screen_x + self.hex_grid.hex_width/2, 
                               y - screen_y + self.hex_grid.hex_height/2) for x, y in corners]
            pygame.draw.polygon(fog_surface, fog_color, corners_relative)
            
            # Blit the fog overlay
            self.screen.blit(fog_surface, (screen_x - self.hex_grid.hex_width/2, 
                                          screen_y - self.hex_grid.hex_height/2))
    
    def _draw_coordinates(self, col: int, row: int, screen_x: float, screen_y: float):
        """Draw coordinate labels for debugging."""
        coord_text = self.font.render(f"{col},{row}", True, (100, 100, 100))
        text_rect = coord_text.get_rect(center=(int(screen_x), int(screen_y)))
        self.screen.blit(coord_text, text_rect)
    
    def render_movement_indicators(self, game_state):
        """Render movement and attack indicators on the terrain."""
        # Draw possible moves
        if hasattr(game_state, 'possible_moves') and game_state.possible_moves:
            for move_x, move_y in game_state.possible_moves:
                pixel_x, pixel_y = self.hex_layout.hex_to_pixel(move_x, move_y)
                screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
                corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
                pygame.draw.polygon(self.screen, (100, 200, 100), corners, 3)
        
        # Draw attack targets
        if hasattr(game_state, 'attack_targets') and game_state.attack_targets:
            for target in game_state.attack_targets:
                # Handle both tuple coordinates and unit objects
                if isinstance(target, tuple):
                    target_x, target_y = target
                else:
                    target_x, target_y = target.x, target.y
                
                pixel_x, pixel_y = self.hex_layout.hex_to_pixel(target_x, target_y)
                screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
                corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
                pygame.draw.polygon(self.screen, (255, 100, 100), corners, 3)
        
        # Note: Selected unit highlight is now handled by unit renderer