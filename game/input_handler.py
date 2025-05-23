import pygame

class InputHandler:
    def __init__(self):
        self.left_click_held = False
        self.right_click_held = False
    
    def handle_event(self, event, game_state):
        if game_state.ai_thinking or game_state.animation_manager.is_animating():
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            
            if y >= pygame.display.get_surface().get_height() - 100:
                if x >= pygame.display.get_surface().get_width() - 140 and game_state.current_player == 1:
                    game_state.end_turn()
                return
            
            if event.button == 1 and game_state.current_player == 1:
                self.left_click_held = True
                
                action = game_state.context_menu.handle_click(x, y)
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
                    tile_x = x // game_state.tile_size
                    tile_y = y // game_state.tile_size
                    knight = game_state.get_knight_at(tile_x, tile_y)
                    
                    if knight and knight.player_id == game_state.current_player:
                        game_state.selected_knight = knight
                        knight.selected = True
                        game_state.context_menu.show(x, y, knight, game_state)
                    else:
                        game_state.deselect_knight()
            
            elif event.button == 3 and game_state.current_player == 1:
                self.right_click_held = True
                game_state.deselect_knight()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.left_click_held = False
            elif event.button == 3:
                self.right_click_held = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state.deselect_knight()
            elif event.key == pygame.K_SPACE and game_state.current_player == 1:
                game_state.end_turn()