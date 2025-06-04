"""
Effect rendering system.

Handles animations, particles, special effects, and movement paths.
Extracted from the monolithic Renderer class for better organization.
"""
import pygame
import math
from game.hex_layout import HexLayout


class EffectRenderer:
    """Specialized renderer for animations and visual effects."""
    
    def __init__(self, screen, hex_layout: HexLayout):
        self.screen = screen
        self.hex_layout = hex_layout
        
        self.colors = {
            'path_color': (255, 255, 100),
            'enemy_path_color': (255, 150, 150),
            'attack_flash': (255, 255, 255),
            'arrow_color': (139, 69, 19),
            'explosion_color': (255, 100, 100),
            'heal_color': (100, 255, 100),
            'charge_trail': (255, 200, 100)
        }
    
    def render_animations(self, game_state):
        """Render all active animations."""
        if not hasattr(game_state, 'animation_coordinator'):
            return
        
        # Animations are handled by the unit renderer for positioning
        # This handles special effect overlays
        self._render_animation_effects(game_state)
    
    def render_movement_paths(self, game_state):
        """Render movement history paths for units."""
        if not hasattr(game_state, 'movement_history'):
            return
        
        # Draw movement paths for visibility
        for unit_id, path in game_state.movement_history.items():
            if len(path) < 2:
                continue
            
            # Find the unit to determine if it's enemy or friendly
            unit = self._find_unit_by_id(game_state, unit_id)
            if not unit:
                continue
            
            # Choose path color based on player
            if unit.player_id == game_state.current_player:
                path_color = self.colors['path_color']
            else:
                # Only show enemy paths if enabled
                if not getattr(game_state, 'show_enemy_paths', True):
                    continue
                path_color = self.colors['enemy_path_color']
            
            self._draw_movement_path(game_state, path, path_color)
    
    def render_attack_effects(self, game_state):
        """Render attack-related visual effects."""
        # This could include muzzle flashes, impact effects, etc.
        # For now, this is handled by the animation system
        pass
    
    def render_charge_effects(self, game_state):
        """Render cavalry charge trail effects."""
        # Could add dust clouds, charge trails, etc.
        pass
    
    def _render_animation_effects(self, game_state):
        """Render special effects for active animations."""
        if not hasattr(game_state, 'animation_coordinator'):
            return
        
        for anim in game_state.animation_coordinator.animation_manager.get_current_animations():
            self._render_animation_effect(game_state, anim)
    
    def _render_animation_effect(self, game_state, animation):
        """Render special effect for a specific animation."""
        from game.animation import AttackAnimation, ArrowAnimation, MoveAnimation
        
        if isinstance(animation, AttackAnimation):
            self._render_attack_effect(game_state, animation)
        elif isinstance(animation, ArrowAnimation):
            self._render_arrow_effect(game_state, animation)
        elif isinstance(animation, MoveAnimation):
            self._render_movement_effect(game_state, animation)
    
    def _render_attack_effect(self, game_state, animation):
        """Render attack animation effects (flashes, impacts)."""
        progress = animation.progress if hasattr(animation, 'progress') else animation.get_progress()

        if animation.is_ranged:
            arrow_pos = animation.get_current_arrow_position()
            if arrow_pos:
                arrow_pixel_x, arrow_pixel_y = self.hex_layout.hex_to_pixel(arrow_pos[0], arrow_pos[1])
                arrow_screen_x, arrow_screen_y = game_state.world_to_screen(arrow_pixel_x, arrow_pixel_y)

                start_pixel_x, start_pixel_y = self.hex_layout.hex_to_pixel(animation.attacker.x, animation.attacker.y)
                start_screen_x, start_screen_y = game_state.world_to_screen(start_pixel_x, start_pixel_y)

                dx = arrow_screen_x - start_screen_x
                dy = arrow_screen_y - start_screen_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    dx /= distance
                    dy /= distance
                    arrow_length = 10
                    arrow_end_x = arrow_screen_x + dx * arrow_length
                    arrow_end_y = arrow_screen_y + dy * arrow_length
                    pygame.draw.line(self.screen, self.colors['arrow_color'],
                                     (arrow_screen_x, arrow_screen_y),
                                     (arrow_end_x, arrow_end_y), 3)

        # Flash effect when attack lands
        if 0.45 <= progress <= 0.55:
            # Flash the target area
            target_pixel_x, target_pixel_y = self.hex_layout.hex_to_pixel(animation.target.x, animation.target.y)
            target_screen_x, target_screen_y = game_state.world_to_screen(target_pixel_x, target_pixel_y)

            flash_radius = 30
            flash_surface = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            flash_alpha = int(255 * (1.0 - abs(progress - 0.5) * 4))  # Peak at 0.5
            
            pygame.draw.circle(flash_surface, (*self.colors['attack_flash'], flash_alpha),
                             (flash_radius, flash_radius), flash_radius)
            
            self.screen.blit(flash_surface, (target_screen_x - flash_radius, target_screen_y - flash_radius))
    
    def _render_arrow_effect(self, game_state, animation):
        """Render arrow animation with projectile trail."""
        if not hasattr(animation, 'get_current_arrow_position'):
            return
        
        # Get arrow position
        arrow_pos = animation.get_current_arrow_position()
        if not arrow_pos:
            return
        
        arrow_pixel_x, arrow_pixel_y = self.hex_layout.hex_to_pixel(arrow_pos[0], arrow_pos[1])
        arrow_screen_x, arrow_screen_y = game_state.world_to_screen(arrow_pixel_x, arrow_pixel_y)
        
        # Draw arrow as a small line with direction
        start_pixel_x, start_pixel_y = self.hex_layout.hex_to_pixel(animation.archer.x, animation.archer.y)
        start_screen_x, start_screen_y = game_state.world_to_screen(start_pixel_x, start_pixel_y)
        
        # Calculate arrow direction
        dx = arrow_screen_x - start_screen_x
        dy = arrow_screen_y - start_screen_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Draw arrow as a line
            arrow_length = 10
            arrow_end_x = arrow_screen_x + dx * arrow_length
            arrow_end_y = arrow_screen_y + dy * arrow_length
            
            pygame.draw.line(self.screen, self.colors['arrow_color'],
                           (arrow_screen_x, arrow_screen_y),
                           (arrow_end_x, arrow_end_y), 3)
    
    def _render_movement_effect(self, game_state, animation):
        """Render movement animation effects (dust clouds, etc.)."""
        # Could add dust trails for moving units
        pass
    
    def _draw_movement_path(self, game_state, path: list, color: tuple):
        """Draw a dotted line path between positions."""
        if len(path) < 2:
            return
        
        screen_points = []
        for x, y in path:
            pixel_x, pixel_y = self.hex_layout.hex_to_pixel(x, y)
            screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
            screen_points.append((screen_x, screen_y))
        
        # Draw dotted line between points
        for i in range(len(screen_points) - 1):
            self._draw_dotted_line(
                self.screen,
                screen_points[i],
                screen_points[i + 1],
                color,
                width=2,
                dash_length=8
            )
    
    def _draw_dotted_line(self, surface, start_pos, end_pos, color, width=1, dash_length=5):
        """Draw a dotted line between two points."""
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate total distance and direction
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return
        
        # Normalize direction
        dx /= distance
        dy /= distance
        
        # Draw dashes
        current_distance = 0
        while current_distance < distance:
            # Start of dash
            start_x = x1 + dx * current_distance
            start_y = y1 + dy * current_distance
            
            # End of dash
            end_distance = min(current_distance + dash_length, distance)
            end_x = x1 + dx * end_distance
            end_y = y1 + dy * end_distance
            
            # Draw dash
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)
            
            # Move to next dash (skip gap)
            current_distance += dash_length * 2
    
    def _find_unit_by_id(self, game_state, unit_id: int):
        """Find a unit by its id() value."""
        for unit in game_state.knights:
            if id(unit) == unit_id:
                return unit
        return None
    
    def render_targeting_indicators(self, game_state):
        """Render targeting lines and range indicators."""
        # Could add range circles, targeting lines, etc.
        pass
    
    def render_area_effects(self, game_state):
        """Render area of effect indicators and animations."""
        # Could add spell effects, explosions, etc.
        pass