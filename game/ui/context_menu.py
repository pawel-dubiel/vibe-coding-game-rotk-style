import pygame

class ContextMenu:
    def __init__(self):
        self.visible = False
        self.x = 0
        self.y = 0
        self.options = []
        self.selected_option = None
        self.target_knight = None
        
        self.width = 150
        self.option_height = 30
        self.font = pygame.font.Font(None, 20)
        
        self.colors = {
            'background': (60, 60, 60),
            'hover': (80, 80, 80),
            'text': (255, 255, 255),
            'disabled': (100, 100, 100),
            'border': (100, 100, 100)
        }
    
    def show(self, x, y, knight, game_state):
        self.visible = True
        self.x = x
        self.y = y
        self.target_knight = knight
        self.options = self._get_available_actions(knight, game_state)
        
        screen_height = pygame.display.get_surface().get_height()
        menu_height = len(self.options) * self.option_height
        if self.y + menu_height > screen_height - 100:
            self.y = screen_height - 100 - menu_height
    
    def hide(self):
        self.visible = False
        self.selected_option = None
        self.target_knight = None
    
    def _get_available_actions(self, knight, game_state):
        actions = []
        
        # Check if unit is garrisoned
        if knight.is_garrisoned:
            actions.append({
                'text': 'Exit Garrison',
                'action': 'exit_garrison',
                'enabled': True
            })
        else:
            # Check if near friendly castle
            castle = self._get_nearby_castle(knight, game_state)
            if castle and castle.player_id == knight.player_id and len(castle.garrisoned_units) < castle.garrison_slots:
                actions.append({
                    'text': 'Enter Garrison',
                    'action': 'enter_garrison',
                    'enabled': True
                })
            
            if knight.can_move():
                actions.append({
                    'text': f'Move (1 AP)',
                    'action': 'move',
                    'enabled': True
                })
            else:
                actions.append({
                    'text': f'Move (1 AP)',
                    'action': 'move',
                    'enabled': False
                })
            
            if knight.can_attack():
                actions.append({
                    'text': f'Attack (2 AP)',
                    'action': 'attack',
                    'enabled': True
                })
            else:
                actions.append({
                    'text': f'Attack (2 AP)',
                    'action': 'attack',
                    'enabled': False
                })
            
            # Add cavalry charge option
            if knight.knight_class.value == "Cavalry":
                if knight.will >= 40 and not knight.has_used_special:
                    actions.append({
                        'text': f'Charge (40 Will)',
                        'action': 'charge',
                        'enabled': True
                    })
                else:
                    actions.append({
                        'text': f'Charge (40 Will)',
                        'action': 'charge',
                        'enabled': False
                    })
            
            # Add rotation options
            if hasattr(knight, 'behaviors') and 'rotate' in knight.behaviors:
                rotate_behavior = knight.behaviors['rotate']
                if rotate_behavior.can_execute(knight, game_state):
                    ap_cost = rotate_behavior.get_ap_cost(knight, game_state)
                    rotation_options = rotate_behavior.get_rotation_options(knight)
                    
                    for action_id, text, direction in rotation_options:
                        actions.append({
                            'text': f'{text} ({ap_cost} AP)',
                            'action': action_id,
                            'enabled': True,
                            'data': direction  # Store rotation direction
                        })
                else:
                    # Show disabled if can't rotate
                    actions.append({
                        'text': f'Rotate (In Combat)',
                        'action': 'rotate_disabled',
                        'enabled': False
                    })
        
        actions.append({
            'text': 'Info',
            'action': 'info',
            'enabled': True
        })
        
        actions.append({
            'text': 'Cancel',
            'action': 'cancel',
            'enabled': True
        })
        
        return actions
    
    def _get_nearby_castle(self, knight, game_state):
        """Check if knight is adjacent to a castle"""
        for castle in game_state.castles:
            for tile_x, tile_y in castle.occupied_tiles:
                if abs(knight.x - tile_x) + abs(knight.y - tile_y) <= 1:
                    return castle
        return None
    
    def handle_click(self, x, y):
        if not self.visible:
            return None
        
        if x < self.x or x > self.x + self.width:
            self.hide()
            return None
        
        relative_y = y - self.y
        if relative_y < 0 or relative_y > len(self.options) * self.option_height:
            self.hide()
            return None
        
        option_index = relative_y // self.option_height
        if 0 <= option_index < len(self.options):
            option = self.options[option_index]
            if option['enabled']:
                action = option['action']
                self.hide()
                return action
        
        return None
    
    def get_hover_option(self, x, y):
        if not self.visible:
            return None
        
        if x < self.x or x > self.x + self.width:
            return None
        
        relative_y = y - self.y
        if relative_y < 0 or relative_y > len(self.options) * self.option_height:
            return None
        
        return relative_y // self.option_height
    
    def render(self, screen):
        if not self.visible:
            return
        
        menu_height = len(self.options) * self.option_height
        
        pygame.draw.rect(screen, self.colors['background'],
                        (self.x, self.y, self.width, menu_height))
        pygame.draw.rect(screen, self.colors['border'],
                        (self.x, self.y, self.width, menu_height), 2)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_index = self.get_hover_option(mouse_x, mouse_y)
        
        for i, option in enumerate(self.options):
            y_pos = self.y + i * self.option_height
            
            if hover_index == i and option['enabled']:
                pygame.draw.rect(screen, self.colors['hover'],
                               (self.x, y_pos, self.width, self.option_height))
            
            text_color = self.colors['text'] if option['enabled'] else self.colors['disabled']
            text = self.font.render(option['text'], True, text_color)
            text_rect = text.get_rect(midleft=(self.x + 10, y_pos + self.option_height // 2))
            screen.blit(text, text_rect)
            
            if i < len(self.options) - 1:
                pygame.draw.line(screen, self.colors['border'],
                               (self.x + 5, y_pos + self.option_height),
                               (self.x + self.width - 5, y_pos + self.option_height), 1)