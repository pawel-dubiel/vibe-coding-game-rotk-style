import pygame
import math
from game.entities.knight import KnightClass
from game.hex_utils import HexGrid, HexCoord
from game.hex_layout import HexLayout

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.tile_size = 64
        self.hex_grid = HexGrid(hex_size=36)  # For hex distance calculations
        self.hex_layout = HexLayout(hex_size=36, orientation='flat')  # For positioning
        self.font = pygame.font.Font(None, 24)
        self.ui_font = pygame.font.Font(None, 32)
        
        self.colors = {
            'background': (50, 50, 50),
            'tile_light': (120, 100, 80),
            'tile_dark': (100, 80, 60),
            'selected': (255, 255, 100),
            'possible_move': (100, 200, 100),
            'attack_target': (255, 100, 100),
            'player1': (100, 100, 255),
            'player2': (255, 100, 100),
            'health_bar_bg': (60, 60, 60),
            'health_bar': (0, 255, 0),
            'castle': (150, 150, 150),
            'ui_bg': (40, 40, 40),
            'text': (255, 255, 255),
            # Terrain colors
            'plains': (144, 238, 144),
            'forest': (34, 139, 34),
            'hills': (139, 90, 43),
            'water': (64, 164, 223),
            'bridge': (139, 69, 19),
            'swamp': (47, 79, 47),
            'road': (169, 169, 169)
        }
    
    def render(self, game_state):
        self.screen.fill(self.colors['background'])
        
        self._draw_board(game_state)
        self._draw_castles(game_state)
        self._draw_knights(game_state)
        self._draw_animations(game_state)
        self._draw_ui(game_state)
        game_state.context_menu.render(self.screen)
    
    def _draw_board(self, game_state):
        from game.terrain import TerrainType
        
        # Calculate visible hex range based on camera position
        # We need to draw a bit more to ensure edge hexes are visible
        start_col = max(0, int(game_state.camera_x / self.hex_grid.hex_width) - 1)
        end_col = min(game_state.board_width, int((game_state.camera_x + game_state.screen_width) / self.hex_grid.hex_width) + 2)
        start_row = max(0, int(game_state.camera_y / self.hex_grid.hex_height) - 1)
        end_row = min(game_state.board_height, int((game_state.camera_y + game_state.screen_height) / self.hex_grid.hex_height) + 2)
        
        for col in range(start_col, end_col):
            for row in range(start_row, end_row):
                # Use hex layout for proper positioning
                pixel_x, pixel_y = self.hex_layout.hex_to_pixel(col, row)
                
                # Apply camera offset
                screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
                
                # Get terrain color
                terrain = game_state.terrain_map.get_terrain(col, row)
                if terrain:
                    terrain_colors = {
                        TerrainType.PLAINS: self.colors['plains'],
                        TerrainType.FOREST: self.colors['forest'],
                        TerrainType.HILLS: self.colors['hills'],
                        TerrainType.WATER: self.colors['water'],
                        TerrainType.BRIDGE: self.colors['bridge'],
                        TerrainType.SWAMP: self.colors['swamp'],
                        TerrainType.ROAD: self.colors['road']
                    }
                    color = terrain_colors.get(terrain.type, self.colors['plains'])
                else:
                    color = self.colors['tile_light'] if (col + row) % 2 == 0 else self.colors['tile_dark']
                
                # Get hex corners and draw the hexagon
                corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
                pygame.draw.polygon(self.screen, color, corners)
                pygame.draw.polygon(self.screen, (0, 0, 0), corners, 1)  # Black outline
                
                # Draw coordinate labels (optional - for debugging)
                if game_state.show_coordinates:
                    coord_text = self.font.render(f"{col},{row}", True, (100, 100, 100))
                    text_rect = coord_text.get_rect(center=(int(screen_x), int(screen_y)))
                    self.screen.blit(coord_text, text_rect)
                
                # Add texture patterns for different terrains inside hexes
                if terrain:
                    if terrain.type == TerrainType.FOREST:
                        # Draw small trees inside hex
                        for i in range(2):
                            tree_x = screen_x + (i - 0.5) * 15
                            tree_y = screen_y + (i % 2 - 0.5) * 15
                            pygame.draw.circle(self.screen, (0, 100, 0), (int(tree_x), int(tree_y)), 4)
                    elif terrain.type == TerrainType.HILLS:
                        # Draw hill symbol
                        pygame.draw.arc(self.screen, (100, 50, 0), 
                                      (screen_x - 15, screen_y - 10, 30, 20), 0, 3.14, 3)
                    elif terrain.type == TerrainType.WATER:
                        # Draw wave lines
                        for i in range(2):
                            wave_y = screen_y + (i - 0.5) * 10
                            pygame.draw.line(self.screen, (100, 200, 255), 
                                           (screen_x - 15, wave_y), (screen_x + 15, wave_y), 2)
                    elif terrain.type == TerrainType.SWAMP:
                        # Draw dots for swamp
                        for i in range(4):
                            angle = i * 90
                            dot_x = screen_x + 10 * math.cos(math.radians(angle))
                            dot_y = screen_y + 10 * math.sin(math.radians(angle))
                            pygame.draw.circle(self.screen, (70, 100, 70), (int(dot_x), int(dot_y)), 2)
        
        # Draw possible moves as highlighted hexes
        for move_x, move_y in game_state.possible_moves:
            # Use hex layout for proper positioning
            pixel_x, pixel_y = self.hex_layout.hex_to_pixel(move_x, move_y)
            screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
            
            # Get hex corners and draw highlight
            corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
            
            # Check if this move would break formation
            if game_state.selected_knight:
                start_adjacent = game_state.selected_knight._has_adjacent_friendly(
                    game_state.selected_knight.x, game_state.selected_knight.y, game_state)
                end_adjacent = game_state.selected_knight._has_adjacent_friendly(
                    move_x, move_y, game_state)
                
                # Use different color if breaking formation
                if start_adjacent and not end_adjacent:
                    pygame.draw.polygon(self.screen, (200, 100, 100), corners, 3)  # Red tint
                else:
                    pygame.draw.polygon(self.screen, self.colors['possible_move'], corners, 3)
        
        # Draw attack targets as highlighted hexes
        for target_x, target_y in game_state.attack_targets:
            # Use hex layout for proper positioning
            pixel_x, pixel_y = self.hex_layout.hex_to_pixel(target_x, target_y)
            screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
            
            # Get hex corners and draw highlight
            corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
            
            # Use different color for charge targets
            if game_state.current_action == 'charge':
                pygame.draw.polygon(self.screen, (255, 200, 0), corners, 4)  # Golden color
            else:
                pygame.draw.polygon(self.screen, self.colors['attack_target'], corners, 3)
    
    def _draw_castles(self, game_state):
        for castle in game_state.castles:
            # Draw all castle tiles as hexagons
            for tile_x, tile_y in castle.occupied_tiles:
                # Use hex layout for positioning
                pixel_x, pixel_y = self.hex_layout.hex_to_pixel(tile_x, tile_y)
                x, y = game_state.world_to_screen(pixel_x, pixel_y)
                
                # Get hex corners
                corners = self.hex_layout.get_hex_corners(x, y)
                
                # Draw castle hex
                player_color = self.colors['player1'] if castle.player_id == 1 else self.colors['player2']
                
                # Different shading for center vs outer tiles
                if tile_x == castle.center_x and tile_y == castle.center_y:
                    # Draw filled hex for center
                    pygame.draw.polygon(self.screen, self.colors['castle'], corners)
                    pygame.draw.polygon(self.screen, player_color, corners, 4)
                else:
                    # Draw semi-filled hex for outer tiles
                    pygame.draw.polygon(self.screen, self.colors['castle'], corners)
                    pygame.draw.polygon(self.screen, player_color, corners, 3)
            
            # Draw health bar at center
            center_pixel_x, center_pixel_y = self.hex_layout.hex_to_pixel(castle.center_x, castle.center_y)
            center_x, center_y = game_state.world_to_screen(center_pixel_x, center_pixel_y)
            
            health_percent = castle.health / castle.max_health
            bar_width = int(self.hex_grid.hex_width * 0.6)
            bar_height = 6
            bar_x = center_x - bar_width // 2
            bar_y = center_y + int(self.hex_grid.hex_height * 0.3)
            
            pygame.draw.rect(self.screen, self.colors['health_bar_bg'],
                           (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, self.colors['health_bar'],
                           (bar_x, bar_y, int(bar_width * health_percent), bar_height))
            
            # Show garrison info
            if castle.garrisoned_units:
                garrison_text = self.font.render(f"G:{len(castle.garrisoned_units)}", True, self.colors['text'])
                self.screen.blit(garrison_text, (center_x + 5, center_y + 5))
            
            # Draw castle range indicator when castle has enemies nearby and archers
            if castle.get_total_archer_soldiers() > 0:
                enemies_in_range = castle.get_enemies_in_range(game_state.knights)
                if enemies_in_range and not castle.has_shot:
                    # Draw hex range for castle archers
                    for tile_x, tile_y in castle.occupied_tiles:
                        castle_hex = self.hex_grid.offset_to_axial(tile_x, tile_y)
                        range_hexes = castle_hex.get_neighbors_within_range(castle.arrow_range)
                        
                        for hex_coord in range_hexes:
                            range_x, range_y = self.hex_grid.axial_to_offset(hex_coord)
                            if 0 <= range_x < game_state.board_width and 0 <= range_y < game_state.board_height:
                                # Use hex layout for positioning
                                pixel_x, pixel_y = self.hex_layout.hex_to_pixel(range_x, range_y)
                                screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
                                corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
                                pygame.draw.polygon(self.screen, (255, 200, 200), corners, 1)
    
    def _draw_knights(self, game_state):
        from game.animation import MoveAnimation, PathMoveAnimation
        
        for knight in game_state.knights:
            # Use hex layout for positioning
            pixel_x, pixel_y = self.hex_layout.hex_to_pixel(knight.x, knight.y)
            
            # Check for move animations (both types)
            for anim in game_state.animation_manager.get_current_animations():
                if (isinstance(anim, (MoveAnimation, PathMoveAnimation)) and anim.knight == knight):
                    anim_x, anim_y = anim.get_current_position()
                    pixel_x, pixel_y = self.hex_layout.hex_to_pixel(anim_x, anim_y)
                    break
            
            # Convert to screen coordinates
            x, y = game_state.world_to_screen(pixel_x, pixel_y)
            
            player_color = self.colors['player1'] if knight.player_id == 1 else self.colors['player2']
            
            center_x = x
            center_y = y
            
            if knight.knight_class == KnightClass.WARRIOR:
                pygame.draw.rect(self.screen, player_color,
                               (center_x - 20, center_y - 20, 40, 40))
            elif knight.knight_class == KnightClass.ARCHER:
                pygame.draw.polygon(self.screen, player_color,
                                  [(center_x, center_y - 25),
                                   (center_x - 20, center_y + 20),
                                   (center_x + 20, center_y + 20)])
            elif knight.knight_class == KnightClass.CAVALRY:
                pygame.draw.ellipse(self.screen, player_color,
                                  (center_x - 25, center_y - 15, 50, 30))
            elif knight.knight_class == KnightClass.MAGE:
                pygame.draw.circle(self.screen, player_color, (center_x, center_y), 22)
            
            if knight.selected:
                pygame.draw.circle(self.screen, self.colors['selected'],
                                 (center_x, center_y), 30, 3)
            
            health_percent = knight.health / knight.max_health
            bar_width = 40
            bar_height = 4
            bar_x = x + (self.tile_size - bar_width) // 2
            bar_y = y + 8
            
            pygame.draw.rect(self.screen, self.colors['health_bar_bg'],
                           (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, self.colors['health_bar'],
                           (bar_x, bar_y, int(bar_width * health_percent), bar_height))
            
            # Show soldier count instead of AP
            soldier_text = self.font.render(f"{knight.soldiers}", True, self.colors['text'])
            text_rect = soldier_text.get_rect(center=(center_x, y + self.tile_size - 8))
            self.screen.blit(soldier_text, text_rect)
            
            # Show morale indicator (left side)
            if knight.morale < 100:
                morale_color = (255, 255 - int(knight.morale * 2.55), 0)
                pygame.draw.circle(self.screen, morale_color, (center_x - 20, center_y - 20), 5)
            
            # Show will indicator (right side) - only for units that use will
            if knight.knight_class == KnightClass.CAVALRY and knight.will < knight.max_will:
                will_percent = knight.will / knight.max_will
                will_color = (100, 100, 255 - int((1 - will_percent) * 155))
                pygame.draw.circle(self.screen, will_color, (center_x + 20, center_y - 20), 5)
            
            # Show routing flag
            if knight.is_routing:
                # Draw white flag for routing units
                flag_x = center_x - 25
                flag_y = center_y - 25
                pygame.draw.line(self.screen, (200, 200, 200), (flag_x, flag_y), (flag_x, flag_y + 15), 2)
                pygame.draw.polygon(self.screen, (255, 255, 255), 
                                  [(flag_x, flag_y), (flag_x + 10, flag_y + 3), (flag_x, flag_y + 6)])
            
            # Show ZOC indicator
            if knight.has_zone_of_control():
                # Draw ZOC for hex neighbors
                knight_hex = self.hex_grid.offset_to_axial(knight.x, knight.y)
                neighbors = knight_hex.get_neighbors()
                
                for neighbor_hex in neighbors:
                    zoc_x, zoc_y = self.hex_grid.axial_to_offset(neighbor_hex)
                    if 0 <= zoc_x < game_state.board_width and 0 <= zoc_y < game_state.board_height:
                        # Use hex layout for positioning
                        pixel_x, pixel_y = self.hex_layout.hex_to_pixel(zoc_x, zoc_y)
                        screen_x, screen_y = game_state.world_to_screen(pixel_x, pixel_y)
                        pygame.draw.circle(self.screen, player_color, (int(screen_x), int(screen_y)), 3, 1)
    
    def _draw_animations(self, game_state):
        from game.animation import AttackAnimation, ArrowAnimation
        
        for anim in game_state.animation_manager.get_current_animations():
            if isinstance(anim, AttackAnimation):
                result = anim.get_effect_position()
                if len(result) == 3:  # Before impact
                    x, y, _ = result
                    # Use hex layout for proper positioning
                    world_x, world_y = self.hex_layout.hex_to_pixel(x, y)
                    screen_x, screen_y = game_state.world_to_screen(world_x, world_y)
                    pygame.draw.circle(self.screen, (255, 255, 0), (int(screen_x), int(screen_y)), 10)
                else:  # Impact with shake
                    x, y, _, shake_x, shake_y = result
                    # Draw damage number
                    damage_text = self.ui_font.render(str(anim.damage), True, (255, 50, 50))
                    # Use hex layout for proper positioning
                    world_x, world_y = self.hex_layout.hex_to_pixel(x, y)
                    screen_x, screen_y = game_state.world_to_screen(world_x, world_y)
                    text_x = int(screen_x + shake_x)
                    text_y = int(screen_y + shake_y)
                    text_rect = damage_text.get_rect(center=(text_x, text_y))
                    self.screen.blit(damage_text, text_rect)
            
            elif isinstance(anim, ArrowAnimation):
                arrows, hit = anim.get_arrow_positions()
                if not hit:
                    # Draw flying arrows
                    for arrow_x, arrow_y in arrows:
                        # Use hex layout for proper positioning
                        world_x, world_y = self.hex_layout.hex_to_pixel(arrow_x, arrow_y)
                        center_x, center_y = game_state.world_to_screen(world_x, world_y)
                        center_x = int(center_x)
                        center_y = int(center_y)
                        # Draw arrow as a small triangle
                        pygame.draw.polygon(self.screen, (139, 69, 19),
                                          [(center_x - 5, center_y),
                                           (center_x + 5, center_y),
                                           (center_x, center_y - 10)])
                else:
                    # Show damage on targets
                    for i, (target, damage) in enumerate(zip(anim.targets, anim.damages)):
                        damage_text = self.font.render(f"-{damage}", True, (255, 50, 50))
                        world_x = target.x * self.tile_size + self.tile_size // 2
                        world_y = target.y * self.tile_size + 20
                        screen_x, screen_y = game_state.world_to_screen(world_x, world_y)
                        text_rect = damage_text.get_rect(center=(int(screen_x), int(screen_y)))
                        self.screen.blit(damage_text, text_rect)
    
    def _draw_ui(self, game_state):
        ui_height = 100
        ui_y = self.screen.get_height() - ui_height
        pygame.draw.rect(self.screen, self.colors['ui_bg'],
                       (0, ui_y, self.screen.get_width(), ui_height))
        
        # Show turn counter prominently at top of screen
        turn_bg = pygame.Rect(self.screen.get_width() // 2 - 100, 10, 200, 40)
        pygame.draw.rect(self.screen, self.colors['ui_bg'], turn_bg)
        pygame.draw.rect(self.screen, self.colors['text'], turn_bg, 2)
        turn_text = self.ui_font.render(f"Turn {game_state.turn_number}", True, self.colors['text'])
        turn_rect = turn_text.get_rect(center=turn_bg.center)
        self.screen.blit(turn_text, turn_rect)
        
        # Draw messages
        self._draw_messages(game_state)
        
        # Current player in UI bar
        player_text = self.ui_font.render(f"Player {game_state.current_player}",
                                      True, self.colors['text'])
        self.screen.blit(player_text, (20, ui_y + 10))
        
        if game_state.selected_knight:
            knight = game_state.selected_knight
            
            # Get terrain info
            terrain = game_state.terrain_map.get_terrain(knight.x, knight.y) if not knight.is_garrisoned else None
            terrain_str = f" - Terrain: {terrain.type.value}" if terrain else ""
            garrison_str = " - GARRISONED" if knight.is_garrisoned else ""
            
            status_str = ""
            if knight.is_routing:
                status_str = " - ROUTING!"
            elif knight.in_enemy_zoc:
                status_str = " - ENGAGED"
            
            info_text = self.font.render(
                f"{knight.name} ({knight.knight_class.value}) - "
                f"Soldiers: {knight.soldiers}/{knight.max_soldiers} - "
                f"Morale: {int(knight.morale)}% - "
                f"Will: {int(knight.will)}% - "
                f"AP: {knight.action_points} - "
                f"Frontage: {knight.get_effective_soldiers(terrain)}{terrain_str}{garrison_str}{status_str}",
                True, self.colors['text']
            )
            self.screen.blit(info_text, (20, ui_y + 50))
        
        # Show castle status
        player_castle = game_state.castles[0] if game_state.current_player == 1 else game_state.castles[1]
        enemies_near = len(player_castle.get_enemies_in_range(game_state.knights))
        archer_count = player_castle.get_total_archer_soldiers()
        garrison_info = f"Garrison: {len(player_castle.garrisoned_units)}/{player_castle.garrison_slots}"
        
        castle_text = self.font.render(
            f"Castle - HP: {player_castle.health}/{player_castle.max_health} - "
            f"{garrison_info} - Archers: {archer_count} - Enemies in range: {enemies_near}",
            True, self.colors['text']
        )
        self.screen.blit(castle_text, (20, ui_y + 75))
        
        end_turn_rect = pygame.Rect(self.screen.get_width() - 140, ui_y + 20, 120, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), end_turn_rect)
        end_turn_text = self.font.render("End Turn", True, self.colors['text'])
        text_rect = end_turn_text.get_rect(center=end_turn_rect.center)
        self.screen.blit(end_turn_text, text_rect)
        
        victory = game_state.check_victory()
        if victory:
            victory_text = self.ui_font.render(f"Player {victory} Wins!", True, self.colors['text'])
            text_rect = victory_text.get_rect(center=(self.screen.get_width() // 2, ui_y + 70))
            self.screen.blit(victory_text, text_rect)
    
    def _draw_messages(self, game_state):
        """Draw combat messages on screen"""
        import time
        current_time = time.time()
        y_offset = 60  # Start below turn counter
        
        for i, (message, timestamp, priority) in enumerate(game_state.messages[:5]):  # Show max 5 messages
            # Calculate fade based on age
            age = current_time - timestamp
            max_age = game_state.message_duration * priority
            alpha = int(255 * (1 - age / max_age))
            
            # Create message surface with background
            msg_surface = self.ui_font.render(message, True, self.colors['text'])
            msg_rect = msg_surface.get_rect(center=(self.screen.get_width() // 2, y_offset + i * 35))
            
            # Draw background box
            bg_rect = msg_rect.inflate(20, 10)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(alpha * 0.7)
            bg_surface.fill(self.colors['ui_bg'])
            self.screen.blit(bg_surface, bg_rect)
            
            # Draw message text
            msg_surface.set_alpha(alpha)
            self.screen.blit(msg_surface, msg_rect)