import pygame
import math
from game.entities.knight import KnightClass
from game.hex_utils import HexGrid, HexCoord
from game.hex_layout import HexLayout
from game.visibility import VisibilityState
from game.terrain import TerrainType
from game.asset_manager import AssetManager

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.tile_size = 64
        self.hex_grid = HexGrid(hex_size=36)  # For hex distance calculations
        self.hex_layout = HexLayout(hex_size=36)  # For positioning
        self.font = pygame.font.Font(None, 24)
        self.ui_font = pygame.font.Font(None, 32)
        self.asset_manager = AssetManager()
        self.input_handler = None  # Will be set by main.py
        
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
            'road': (169, 169, 169),
            # New terrain type colors
            'light_forest': (85, 170, 85),      # Lighter green than forest
            'dense_forest': (0, 100, 0),        # Darker green than forest
            'high_hills': (160, 82, 45),        # Darker brown than hills
            'mountains': (105, 105, 105),       # Dark grey
            'deep_water': (0, 0, 139),          # Dark blue
            'marsh': (107, 142, 35),            # Olive/yellowish green
            'desert': (238, 203, 173),          # Sandy beige
            'snow': (255, 250, 250)
        }
    
    def _draw_dotted_line(self, surface, start_pos, end_pos, color, width=1, dash_length=5):
        """Draw a dotted line between two points"""
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate distance and direction
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            return
            
        # Normalize direction
        dx /= distance
        dy /= distance
        
        # Draw dashes
        drawn = 0
        draw_dash = True
        
        while drawn < distance:
            if draw_dash:
                # Calculate dash end point
                dash_end = min(drawn + dash_length, distance)
                
                # Draw the dash
                start_x = x1 + dx * drawn
                start_y = y1 + dy * drawn
                end_x = x1 + dx * dash_end
                end_y = y1 + dy * dash_end
                
                pygame.draw.line(surface, color, 
                               (int(start_x), int(start_y)), 
                               (int(end_x), int(end_y)), 
                               width)
            
            drawn += dash_length
            draw_dash = not draw_dash
    
    def render(self, game_state):
        self.screen.fill(self.colors['background'])
        
        # Update zoom settings if input handler is available
        if self.input_handler:
            self.hex_grid = self.input_handler.hex_grid
            self.hex_layout = self.input_handler.hex_layout
        
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
                        TerrainType.ROAD: self.colors['road'],
                        # New terrain types
                        TerrainType.LIGHT_FOREST: self.colors['light_forest'],
                        TerrainType.DENSE_FOREST: self.colors['dense_forest'],
                        TerrainType.HIGH_HILLS: self.colors['high_hills'],
                        TerrainType.MOUNTAINS: self.colors['mountains'],
                        TerrainType.DEEP_WATER: self.colors['deep_water'],
                        TerrainType.MARSH: self.colors['marsh'],
                        TerrainType.DESERT: self.colors['desert'],
                        TerrainType.SNOW: self.colors['snow']
                    }
                    color = terrain_colors.get(terrain.type, self.colors['plains'])
                else:
                    color = self.colors['tile_light'] if (col + row) % 2 == 0 else self.colors['tile_dark']
                
                # Get hex corners and draw the hexagon
                corners = self.hex_layout.get_hex_corners(screen_x, screen_y)
                
                # Check if we have an image asset for this terrain
                terrain_image = None
                has_asset = False
                if terrain:
                    if terrain.type == TerrainType.WATER:
                        terrain_image = self.asset_manager.get_terrain_image("water", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.DEEP_WATER:
                        terrain_image = self.asset_manager.get_terrain_image("deep-water", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.PLAINS:
                        terrain_image = self.asset_manager.get_terrain_image("plain", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.HILLS:
                        terrain_image = self.asset_manager.get_terrain_image("hills", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.LIGHT_FOREST:
                        terrain_image = self.asset_manager.get_terrain_image("light-forrest", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.FOREST:
                        terrain_image = self.asset_manager.get_terrain_image("forrest", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.DENSE_FOREST:
                        terrain_image = self.asset_manager.get_terrain_image("dense-forrest", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.SWAMP:
                        terrain_image = self.asset_manager.get_terrain_image("swamp", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.MOUNTAINS:
                        terrain_image = self.asset_manager.get_terrain_image("mountains", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.HIGH_HILLS:
                        terrain_image = self.asset_manager.get_terrain_image("high-hills", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.SNOW:
                        terrain_image = self.asset_manager.get_terrain_image("snow", self.hex_grid.hex_size)
                    elif terrain.type == TerrainType.DESERT:
                        terrain_image = self.asset_manager.get_terrain_image("desert", self.hex_grid.hex_size)
                    has_asset = terrain_image is not None
                
                if terrain_image:
                    # Calculate position to center the image in the hex
                    image_rect = terrain_image.get_rect(center=(int(screen_x), int(screen_y)))
                    self.screen.blit(terrain_image, image_rect)
                    pygame.draw.polygon(self.screen, (0, 0, 0), corners, 1)  # Black outline
                else:
                    # Fallback to colored polygon
                    pygame.draw.polygon(self.screen, color, corners)
                    pygame.draw.polygon(self.screen, (0, 0, 0), corners, 1)  # Black outline
                
                # Check fog of war visibility and apply overlay
                visibility = VisibilityState.VISIBLE  # Default for no fog
                if hasattr(game_state, 'fog_of_war') and game_state.fog_view_player is not None:
                    visibility = game_state.fog_of_war.get_visibility_state(game_state.fog_view_player, col, row)
                
                # Apply fog overlay for non-visible hexes
                if visibility != VisibilityState.VISIBLE:
                    # Create a semi-transparent grey overlay
                    fog_surface = pygame.Surface((int(self.hex_grid.hex_width), int(self.hex_grid.hex_height)), pygame.SRCALPHA)
                    
                    # Different alpha values for different visibility states
                    if visibility == VisibilityState.HIDDEN:
                        # Heavy fog for never-seen areas
                        fog_color = (40, 40, 40, 200)  # Dark grey, very opaque
                    elif visibility == VisibilityState.EXPLORED:
                        # Medium fog for previously seen areas
                        fog_color = (60, 60, 60, 150)  # Grey, semi-opaque
                    else:  # PARTIAL
                        # Light fog for partially visible areas
                        fog_color = (80, 80, 80, 100)  # Light grey, less opaque
                    
                    # Draw fog polygon on the surface
                    corners_relative = [(x - screen_x + self.hex_grid.hex_width/2, 
                                       y - screen_y + self.hex_grid.hex_height/2) for x, y in corners]
                    pygame.draw.polygon(fog_surface, fog_color, corners_relative)
                    
                    # Blit the fog overlay
                    self.screen.blit(fog_surface, (screen_x - self.hex_grid.hex_width/2, 
                                                  screen_y - self.hex_grid.hex_height/2))
                
                # Draw coordinate labels (optional - for debugging)
                if game_state.show_coordinates:
                    coord_text = self.font.render(f"{col},{row}", True, (100, 100, 100))
                    text_rect = coord_text.get_rect(center=(int(screen_x), int(screen_y)))
                    self.screen.blit(coord_text, text_rect)
                
                # Add texture patterns for different terrains inside hexes (only if no asset image)
                if terrain and not has_asset:
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
        
        # Draw enemy movement paths (if enabled)
        if game_state.show_enemy_paths and hasattr(game_state, 'movement_history'):
            for unit_id, path in game_state.movement_history.items():
                # Find the unit to check if it's an enemy
                unit = None
                for knight in game_state.knights:
                    if id(knight) == unit_id:
                        unit = knight
                        break
                
                # Only draw enemy paths
                if unit and unit.player_id != game_state.current_player and len(path) > 1:
                    # Draw dotted lines between consecutive positions
                    for i in range(len(path) - 1):
                        start_pos = path[i]
                        end_pos = path[i + 1]
                        
                        # Check if both positions are visible (not in fog of war)
                        start_visible = True
                        end_visible = True
                        
                        if hasattr(game_state, 'fog_of_war') and game_state.current_player is not None:
                            start_vis = game_state.fog_of_war.get_visibility_state(
                                game_state.current_player, start_pos[0], start_pos[1])
                            end_vis = game_state.fog_of_war.get_visibility_state(
                                game_state.current_player, end_pos[0], end_pos[1])
                            
                            # Draw if both positions are at least explored (not completely hidden)
                            # This allows seeing paths in previously explored areas
                            start_visible = start_vis in [VisibilityState.VISIBLE, VisibilityState.PARTIAL, VisibilityState.EXPLORED]
                            end_visible = end_vis in [VisibilityState.VISIBLE, VisibilityState.PARTIAL, VisibilityState.EXPLORED]
                        
                        if start_visible and end_visible:
                            # Convert hex positions to screen coordinates
                            start_pixel_x, start_pixel_y = self.hex_layout.hex_to_pixel(start_pos[0], start_pos[1])
                            start_screen_x, start_screen_y = game_state.world_to_screen(start_pixel_x, start_pixel_y)
                            
                            end_pixel_x, end_pixel_y = self.hex_layout.hex_to_pixel(end_pos[0], end_pos[1])
                            end_screen_x, end_screen_y = game_state.world_to_screen(end_pixel_x, end_pixel_y)
                            
                            # Draw dotted line
                            self._draw_dotted_line(self.screen, 
                                                 (start_screen_x, start_screen_y),
                                                 (end_screen_x, end_screen_y),
                                                 (255, 255, 0),  # Yellow color for enemy paths
                                                 3, 8)  # width=3, dash_length=8
    
    def _draw_castles(self, game_state):
        for castle in game_state.castles:
            # Check if any part of the castle is visible
            castle_visible = False
            if hasattr(game_state, 'fog_of_war') and game_state.fog_view_player is not None:
                for tile_x, tile_y in castle.occupied_tiles:
                    visibility = game_state.fog_of_war.get_visibility_state(game_state.fog_view_player, tile_x, tile_y)
                    if visibility in [VisibilityState.VISIBLE, VisibilityState.PARTIAL, VisibilityState.EXPLORED]:
                        castle_visible = True
                        break
            else:
                castle_visible = True  # No fog of war
                
            if not castle_visible:
                continue
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
            # Check fog of war visibility
            is_identified = True  # Default to identified if no fog of war
            if hasattr(game_state, 'fog_of_war') and game_state.fog_view_player is not None:
                visibility = game_state.fog_of_war.get_visibility_state(game_state.fog_view_player, knight.x, knight.y)
                
                # Don't draw units we can't see
                if visibility not in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                    continue
                    
                # For partial visibility, we'll show a generic unit marker
                is_identified = (visibility == VisibilityState.VISIBLE or 
                               knight.player_id == game_state.current_player)
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
            
            # Draw unit based on identification status
            if not hasattr(game_state, 'fog_of_war') or is_identified:
                # Full identification - draw specific unit type
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
            else:
                # Partial visibility - draw generic unit marker
                pygame.draw.circle(self.screen, (150, 150, 150), (center_x, center_y), 20)
                pygame.draw.circle(self.screen, player_color, (center_x, center_y), 20, 3)
            
            if knight.selected:
                pygame.draw.circle(self.screen, self.colors['selected'],
                                 (center_x, center_y), 30, 3)
            
            # Draw facing indicator
            if hasattr(knight, 'facing'):
                # Get arrow coordinates
                start, end = knight.facing.get_facing_arrow_coords(center_x, center_y, 25)
                
                # Draw arrow line
                pygame.draw.line(self.screen, (255, 255, 0), start, end, 3)
                
                # Draw arrowhead
                arrow_angle = math.atan2(end[1] - start[1], end[0] - start[0])
                arrow_length = 8
                arrow_degrees = 25
                
                # Calculate arrowhead points
                angle1 = arrow_angle + math.radians(180 - arrow_degrees)
                angle2 = arrow_angle + math.radians(180 + arrow_degrees)
                
                arrow_x1 = end[0] + arrow_length * math.cos(angle1)
                arrow_y1 = end[1] + arrow_length * math.sin(angle1)
                arrow_x2 = end[0] + arrow_length * math.cos(angle2)
                arrow_y2 = end[1] + arrow_length * math.sin(angle2)
                
                # Draw filled arrowhead
                pygame.draw.polygon(self.screen, (255, 255, 0), 
                                  [end, (arrow_x1, arrow_y1), (arrow_x2, arrow_y2)])
            
            health_percent = knight.health / knight.max_health
            bar_width = 40
            bar_height = 4
            bar_x = x - bar_width // 2  # Center the bar horizontally
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
        
        # Current player in UI bar with mode indicator
        if game_state.vs_ai:
            if game_state.current_player == 1:
                player_info = "Player 1 (Human)"
            else:
                player_info = "Player 2 (AI)" + (" - Thinking..." if game_state.ai_thinking else "")
        else:
            player_info = f"Player {game_state.current_player} (Human)"
        
        player_text = self.ui_font.render(player_info, True, self.colors['text'])
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
            elif knight.is_disrupted:
                status_str = " - DISRUPTED"
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
            
            # Show attached generals
            if knight.generals and knight.generals.generals:
                general_names = [g.name for g in knight.generals.generals]
                generals_text = self.font.render(
                    f"Generals: {', '.join(general_names)}",
                    True, self.colors['text']
                )
                self.screen.blit(generals_text, (20, ui_y + 75))
        
        # Show enemy unit info if clicked
        elif game_state.enemy_info_unit:
            enemy = game_state.enemy_info_unit
            terrain = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
            terrain_str = f" - Terrain: {terrain.type.value}" if terrain else ""
            
            # Check status
            status_str = ""
            if enemy.is_routing:
                status_str = " - ROUTING!"
            elif enemy.is_disrupted:
                status_str = " - DISRUPTED"
            elif enemy.in_enemy_zoc:
                status_str = " - ENGAGED"
            
            enemy_info_text = self.font.render(
                f"Enemy: {enemy.name} ({enemy.knight_class.value}) - "
                f"Soldiers: {enemy.soldiers}/{enemy.max_soldiers} - "
                f"Morale: {int(enemy.morale)}% - "
                f"Will: {int(enemy.will)}% - "
                f"AP: {enemy.action_points} - "
                f"Frontage: {enemy.get_effective_soldiers(terrain)}{terrain_str}{status_str}",
                True, (255, 100, 100)  # Red color for enemy
            )
            self.screen.blit(enemy_info_text, (20, ui_y + 50))
            
            # Show enemy generals
            if enemy.generals and enemy.generals.generals:
                enemy_general_names = [g.name for g in enemy.generals.generals]
                enemy_generals_text = self.font.render(
                    f"Enemy Generals: {', '.join(enemy_general_names)}",
                    True, (255, 100, 100)
                )
                self.screen.blit(enemy_generals_text, (20, ui_y + 75))
        
        # Show terrain info if clicked on empty terrain
        elif game_state.terrain_info:
            terrain_data = game_state.terrain_info
            terrain = terrain_data['terrain']
            x, y = terrain_data['x'], terrain_data['y']
            
            # Get terrain type and feature
            terrain_type = terrain.type.value
            feature_str = f" - Feature: {terrain.feature.value}" if terrain.feature.value != "None" else ""
            
            # Get terrain properties
            movement_cost = terrain.movement_cost
            defense_bonus = terrain.defense_bonus
            elevation = terrain.elevation
            passable = "Yes" if terrain.passable else "No"
            blocks_vision = "Yes" if terrain.blocks_vision else "No"
            
            # Format movement cost
            if movement_cost == float('inf'):
                movement_str = "Impassable"
            else:
                movement_str = f"{movement_cost:.1f}"
            
            terrain_info_text = self.font.render(
                f"Terrain: {terrain_type} at ({x}, {y}){feature_str}",
                True, (200, 200, 255)  # Light blue color for terrain
            )
            self.screen.blit(terrain_info_text, (20, ui_y + 50))
            
            terrain_details_text = self.font.render(
                f"Movement Cost: {movement_str} - Defense: {defense_bonus:+d} - "
                f"Elevation: {elevation} - Passable: {passable} - Blocks Vision: {blocks_vision}",
                True, (180, 180, 235)  # Slightly darker blue
            )
            self.screen.blit(terrain_details_text, (20, ui_y + 75))
        
        # Show castle status (only if castles exist)
        if game_state.castles:
            player_castle = None
            for castle in game_state.castles:
                if castle.player_id == game_state.current_player:
                    player_castle = castle
                    break
                    
            if player_castle:
                enemies_near = len(player_castle.get_enemies_in_range(game_state.knights))
                archer_count = player_castle.get_total_archer_soldiers()
                garrison_info = f"Garrison: {len(player_castle.garrisoned_units)}/{player_castle.garrison_slots}"
                
                castle_text = self.font.render(
                    f"Castle - HP: {player_castle.health}/{player_castle.max_health} - "
                    f"{garrison_info} - Archers: {archer_count} - Enemies in range: {enemies_near}",
                    True, self.colors['text']
                )
                castle_y = ui_y + 100 if game_state.selected_knight or game_state.enemy_info_unit or game_state.terrain_info else ui_y + 75
                self.screen.blit(castle_text, (20, castle_y))
        
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