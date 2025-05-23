import pygame

class InputHandler:
    def __init__(self):
        self.left_click_held = False
        self.right_click_held = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.camera_drag_start_x = 0
        self.camera_drag_start_y = 0
    
    def handle_event(self, event, game_state):
        if game_state.ai_thinking or game_state.animation_manager.is_animating():
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            screen_x, screen_y = pygame.mouse.get_pos()
            # Convert screen coordinates to world coordinates
            x, y = game_state.screen_to_world(screen_x, screen_y)
            
            if screen_y >= pygame.display.get_surface().get_height() - 100:
                if screen_x >= pygame.display.get_surface().get_width() - 140 and game_state.current_player == 1:
                    game_state.end_turn()
                return
            
            if event.button == 1 and game_state.current_player == 1:
                self.left_click_held = True
                
                # Context menu uses screen coordinates
                action = game_state.context_menu.handle_click(screen_x, screen_y)
                if action:
                    game_state.set_action_mode(action)
                    return
                
                if game_state.current_action == 'move':
                    if game_state.move_selected_knight(x, y):
                        game_state.current_action = None
                        game_state.possible_moves = []
                elif game_state.current_action == 'attack':
                    if game_state.attack_with_selected_knight(x, y):
                        game_state.current_action = None
                        game_state.attack_targets = []
                elif game_state.current_action == 'charge':
                    if game_state.charge_with_selected_knight(x, y):
                        game_state.current_action = None
                        game_state.attack_targets = []
                else:
                    tile_x = int(x // game_state.tile_size)
                    tile_y = int(y // game_state.tile_size)
                    knight = game_state.get_knight_at(tile_x, tile_y)
                    
                    if knight and knight.player_id == game_state.current_player:
                        game_state.selected_knight = knight
                        knight.selected = True
                        # Context menu uses screen coordinates
                        game_state.context_menu.show(screen_x, screen_y, knight, game_state)
                    else:
                        game_state.deselect_knight()
            
            elif event.button == 3:  # Right mouse button for scrolling
                self.right_click_held = True
                self.drag_start_x = screen_x
                self.drag_start_y = screen_y
                self.camera_drag_start_x = game_state.camera_x
                self.camera_drag_start_y = game_state.camera_y
                # Only deselect if player 1
                if game_state.current_player == 1:
                    game_state.deselect_knight()
        
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
            elif event.key == pygame.K_SPACE and game_state.current_player == 1:
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