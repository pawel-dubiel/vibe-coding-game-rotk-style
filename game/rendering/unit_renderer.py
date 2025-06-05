"""
Unit rendering system.

Handles drawing units, health bars, facing indicators, and status effects.
Supports fog of war identification and animation integration.
"""
import pygame
import math
from game.entities.knight import KnightClass
from game.hex_layout import HexLayout
from game.visibility import VisibilityState
from game.asset_manager import AssetManager
from .unit_render_strategies import (
    ArcherRenderStrategy,
    CavalryRenderStrategy,
    MageRenderStrategy,
    UnitRenderStrategy,
    WarriorRenderStrategy,
)


class UnitRenderer:
    """Specialized renderer for units, health bars, and status indicators."""
    
    def __init__(self, screen, hex_layout: HexLayout):
        self.screen = screen
        self.hex_layout = hex_layout
        self.asset_manager = AssetManager()
        self.font = pygame.font.Font(None, 24)
        
        # Unit colors
        self.colors = {
            'player1': (100, 100, 255),
            'player2': (255, 100, 100),
            'health_bar_bg': (60, 60, 60),
            'health_bar_good': (100, 200, 100),
            'health_bar_medium': (200, 200, 100),
            'health_bar_low': (200, 100, 100),
            'morale_bar_bg': (40, 40, 40),
            'morale_bar_high': (100, 100, 255),
            'morale_bar_medium': (100, 200, 100),
            'morale_bar_low': (200, 100, 100),
            'facing_arrow': (255, 255, 255),
            'routing_indicator': (255, 200, 0),
            'disrupted_indicator': (255, 100, 0)
        }

        # Mapping of unit classes to rendering strategies
        self.unit_render_strategies: dict[KnightClass, UnitRenderStrategy] = {
            KnightClass.WARRIOR: WarriorRenderStrategy(),
            KnightClass.ARCHER: ArcherRenderStrategy(),
            KnightClass.CAVALRY: CavalryRenderStrategy(),
            KnightClass.MAGE: MageRenderStrategy(),
        }
    
    def render_units(self, game_state):
        """Render all visible units with health bars and status indicators."""
        for unit in game_state.knights:
            if self._should_render_unit(unit, game_state):
                self._render_unit(unit, game_state)
    
    def render_castles(self, game_state):
        """Render castle structures."""
        for castle in game_state.castles:
            if self._should_render_castle(castle, game_state):
                self._render_castle(castle, game_state)
    
    def _should_render_unit(self, unit, game_state) -> bool:
        """Check if unit should be rendered based on fog of war."""
        if not hasattr(game_state, 'fog_of_war') or game_state.fog_view_player is None:
            return True

        visibility = game_state.fog_of_war.get_visibility_state(game_state.fog_view_player, unit.x, unit.y)
        return visibility in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]
    
    def _should_render_castle(self, castle, game_state) -> bool:
        """Check if castle should be rendered based on fog of war."""
        if not hasattr(game_state, 'fog_of_war') or game_state.fog_view_player is None:
            return True
        
        # Check if any castle tile is visible
        for tile_x, tile_y in castle.occupied_tiles:
            visibility = game_state.fog_of_war.get_visibility_state(game_state.fog_view_player, tile_x, tile_y)
            if visibility in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                return True
        return False
    
    def _render_unit(self, unit, game_state):
        """Render a single unit with all its visual elements."""
        # Get unit position (may be animated)
        pixel_x, pixel_y = self._get_unit_render_position(unit, game_state)
        screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
        
        # Check identification status
        is_identified = self._is_unit_identified(unit, game_state)
        
        # Render unit sprite/shape
        self._render_unit_sprite(unit, screen_x, screen_y, is_identified)
        
        # Render selection indicator
        if hasattr(unit, 'selected') and unit.selected:
            pygame.draw.circle(self.screen, (255, 255, 100), (int(screen_x), int(screen_y)), 30, 3)
        
        # Render status indicators
        if is_identified:
            self._render_health_bar(unit, screen_x, screen_y)
            self._render_morale_bar(unit, screen_x, screen_y)
            self._render_facing_indicator(unit, screen_x, screen_y)
            self._render_status_effects(unit, screen_x, screen_y)
            self._render_unit_name(unit, screen_x, screen_y)
    
    def _get_unit_render_position(self, unit, game_state) -> tuple:
        """Get the rendering position for a unit, accounting for animations."""
        from game.animation import MoveAnimation, PathMoveAnimation
        
        # Default to hex grid position
        pixel_x, pixel_y = self.hex_layout.hex_to_pixel(unit.x, unit.y)
        
        # Check for move animations
        if hasattr(game_state, 'animation_coordinator'):
            for anim in game_state.animation_coordinator.animation_manager.get_current_animations():
                if (isinstance(anim, (MoveAnimation, PathMoveAnimation)) and anim.knight == unit):
                    anim_x, anim_y = anim.get_current_position()
                    pixel_x, pixel_y = self.hex_layout.hex_to_pixel(anim_x, anim_y)
                    break
        
        return pixel_x, pixel_y
    
    def _is_unit_identified(self, unit, game_state) -> bool:
        """Check if unit is fully identified (not just detected)."""
        if not hasattr(game_state, 'fog_of_war') or game_state.fog_view_player is None:
            return True

        visibility = game_state.fog_of_war.get_visibility_state(game_state.fog_view_player, unit.x, unit.y)
        return (visibility == VisibilityState.VISIBLE or unit.player_id == game_state.fog_view_player)
    
    def _render_unit_sprite(self, unit, screen_x: float, screen_y: float, is_identified: bool):
        """Render the unit sprite based on type and identification status."""
        player_color = self.colors['player1'] if unit.player_id == 1 else self.colors['player2']
        center_x, center_y = int(screen_x), int(screen_y)
        
        if not is_identified:
            # Generic unit marker for unidentified units
            pygame.draw.circle(self.screen, (128, 128, 128), (center_x, center_y), 15)
            pygame.draw.circle(self.screen, (64, 64, 64), (center_x, center_y), 15, 2)
            return
        
        strategy = self.unit_render_strategies.get(unit.unit_class)
        if strategy:
            strategy.render(self.screen, player_color, center_x, center_y)
    
    def _render_health_bar(self, unit, screen_x: float, screen_y: float):
        """Render health bar above unit."""
        bar_width = 30
        bar_height = 4
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - 35
        
        # Background
        pygame.draw.rect(self.screen, self.colors['health_bar_bg'], (bar_x, bar_y, bar_width, bar_height))
        
        # Health percentage
        health_percent = unit.health / unit.max_health if unit.max_health > 0 else 0
        fill_width = bar_width * health_percent
        
        # Health color based on percentage
        if health_percent > 0.66:
            health_color = self.colors['health_bar_good']
        elif health_percent > 0.33:
            health_color = self.colors['health_bar_medium']
        else:
            health_color = self.colors['health_bar_low']
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, fill_width, bar_height))
    
    def _render_morale_bar(self, unit, screen_x: float, screen_y: float):
        """Render morale bar below health bar."""
        bar_width = 30
        bar_height = 3
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - 30
        
        # Background
        pygame.draw.rect(self.screen, self.colors['morale_bar_bg'], (bar_x, bar_y, bar_width, bar_height))
        
        # Morale percentage
        max_morale = getattr(unit.stats.stats, 'max_morale', 100) if hasattr(unit, 'stats') else 100
        morale_percent = unit.morale / max_morale if max_morale > 0 else 0
        fill_width = bar_width * morale_percent
        
        # Morale color based on percentage
        if morale_percent > 0.75:
            morale_color = self.colors['morale_bar_high']
        elif morale_percent > 0.5:
            morale_color = self.colors['morale_bar_medium']
        else:
            morale_color = self.colors['morale_bar_low']
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, morale_color, (bar_x, bar_y, fill_width, bar_height))
    
    def _render_facing_indicator(self, unit, screen_x: float, screen_y: float):
        """Render facing direction arrow."""
        if not hasattr(unit, 'facing') or not unit.facing:
            return
        
        # Use the facing component's arrow coordinate method
        start_coords, end_coords = unit.facing.get_facing_arrow_coords(screen_x, screen_y, length=15)
        
        # Draw facing arrow
        pygame.draw.line(self.screen, self.colors['facing_arrow'], start_coords, end_coords, 2)
        
        # Calculate arrowhead points
        start_x, start_y = start_coords
        end_x, end_y = end_coords
        
        # Calculate arrow direction for arrowhead
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length > 0:
            # Normalize direction
            dx /= length
            dy /= length
            
            # Calculate arrowhead points
            head_size = 5
            head_angle = math.pi * 0.8
            
            # Rotate direction vector for arrowhead points
            cos_angle = math.cos(head_angle)
            sin_angle = math.sin(head_angle)
            
            head1_x = end_x - head_size * (dx * cos_angle - dy * sin_angle)
            head1_y = end_y - head_size * (dx * sin_angle + dy * cos_angle)
            
            head2_x = end_x - head_size * (dx * cos_angle + dy * sin_angle)
            head2_y = end_y - head_size * (-dx * sin_angle + dy * cos_angle)
            
            pygame.draw.polygon(self.screen, self.colors['facing_arrow'],
                              [(end_x, end_y), (head1_x, head1_y), (head2_x, head2_y)])
    
    def _render_status_effects(self, unit, screen_x: float, screen_y: float):
        """Render status effect indicators."""
        indicator_y = screen_y + 30
        indicator_x = screen_x - 10
        
        # Routing indicator
        if getattr(unit, 'is_routing', False):
            pygame.draw.circle(self.screen, self.colors['routing_indicator'], (indicator_x, indicator_y), 5)
            indicator_x += 12
        
        # Disrupted indicator
        if getattr(unit, 'is_disrupted', False):
            pygame.draw.circle(self.screen, self.colors['disrupted_indicator'], (indicator_x, indicator_y), 5)
            indicator_x += 12
    
    def _render_unit_name(self, unit, screen_x: float, screen_y: float):
        """Render unit name below the unit."""
        name_text = self.font.render(unit.name, True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(screen_x, screen_y + 45))
        self.screen.blit(name_text, name_rect)
    
    def _render_castle(self, castle, game_state):
        """Render a castle structure."""
        player_color = self.colors['player1'] if castle.player_id == 1 else self.colors['player2']
        
        for tile_x, tile_y in castle.occupied_tiles:
            pixel_x, pixel_y = self.hex_layout.hex_to_pixel(tile_x, tile_y)
            screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
            
            # Draw castle tile
            corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
            pygame.draw.polygon(self.screen, player_color, corners)
            pygame.draw.polygon(self.screen, (0, 0, 0), corners, 2)
            
            # Draw castle symbol
            castle_size = 20
            pygame.draw.rect(self.screen, (100, 100, 100),
                           (screen_x - castle_size//2, screen_y - castle_size//2, castle_size, castle_size))
            pygame.draw.rect(self.screen, (0, 0, 0),
                           (screen_x - castle_size//2, screen_y - castle_size//2, castle_size, castle_size), 2)
        
        # Render castle health bar
        center_pixel_x, center_pixel_y = self.hex_layout.hex_to_pixel(castle.center_x, castle.center_y)
        center_screen_x, center_screen_y = game_state.world_to_screen(center_pixel_x, center_pixel_y)
        self._render_castle_health_bar(castle, center_screen_x, center_screen_y)
    
    def _render_castle_health_bar(self, castle, screen_x: float, screen_y: float):
        """Render health bar for castle."""
        bar_width = 40
        bar_height = 6
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - 40
        
        # Background
        pygame.draw.rect(self.screen, self.colors['health_bar_bg'], (bar_x, bar_y, bar_width, bar_height))
        
        # Health percentage
        health_percent = castle.health / castle.max_health if castle.max_health > 0 else 0
        fill_width = bar_width * health_percent
        
        # Health color
        if health_percent > 0.66:
            health_color = self.colors['health_bar_good']
        elif health_percent > 0.33:
            health_color = self.colors['health_bar_medium']
        else:
            health_color = self.colors['health_bar_low']
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, fill_width, bar_height))