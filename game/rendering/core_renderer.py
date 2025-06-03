"""
Core rendering coordinator.

Orchestrates all specialized renderers and maintains the overall rendering pipeline.
Replaces the monolithic Renderer class with a clean, modular architecture.
"""
import pygame
from game.hex_utils import HexGrid
from game.hex_layout import HexLayout
from .terrain_renderer import TerrainRenderer
from .unit_renderer import UnitRenderer
from .ui_renderer import UIRenderer
from .effect_renderer import EffectRenderer


class CoreRenderer:
    """Main renderer that coordinates all specialized rendering components."""
    
    def __init__(self, screen):
        self.screen = screen
        
        # Initialize hex system
        self.hex_grid = HexGrid(hex_size=36)
        self.hex_layout = HexLayout(hex_size=36, orientation='flat')
        
        # Initialize specialized renderers
        self.terrain_renderer = TerrainRenderer(screen, self.hex_grid, self.hex_layout)
        self.unit_renderer = UnitRenderer(screen, self.hex_layout)
        self.ui_renderer = UIRenderer(screen)
        self.effect_renderer = EffectRenderer(screen, self.hex_layout)
        
        # Background color
        self.background_color = (50, 50, 50)
        
        # For compatibility with existing code
        self.tile_size = 64
        self.input_handler = None  # Will be set by main.py
    
    def render(self, game_state):
        """Main rendering pipeline."""
        # Clear screen
        self.screen.fill(self.background_color)
        
        # Update hex layout to match game state zoom
        self._update_hex_layout_for_zoom(game_state)
        
        # Render in layers (back to front)
        self.terrain_renderer.render_terrain(game_state)
        self.terrain_renderer.render_movement_indicators(game_state)
        self.effect_renderer.render_movement_paths(game_state)
        self.unit_renderer.render_castles(game_state)
        self.unit_renderer.render_units(game_state)
        self.effect_renderer.render_animations(game_state)
        self.effect_renderer.render_attack_effects(game_state)
        self.ui_renderer.render_messages(game_state)
        self.ui_renderer.render_ui(game_state)
        
        # Display the rendered frame
        pygame.display.flip()
    
    def render_debug(self, game_state, fps: float):
        """Render with debug information."""
        self.render(game_state)
        self.ui_renderer.render_debug_info(game_state, fps)
    
    def _update_hex_layout_for_zoom(self, game_state):
        """Update hex layout and hex grid from input handler (original working implementation)."""
        # Use input handler's hex layout and hex grid which include zoom scaling
        if self.input_handler and hasattr(self.input_handler, 'hex_layout'):
            if self.hex_layout.hex_size != self.input_handler.hex_layout.hex_size:
                self.hex_layout = self.input_handler.hex_layout
                self.hex_grid = self.input_handler.hex_grid
                self.terrain_renderer.hex_layout = self.hex_layout
                self.terrain_renderer.hex_grid = self.hex_grid
                self.unit_renderer.hex_layout = self.hex_layout
                self.effect_renderer.hex_layout = self.hex_layout
    
    def world_to_screen(self, world_x: float, world_y: float, game_state) -> tuple:
        """Convert world coordinates to screen coordinates."""
        if hasattr(game_state, 'camera_manager'):
            return game_state.camera_manager.world_to_screen(world_x, world_y)
        else:
            # Legacy fallback
            screen_x = (world_x - game_state.camera_x) * getattr(game_state, 'zoom_level', 1.0)
            screen_y = (world_y - game_state.camera_y) * getattr(game_state, 'zoom_level', 1.0)
            return screen_x, screen_y
    
    def screen_to_world(self, screen_x: float, screen_y: float, game_state) -> tuple:
        """Convert screen coordinates to world coordinates."""
        if hasattr(game_state, 'camera_manager'):
            return game_state.camera_manager.screen_to_world(screen_x, screen_y)
        else:
            # Legacy fallback
            zoom = getattr(game_state, 'zoom_level', 1.0)
            world_x = screen_x / zoom + game_state.camera_x
            world_y = screen_y / zoom + game_state.camera_y
            return world_x, world_y
    
    def get_hex_at_screen_position(self, screen_x: float, screen_y: float, game_state) -> tuple:
        """Get hex coordinates at screen position."""
        world_x, world_y = self.screen_to_world(screen_x, screen_y, game_state)
        return self.hex_layout.pixel_to_hex(world_x, world_y)
    
    # Legacy compatibility methods
    @property
    def hex_grid(self):
        """Legacy compatibility for hex_grid access."""
        return self._hex_grid
    
    @hex_grid.setter
    def hex_grid(self, value):
        self._hex_grid = value
    
    @property
    def hex_layout(self):
        """Legacy compatibility for hex_layout access."""
        return self._hex_layout
    
    @hex_layout.setter
    def hex_layout(self, value):
        self._hex_layout = value