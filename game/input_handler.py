import pygame
from game.hex_utils import HexGrid
from game.hex_layout import HexLayout

class InputHandler:
    def __init__(self):
        self.left_click_held = False
        self.right_click_held = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.camera_drag_start_x = 0
        self.camera_drag_start_y = 0
        self.hex_grid = HexGrid(hex_size=36)  # For hex distance calculations
        self.hex_layout = HexLayout(hex_size=36, orientation='flat')  # For positioning
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
    
    def handle_event(self, event, game_state):
        if game_state.ai_thinking or game_state.animation_manager.is_animating():
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            screen_x, screen_y = pygame.mouse.get_pos()
            # Convert screen coordinates to world coordinates
            x, y = game_state.screen_to_world(screen_x, screen_y)
            
            if screen_y >= pygame.display.get_surface().get_height() - 100:
                if screen_x >= pygame.display.get_surface().get_width() - 140:
                    game_state.end_turn()
                return
            
            if event.button == 1:
                self.left_click_held = True
                
                # Context menu uses screen coordinates
                action = game_state.context_menu.handle_click(screen_x, screen_y)
                if action:
                    game_state.set_action_mode(action)
                    return
                
                if game_state.current_action == 'move':
                    move_tile_x, move_tile_y = self.hex_layout.pixel_to_hex(x, y)
                    if game_state.move_selected_knight_hex(move_tile_x, move_tile_y):
                        game_state.current_action = None
                        game_state.possible_moves = []
                elif game_state.current_action == 'attack':
                    attack_tile_x, attack_tile_y = self.hex_layout.pixel_to_hex(x, y)
                    if game_state.attack_with_selected_knight_hex(attack_tile_x, attack_tile_y):
                        game_state.current_action = None
                        game_state.attack_targets = []
                    else:
                        # Show attack failure feedback
                        target = game_state.get_knight_at(attack_tile_x, attack_tile_y)
                        if target and game_state.selected_knight:
                            # Get attack behavior to check why attack failed
                            attack_behavior = game_state.selected_knight.behaviors.get('attack')
                            if attack_behavior and hasattr(attack_behavior, 'get_attack_blocked_reason'):
                                reason = attack_behavior.get_attack_blocked_reason(game_state.selected_knight, target, game_state)
                                game_state.add_message(f"Cannot attack: {reason}", priority=1)
                            else:
                                game_state.add_message("Cannot attack target", priority=1)
                        elif not target:
                            game_state.add_message("No target at that location", priority=1)
                        else:
                            game_state.add_message("Cannot attack - no unit selected", priority=1)
                elif game_state.current_action == 'charge':
                    charge_tile_x, charge_tile_y = self.hex_layout.pixel_to_hex(x, y)
                    if game_state.charge_with_selected_knight_hex(charge_tile_x, charge_tile_y):
                        game_state.current_action = None
                        game_state.attack_targets = []
                    else:
                        # Show charge failure feedback
                        charge_info = game_state.get_charge_info_at(charge_tile_x, charge_tile_y)
                        if charge_info and not charge_info['can_charge']:
                            # Display helpful message about why charge failed
                            reason = charge_info['reason']
                            game_state.add_message(f"Cannot charge: {reason}", priority=1)
                else:
                    # Use hex layout to convert click to hex coordinates
                    tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
                    knight = game_state.get_knight_at(tile_x, tile_y)
                    
                    if knight:
                        if knight.player_id == game_state.current_player:
                            game_state.selected_knight = knight
                            knight.selected = True
                            # Context menu uses screen coordinates
                            game_state.context_menu.show(screen_x, screen_y, knight, game_state)
                            game_state.enemy_info_unit = None
                            game_state.terrain_info = None
                        else:
                            # Check if enemy unit is visible to current player
                            if game_state.fog_of_war.is_hex_visible(game_state.current_player, knight.x, knight.y):
                                # Enemy is visible - show its info
                                game_state.enemy_info_unit = knight
                                game_state.terrain_info = None
                            else:
                                # Enemy is hidden by fog - show terrain info instead
                                terrain = game_state.terrain_map.get_terrain(tile_x, tile_y)
                                if terrain:
                                    game_state.terrain_info = {
                                        'terrain': terrain,
                                        'x': tile_x,
                                        'y': tile_y
                                    }
                                else:
                                    game_state.terrain_info = None
                                game_state.enemy_info_unit = None
                            game_state.deselect_knight()
                    else:
                        # Clicked on empty terrain - show terrain info
                        terrain = game_state.terrain_map.get_terrain(tile_x, tile_y)
                        if terrain:
                            game_state.terrain_info = {
                                'terrain': terrain,
                                'x': tile_x,
                                'y': tile_y
                            }
                        else:
                            game_state.terrain_info = None
                        game_state.deselect_knight()
                        game_state.enemy_info_unit = None
            
            elif event.button == 3:  # Right mouse button for scrolling
                self.right_click_held = True
                self.drag_start_x = screen_x
                self.drag_start_y = screen_y
                self.camera_drag_start_x = game_state.camera_x
                self.camera_drag_start_y = game_state.camera_y
                # Deselect on right click
                game_state.deselect_knight()
                game_state.terrain_info = None
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.left_click_held = False
            elif event.button == 3:
                self.right_click_held = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.right_click_held:
                # Calculate drag delta
                current_x, current_y = pygame.mouse.get_pos()
                dx = self.drag_start_x - current_x
                dy = self.drag_start_y - current_y
                
                # Update camera position
                game_state.set_camera_position(
                    self.camera_drag_start_x + dx,
                    self.camera_drag_start_y + dy
                )
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state.deselect_knight()
            elif event.key == pygame.K_SPACE:
                game_state.end_turn()
            # Arrow keys for camera movement
            elif event.key == pygame.K_LEFT:
                game_state.move_camera(-100, 0)
            elif event.key == pygame.K_RIGHT:
                game_state.move_camera(100, 0)
            elif event.key == pygame.K_UP:
                game_state.move_camera(0, -100)
            elif event.key == pygame.K_DOWN:
                game_state.move_camera(0, 100)
            # WASD keys as alternative
            elif event.key == pygame.K_a:
                game_state.move_camera(-100, 0)
            elif event.key == pygame.K_d:
                game_state.move_camera(100, 0)
            elif event.key == pygame.K_w:
                game_state.move_camera(0, -100)
            elif event.key == pygame.K_s:
                game_state.move_camera(0, 100)
            # Toggle coordinate display
            elif event.key == pygame.K_c:
                game_state.show_coordinates = not game_state.show_coordinates
            # Toggle enemy movement paths
            elif event.key == pygame.K_p:
                game_state.show_enemy_paths = not game_state.show_enemy_paths
                if game_state.show_enemy_paths:
                    game_state.add_message("Enemy movement paths: ON")
                else:
                    game_state.add_message("Enemy movement paths: OFF")
            # Zoom controls with keyboard
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.zoom_in(game_state)
            elif event.key == pygame.K_MINUS:
                self.zoom_out(game_state)
        
        # Handle trackpad/mouse wheel events for zoom
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.zoom_in(game_state)
            elif event.y < 0:
                self.zoom_out(game_state)
    
    def zoom_in(self, game_state):
        """Zoom in the view"""
        old_zoom = self.zoom_level
        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
        if self.zoom_level != old_zoom:
            self.update_zoom(game_state)
    
    def zoom_out(self, game_state):
        """Zoom out the view"""
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
        if self.zoom_level != old_zoom:
            self.update_zoom(game_state)
    
    def update_zoom(self, game_state):
        """Update hex grid and layout with new zoom level"""
        new_hex_size = int(36 * self.zoom_level)
        self.hex_grid = HexGrid(hex_size=new_hex_size)
        self.hex_layout = HexLayout(hex_size=new_hex_size, orientation='flat')
        
        # Update renderer's hex grid and layout
        if hasattr(game_state, 'renderer'):
            game_state.renderer.hex_grid = self.hex_grid
            game_state.renderer.hex_layout = self.hex_layout
        
        # Update game_state's hex_layout to ensure coordinate conversion consistency
        if hasattr(game_state, 'hex_layout'):
            game_state.hex_layout = self.hex_layout
    
    def screen_to_world_zoom_aware(self, screen_x, screen_y, game_state):
        """Convert screen coordinates to world coordinates accounting for zoom"""
        # Get base world coordinates
        world_x, world_y = game_state.screen_to_world(screen_x, screen_y)
        return world_x, world_y
    
    def get_zoom_level(self):
        """Get current zoom level"""
        return self.zoom_level