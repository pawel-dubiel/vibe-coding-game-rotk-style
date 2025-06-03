"""
UI rendering system.

Handles HUD elements, turn counter, unit info panels, and context menus.
Extracted from the monolithic Renderer class for better organization.
"""
import pygame


class UIRenderer:
    """Specialized renderer for user interface elements."""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.ui_font = pygame.font.Font(None, 32)
        
        self.colors = {
            'ui_bg': (80, 80, 80),
            'text': (255, 255, 255),
            'message_bg': (50, 50, 50, 180),
            'button_bg': (100, 100, 100),
            'button_hover': (120, 120, 120),
            'health_good': (100, 200, 100),
            'health_medium': (200, 200, 100),
            'health_low': (200, 100, 100),
            'enemy_text': (255, 200, 200)
        }
    
    def render_ui(self, game_state):
        """Render all UI elements."""
        self._render_turn_counter(game_state)
        self._render_ui_bar(game_state)
        self._render_selected_unit_info(game_state)
        self._render_enemy_unit_info(game_state)
        self._render_terrain_info(game_state)
        self._render_context_menu(game_state)
        self._render_end_turn_button(game_state)
        self._render_victory_message(game_state)
        self._render_castle_info(game_state)
    
    def render_messages(self, game_state):
        """Render game messages with priority-based display."""
        if hasattr(game_state, 'message_system'):
            messages = game_state.message_system.get_recent_messages(5)
        else:
            # Legacy fallback
            messages = [msg for msg, _, _ in getattr(game_state, 'messages', [])][:5]
        
        if not messages:
            return
        
        # Create semi-transparent background
        message_height = len(messages) * 25 + 10
        message_surface = pygame.Surface((400, message_height), pygame.SRCALPHA)
        message_surface.fill(self.colors['message_bg'])
        
        # Draw messages
        for i, message in enumerate(messages):
            text = self.font.render(message, True, self.colors['text'])
            message_surface.blit(text, (10, 5 + i * 25))
        
        # Position at top-right of screen
        message_x = self.screen.get_width() - 410
        message_y = 60
        self.screen.blit(message_surface, (message_x, message_y))
    
    def _render_turn_counter(self, game_state):
        """Render turn counter at top of screen."""
        turn_bg = pygame.Rect(self.screen.get_width() // 2 - 100, 10, 200, 40)
        pygame.draw.rect(self.screen, self.colors['ui_bg'], turn_bg)
        pygame.draw.rect(self.screen, self.colors['text'], turn_bg, 2)
        
        turn_text = self.ui_font.render(f"Turn {game_state.turn_number}", True, self.colors['text'])
        turn_rect = turn_text.get_rect(center=turn_bg.center)
        self.screen.blit(turn_text, turn_rect)
    
    def _render_ui_bar(self, game_state):
        """Render bottom UI bar with player info."""
        ui_height = 100
        ui_y = self.screen.get_height() - ui_height
        pygame.draw.rect(self.screen, self.colors['ui_bg'],
                        (0, ui_y, self.screen.get_width(), ui_height))
        
        # Current player info
        if game_state.vs_ai:
            if game_state.current_player == 1:
                player_info = "Player 1 (Human)"
            else:
                player_info = "Player 2 (AI)" + (" - Thinking..." if game_state.ai_thinking else "")
        else:
            player_info = f"Player {game_state.current_player} (Human)"
        
        player_text = self.ui_font.render(player_info, True, self.colors['text'])
        self.screen.blit(player_text, (20, ui_y + 10))
        
        # Action mode indicator
        if hasattr(game_state, 'current_action') and game_state.current_action:
            action_text = self.font.render(f"Mode: {game_state.current_action.title()}", True, self.colors['text'])
            self.screen.blit(action_text, (20, ui_y + 40))
    
    def _render_selected_unit_info(self, game_state):
        """Render info panel for selected unit."""
        if not hasattr(game_state, 'selected_knight') or not game_state.selected_knight:
            return
        
        unit = game_state.selected_knight
        ui_y = self.screen.get_height() - 100
        
        # Get terrain and status info
        terrain = game_state.terrain_map.get_terrain(unit.x, unit.y) if not unit.is_garrisoned else None
        terrain_str = f" - Terrain: {terrain.type.value}" if terrain else ""
        garrison_str = " - GARRISONED" if getattr(unit, 'is_garrisoned', False) else ""
        
        status_str = ""
        if getattr(unit, 'is_routing', False):
            status_str = " - ROUTING!"
        elif getattr(unit, 'is_disrupted', False):
            status_str = " - DISRUPTED"
        elif getattr(unit, 'in_enemy_zoc', False):
            status_str = " - ENGAGED"
        
        # Main unit info
        info_text = self.font.render(
            f"{unit.name} ({unit.unit_class.value}) - "
            f"Soldiers: {unit.health}/{unit.max_health} - "
            f"Morale: {int(unit.morale)}% - "
            f"Will: {int(unit.will)}% - "
            f"AP: {unit.action_points}/{unit.max_action_points}"
            f"{terrain_str}{garrison_str}{status_str}",
            True, self.colors['text']
        )
        self.screen.blit(info_text, (20, ui_y + 60))
        
        # Generals info
        if hasattr(unit, 'generals') and unit.generals and unit.generals.generals:
            generals_info = f"Generals: {', '.join([g.name for g in unit.generals.generals])}"
            generals_text = self.font.render(generals_info, True, self.colors['text'])
            self.screen.blit(generals_text, (20, ui_y + 80))
    
    def _render_enemy_unit_info(self, game_state):
        """Render info for enemy unit under cursor."""
        if not hasattr(game_state, 'enemy_info_unit') or not game_state.enemy_info_unit:
            return
        
        enemy = game_state.enemy_info_unit
        
        # Create info panel
        info_lines = [
            f"Enemy: {enemy.name} ({enemy.unit_class.value})",
            f"Soldiers: {enemy.health}/{enemy.max_health}",
            f"Morale: {int(enemy.morale)}%"
        ]
        
        # Add status info
        if getattr(enemy, 'is_routing', False):
            info_lines.append("Status: ROUTING")
        elif getattr(enemy, 'is_disrupted', False):
            info_lines.append("Status: DISRUPTED")
        
        # Calculate panel size
        panel_width = 250
        panel_height = len(info_lines) * 25 + 20
        
        # Position panel near cursor (simplified - could use mouse position)
        panel_x = self.screen.get_width() - panel_width - 20
        panel_y = 100
        
        # Draw panel background
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.colors['message_bg'])
        
        # Draw info lines
        for i, line in enumerate(info_lines):
            text = self.font.render(line, True, self.colors['enemy_text'])
            panel_surface.blit(text, (10, 10 + i * 25))
        
        self.screen.blit(panel_surface, (panel_x, panel_y))
    
    def _render_terrain_info(self, game_state):
        """Render terrain info for tile under cursor."""
        if not hasattr(game_state, 'terrain_info') or not game_state.terrain_info:
            return
        
        terrain_info = game_state.terrain_info
        
        # Extract terrain object and position info
        if isinstance(terrain_info, dict) and 'terrain' in terrain_info:
            terrain = terrain_info['terrain']
            tile_x = terrain_info.get('x', '?')
            tile_y = terrain_info.get('y', '?')
            
            # Get terrain details
            terrain_type = terrain.type.value if hasattr(terrain.type, 'value') else str(terrain.type)
            terrain_cost = f"{terrain.movement_cost:.1f}"
            elevation = getattr(terrain, 'elevation', 1)
            defense_bonus = getattr(terrain, 'defense_bonus', 0)
            
            # Create detailed terrain info
            info_lines = [
                f"Terrain: {terrain_type} ({tile_x}, {tile_y})",
                f"Movement Cost: {terrain_cost}",
                f"Elevation: {elevation}, Defense: +{defense_bonus}"
            ]
            info_text = " | ".join(info_lines)
        else:
            # Fallback for unexpected format
            info_text = f"Terrain: {str(terrain_info)}"
        text_surface = self.font.render(info_text, True, self.colors['text'])
        
        # Position at bottom right
        text_x = self.screen.get_width() - text_surface.get_width() - 20
        text_y = self.screen.get_height() - 120
        
        # Background
        bg_rect = text_surface.get_rect()
        bg_rect.x = text_x - 5
        bg_rect.y = text_y - 5
        bg_rect.width += 10
        bg_rect.height += 10
        
        pygame.draw.rect(self.screen, self.colors['ui_bg'], bg_rect)
        pygame.draw.rect(self.screen, self.colors['text'], bg_rect, 1)
        
        self.screen.blit(text_surface, (text_x, text_y))
    
    def _render_context_menu(self, game_state):
        """Render context menu if visible."""
        if not hasattr(game_state, 'context_menu') or not game_state.context_menu.visible:
            return
        
        menu = game_state.context_menu
        
        # Calculate menu size
        menu_width = 150
        item_height = 30
        menu_height = len(menu.options) * item_height
        
        # Draw menu background
        menu_rect = pygame.Rect(menu.x, menu.y, menu_width, menu_height)
        pygame.draw.rect(self.screen, self.colors['ui_bg'], menu_rect)
        pygame.draw.rect(self.screen, self.colors['text'], menu_rect, 2)
        
        # Draw menu items
        for i, option in enumerate(menu.options):
            item_rect = pygame.Rect(menu.x, menu.y + i * item_height, menu_width, item_height)
            
            # Highlight hovered item
            if hasattr(menu, 'selected_option') and i == menu.selected_option:
                pygame.draw.rect(self.screen, self.colors['button_hover'], item_rect)
            
            # Draw item text
            if isinstance(option, dict):
                option_text = option.get('text', 'Unknown')
                text_color = self.colors['text'] if option.get('enabled', True) else (128, 128, 128)
            else:
                option_text = str(option) if option is not None else "Unknown"
                text_color = self.colors['text']
            
            text_surface = self.font.render(option_text, True, text_color)
            text_rect = text_surface.get_rect(center=item_rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def render_debug_info(self, game_state, fps: float):
        """Render debug information."""
        debug_lines = [
            f"FPS: {fps:.1f}",
            f"Camera: ({game_state.camera_x:.1f}, {game_state.camera_y:.1f})",
            f"Units: {len(game_state.knights)}",
            f"Castles: {len(game_state.castles)}"
        ]
        
        if hasattr(game_state, 'animation_coordinator'):
            active_anims = game_state.animation_coordinator.get_active_animation_count()
            debug_lines.append(f"Animations: {active_anims}")
        
        # Draw debug info at top-left
        for i, line in enumerate(debug_lines):
            text = self.font.render(line, True, self.colors['text'])
            self.screen.blit(text, (10, 10 + i * 20))
    
    def _render_end_turn_button(self, game_state):
        """Render the end turn button."""
        ui_height = 100
        ui_y = self.screen.get_height() - ui_height
        
        # End turn button
        end_turn_rect = pygame.Rect(self.screen.get_width() - 140, ui_y + 20, 120, 40)
        pygame.draw.rect(self.screen, self.colors['button_bg'], end_turn_rect)
        pygame.draw.rect(self.screen, self.colors['text'], end_turn_rect, 2)
        
        end_turn_text = self.font.render("End Turn", True, self.colors['text'])
        text_rect = end_turn_text.get_rect(center=end_turn_rect.center)
        self.screen.blit(end_turn_text, text_rect)
        
        # Store button rect for click detection (could be used by input handler)
        if not hasattr(game_state, 'ui_buttons'):
            game_state.ui_buttons = {}
        game_state.ui_buttons['end_turn'] = end_turn_rect
    
    def _render_victory_message(self, game_state):
        """Render victory message if game is won."""
        victory = game_state.check_victory()
        if victory:
            ui_height = 100
            ui_y = self.screen.get_height() - ui_height
            
            victory_text = self.ui_font.render(f"Player {victory} Wins!", True, self.colors['text'])
            text_rect = victory_text.get_rect(center=(self.screen.get_width() // 2, ui_y + 50))
            self.screen.blit(victory_text, text_rect)
    
    def _render_castle_info(self, game_state):
        """Render castle information for current player."""
        ui_height = 100
        ui_y = self.screen.get_height() - ui_height
        
        # Find current player's castle
        player_castle = None
        for castle in game_state.castles:
            if castle.player_id == game_state.current_player:
                player_castle = castle
                break
        
        if player_castle:
            # Castle garrison info
            garrison_count = len(player_castle.garrisoned_units)
            garrison_info = f"Garrison: {garrison_count}/{player_castle.garrison_slots}"
            
            # Count archers in garrison
            archer_count = 0
            for unit in player_castle.garrisoned_units:
                if hasattr(unit, 'unit_class') and 'archer' in unit.unit_class.value.lower():
                    archer_count += 1
            
            # Count enemies in range
            enemies_near = len(player_castle.get_enemies_in_range(game_state.knights))
            
            castle_text = self.font.render(
                f"Castle - HP: {player_castle.health}/{player_castle.max_health} - "
                f"{garrison_info} - Archers: {archer_count} - Enemies in range: {enemies_near}",
                True, self.colors['text']
            )
            
            # Position below other UI elements
            castle_y = ui_y + 80 if (game_state.selected_knight or 
                                   getattr(game_state, 'enemy_info_unit', None) or 
                                   getattr(game_state, 'terrain_info', None)) else ui_y + 60
            self.screen.blit(castle_text, (20, castle_y))