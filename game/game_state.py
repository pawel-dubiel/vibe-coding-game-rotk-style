import pygame
from typing import Optional
from game.entities.knight import KnightClass
from game.entities.unit_factory import UnitFactory
from game.entities.castle import Castle
from game.ai.ai_player import AIPlayer
from game.ui.context_menu import ContextMenu
from game.animation import AnimationManager, MoveAnimation, AttackAnimation, ArrowAnimation, PathMoveAnimation
from game.terrain import TerrainMap
from game.hex_utils import HexGrid, HexCoord
from game.interfaces.game_state import IGameState
from game.visibility import FogOfWar, VisibilityState

class GameState(IGameState):
    def __init__(self, battle_config=None, vs_ai=True):
        if battle_config:
            self.board_width = battle_config['board_size'][0]
            self.board_height = battle_config['board_size'][1]
            self.knights_per_player = battle_config['knights']
            self.castles_per_player = battle_config['castles']
        else:
            self.board_width = 16
            self.board_height = 12
            self.knights_per_player = 3
            self.castles_per_player = 1
        
        self.tile_size = 64
        
        # Camera/viewport system
        self.camera_x = 0
        self.camera_y = 0
        self.screen_width = 1024
        self.screen_height = 768
        
        self.castles = []
        self.knights = []
        self.current_player = 1
        self.selected_knight = None
        self.possible_moves = []
        self.turn_number = 1
        
        self.vs_ai = vs_ai
        self.ai_player = AIPlayer(2, 'medium') if vs_ai else None
        self.ai_thinking = False
        self.ai_turn_delay = 0
        
        self.context_menu = ContextMenu()
        self.current_action = None
        self.attack_targets = []
        self.enemy_info_unit = None  # Track enemy unit to display info
        self.terrain_info = None  # Track terrain info to display
        
        self.animation_manager = AnimationManager()
        self.pending_positions = {}  # Track where knights are moving to
        
        self.terrain_map = TerrainMap(self.board_width, self.board_height)
        
        # Hex layout for coordinate conversions
        from game.hex_layout import HexLayout
        self.hex_layout = HexLayout(hex_size=36, orientation='flat')
        
        # Message system for combat feedback
        self.messages = []  # List of (message, timestamp, priority) tuples
        self.message_duration = 3.0  # Seconds to display each message
        
        # Debug options
        self.show_coordinates = False
        
        # Fog of War system
        self.fog_of_war = FogOfWar(self.board_width, self.board_height, 2)  # 2 players
        
        self._init_game()
        
        # Center camera on player 1's starting area
        if self.knights:
            player1_knights = [k for k in self.knights if k.player_id == 1]
            if player1_knights:
                avg_x = sum(k.x for k in player1_knights) / len(player1_knights)
                avg_y = sum(k.y for k in player1_knights) / len(player1_knights)
                self.center_camera_on_tile(int(avg_x), int(avg_y))
    
    def _init_game(self):
        
        # Place castles
        castle_spacing = self.board_height // (self.castles_per_player + 1)
        for i in range(self.castles_per_player):
            y_pos = castle_spacing * (i + 1)
            self.castles.append(Castle(2, y_pos, 1))
            self.castles.append(Castle(self.board_width - 3, y_pos, 2))
        
        # Knight names and classes for variety
        knight_names_p1 = ["Sir Lancelot", "Robin Hood", "Sir Galahad", "Sir Kay", "Sir Gawain", 
                          "Sir Percival", "Sir Tristan", "Sir Bedivere"]
        knight_names_p2 = ["Black Knight", "Dark Archer", "Shadow Rider", "Dark Mage", "Iron Lord",
                          "Death Knight", "Void Walker", "Night Hunter"]
        knight_classes = [KnightClass.WARRIOR, KnightClass.ARCHER, KnightClass.CAVALRY, KnightClass.MAGE]
        
        # Place knights for player 1
        knight_spacing = self.board_height // (self.knights_per_player + 1)
        for i in range(self.knights_per_player):
            y_pos = knight_spacing * (i + 1)
            x_pos = 4 if i % 2 == 0 else 5
            
            # Find valid position if terrain is impassable
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos is None:
                print(f"Warning: Could not find valid position for player 1 knight {i}")
                continue
            
            x_pos, y_pos = valid_pos
            knight_class = knight_classes[i % len(knight_classes)]
            knight = UnitFactory.create_unit(knight_names_p1[i % len(knight_names_p1)], knight_class, x_pos, y_pos)
            knight.player_id = 1
            self.knights.append(knight)
        
        # Place knights for player 2
        for i in range(self.knights_per_player):
            y_pos = knight_spacing * (i + 1)
            x_pos = self.board_width - 5 if i % 2 == 0 else self.board_width - 6
            
            # Find valid position if terrain is impassable
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos is None:
                print(f"Warning: Could not find valid position for player 2 knight {i}")
                continue
            
            x_pos, y_pos = valid_pos
            knight_class = knight_classes[i % len(knight_classes)]
            knight = UnitFactory.create_unit(knight_names_p2[i % len(knight_names_p2)], knight_class, x_pos, y_pos)
            knight.player_id = 2
            self.knights.append(knight)
        
        # Check initial cavalry disruption for all units
        from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
        for knight in self.knights:
            check_cavalry_disruption_for_terrain(knight, self)
            
        # Initialize fog of war visibility
        self._update_all_fog_of_war()
    
    def _find_valid_position_near(self, x: int, y: int, max_distance: int = 3) -> Optional[tuple[int, int]]:
        """Find a valid position near the given position where terrain is passable.
        
        Returns a tuple (x, y) of a valid position, or None if no valid position found.
        """
        # First check if the original position is valid
        if self._is_position_valid_for_placement(x, y):
            return (x, y)
            
        # Search in expanding rectangles for simplicity
        for distance in range(1, max_distance + 1):
            # Check positions in a square around the original position
            positions_to_check = []
            
            # Top and bottom rows
            for dx in range(-distance, distance + 1):
                positions_to_check.append((x + dx, y - distance))
                positions_to_check.append((x + dx, y + distance))
            
            # Left and right columns (excluding corners already checked)
            for dy in range(-distance + 1, distance):
                positions_to_check.append((x - distance, y + dy))
                positions_to_check.append((x + distance, y + dy))
            
            # Check each position
            for new_x, new_y in positions_to_check:
                if (0 <= new_x < self.board_width and 
                    0 <= new_y < self.board_height and
                    self._is_position_valid_for_placement(new_x, new_y)):
                    return (new_x, new_y)
                    
        return None
    
    def _is_position_valid_for_placement(self, x: int, y: int) -> bool:
        """Check if a position is valid for placing a unit.
        
        Position is valid if:
        - Within board bounds
        - Terrain is passable
        - No other unit at this position
        - Not on a castle
        """
        # Check bounds
        if not (0 <= x < self.board_width and 0 <= y < self.board_height):
            return False
            
        # Check terrain
        if self.terrain_map:
            terrain = self.terrain_map.get_terrain(x, y)
            if terrain and not terrain.passable:
                return False
        
        # Check for other units
        for knight in self.knights:
            if knight.x == x and knight.y == y:
                return False
                
        # Check for castles
        for castle in self.castles:
            if hasattr(castle, 'contains_position') and castle.contains_position(x, y):
                return False
                
        return True
    
    def add_message(self, message, priority=1):
        """Add a message to display. Higher priority messages display longer."""
        import time
        self.messages.append((message, time.time(), priority))
    
    def update_messages(self, dt):
        """Update message display times and remove expired messages"""
        import time
        current_time = time.time()
        self.messages = [(msg, timestamp, priority) for msg, timestamp, priority in self.messages 
                        if current_time - timestamp < self.message_duration * priority]
    
    def update(self, dt):
        # Update animations
        self.animation_manager.update(dt)
        
        # Update messages
        self.update_messages(dt)
        
        # Clean up dead knights after animations
        self._cleanup_dead_knights()
        
        # Update ZOC status for all units
        self._update_zoc_status()
        
        # Don't process AI or input during animations
        if self.animation_manager.is_animating():
            return
        
        # Update fog of war after animations complete
        if hasattr(self, '_fog_update_needed'):
            self._update_all_fog_of_war()
            self._fog_update_needed = False
        
        if self.vs_ai and self.current_player == 2 and not self.ai_thinking:
            self.ai_thinking = True
            self.ai_turn_delay = 0.5
        
        if self.ai_thinking:
            self.ai_turn_delay -= dt
            if self.ai_turn_delay <= 0:
                self._execute_ai_turn()
                self.ai_thinking = False
    
    def _cleanup_dead_knights(self):
        """Remove knights with 0 or less soldiers"""
        had_dead_knights = any(k.soldiers <= 0 for k in self.knights)
        self.knights = [k for k in self.knights if k.soldiers > 0]
        
        # Update fog of war if any units were removed
        if had_dead_knights:
            self._update_all_fog_of_war()
    
    def set_camera_position(self, x, y):
        """Set camera position with bounds checking"""
        # Calculate max camera positions to keep board in view
        max_camera_x = max(0, self.board_width * self.tile_size - self.screen_width)
        max_camera_y = max(0, self.board_height * self.tile_size - self.screen_height)
        
        self.camera_x = max(0, min(x, max_camera_x))
        self.camera_y = max(0, min(y, max_camera_y))
    
    def move_camera(self, dx, dy):
        """Move camera by delta amount"""
        self.set_camera_position(self.camera_x + dx, self.camera_y + dy)
    
    def center_camera_on_tile(self, tile_x, tile_y):
        """Center camera on a specific tile"""
        pixel_x = tile_x * self.tile_size + self.tile_size // 2
        pixel_y = tile_y * self.tile_size + self.tile_size // 2
        
        camera_x = pixel_x - self.screen_width // 2
        camera_y = pixel_y - self.screen_height // 2
        
        self.set_camera_position(camera_x, camera_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = world_x - self.camera_x
        screen_y = world_y - self.camera_y
        return screen_x, screen_y
    
    def _update_zoc_status(self):
        """Update Zone of Control status for all knights"""
        for knight in self.knights:
            in_zoc, enemy = knight.is_in_enemy_zoc(self)
            knight.in_enemy_zoc = in_zoc
            knight.engaged_with = enemy if in_zoc else None
    
    def _execute_ai_turn(self):
        self.ai_player.execute_turn(self)
        self.end_turn()
    
    def select_knight(self, x, y):
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        for knight in self.knights:
            if knight.x == tile_x and knight.y == tile_y and knight.player_id == self.current_player:
                self.selected_knight = knight
                knight.selected = True
                if knight.can_move():
                    self.possible_moves = knight.get_possible_moves(self.board_width, self.board_height, self.terrain_map, self)
                    self.possible_moves = self._filter_valid_moves(self.possible_moves)
                return True
        
        self.deselect_knight()
        return False
    
    def deselect_knight(self):
        if self.selected_knight:
            self.selected_knight.selected = False
        self.selected_knight = None
        self.possible_moves = []
        self.current_action = None
        self.attack_targets = []
        self.context_menu.hide()
    
    def _filter_valid_moves(self, moves):
        valid_moves = []
        for move_x, move_y in moves:
            if not self._is_position_occupied(move_x, move_y, self.selected_knight):
                valid_moves.append((move_x, move_y))
        return valid_moves
    
    def _is_position_occupied(self, x, y, exclude_knight=None):
        """Check if a position is occupied by a knight, castle, or will be occupied (pending move)"""
        # Check castle positions
        for castle in self.castles:
            if castle.contains_position(x, y):
                return True
        
        # Check current knight positions (excluding garrisoned units)
        for knight in self.knights:
            if knight != exclude_knight and not knight.is_garrisoned and knight.x == x and knight.y == y:
                return True
        
        # Check pending positions (knights that are moving)
        for knight_id, pos in self.pending_positions.items():
            if pos == (x, y):
                # Make sure this pending position is not from the excluded knight
                for knight in self.knights:
                    if id(knight) == knight_id and knight != exclude_knight:
                        return True
        
        return False
    
    def move_selected_knight(self, x, y):
        if not self.selected_knight:
            return False
        
        # Use hex layout to convert pixel coordinates to hex coordinates
        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
        
        if (tile_x, tile_y) in self.possible_moves:
            # Use the movement behavior to get the optimal path
            move_behavior = self.selected_knight.behaviors.get('move')
            if move_behavior:
                path = move_behavior.get_path_to(self.selected_knight, self, tile_x, tile_y)
                
                if path:
                    # Calculate total AP cost for the path
                    total_ap_cost = 0
                    current_pos = (self.selected_knight.x, self.selected_knight.y)
                    for next_pos in path:
                        step_cost = move_behavior.get_ap_cost(current_pos, next_pos, self.selected_knight, self)
                        total_ap_cost += step_cost
                        current_pos = next_pos
                    
                    # Consume AP and mark as moved
                    self.selected_knight.action_points -= total_ap_cost
                    self.selected_knight.has_moved = True
                    
                    # Track pending position
                    self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)
                    
                    # Create path animation - shows the optimal route
                    anim = PathMoveAnimation(self.selected_knight, path, step_duration=0.25, game_state=self)
                    self.animation_manager.add_animation(anim)
                    
                    self.possible_moves = []
                    self._fog_update_needed = True  # Update fog after movement
                    return True
            else:
                # Fallback to direct movement if no movement behavior
                self.selected_knight.consume_move_ap()
                self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)
                start_x, start_y = self.selected_knight.x, self.selected_knight.y
                anim = MoveAnimation(self.selected_knight, start_x, start_y, tile_x, tile_y, game_state=self)
                self.animation_manager.add_animation(anim)
                self.possible_moves = []
                self._fog_update_needed = True  # Update fog after movement
                return True
        return False
    
    def get_knight_at(self, tile_x, tile_y):
        for knight in self.knights:
            if knight.x == tile_x and knight.y == tile_y:
                return knight
        return None
    
    def get_castle_at(self, tile_x, tile_y):
        for castle in self.castles:
            if castle.contains_position(tile_x, tile_y):
                return castle
        return None
    
    def attack_with_selected_knight(self, x, y):
        if not self.selected_knight or not self.selected_knight.can_attack():
            return False
        
        # Use hex layout to convert pixel coordinates to hex coordinates
        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
        
        # Calculate hex distance for attack range
        hex_grid = HexGrid()
        attacker_hex = hex_grid.offset_to_axial(self.selected_knight.x, self.selected_knight.y)
        target_hex = hex_grid.offset_to_axial(tile_x, tile_y)
        distance = attacker_hex.distance_to(target_hex)
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3
        
        if distance <= attack_range:
            target = self.get_knight_at(tile_x, tile_y)
            if target and target.player_id != self.current_player:
                # Get terrain for combat modifiers
                attacker_terrain = self.terrain_map.get_terrain(self.selected_knight.x, self.selected_knight.y)
                target_terrain = self.terrain_map.get_terrain(target.x, target.y)
                
                # Use attack behavior if available
                if hasattr(self.selected_knight, 'behaviors') and 'attack' in self.selected_knight.behaviors:
                    result = self.selected_knight.behaviors['attack'].execute(self.selected_knight, self, target)
                    if result['success']:
                        damage = result['damage']
                        counter_damage = result.get('counter_damage', 0)
                        attack_angle = result.get('attack_angle', None)
                        extra_morale_penalty = result.get('extra_morale_penalty', 0)
                        should_check_routing = result.get('should_check_routing', False)
                        
                        # Create attack animation with facing info
                        anim = AttackAnimation(self.selected_knight, target, damage, counter_damage,
                                             attack_angle=attack_angle, 
                                             extra_morale_penalty=extra_morale_penalty,
                                             should_check_routing=should_check_routing)
                        self.animation_manager.add_animation(anim)
                else:
                    # Fallback to old method
                    damage = self.selected_knight.calculate_damage(target, attacker_terrain, target_terrain)
                    self.selected_knight.consume_attack_ap()
                    
                    counter_damage = 0
                    if distance == 1:  # Melee range
                        counter_damage = target.calculate_counter_damage(self.selected_knight, attacker_terrain, target_terrain)
                    
                    anim = AttackAnimation(self.selected_knight, target, damage, counter_damage)
                    self.animation_manager.add_animation(anim)
                
                # Add combat message
                if counter_damage > 0:
                    self.add_message(f"{self.selected_knight.name} attacks {target.name} for {damage} damage! Takes {counter_damage} in return!")
                else:
                    self.add_message(f"{self.selected_knight.name} attacks {target.name} for {damage} damage!")
                
                # Death will be handled after animation in update
                return True
        
        return False
    
    def charge_with_selected_knight(self, x, y):
        """Execute cavalry charge"""
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return False
        
        # Use hex layout to convert pixel coordinates to hex coordinates
        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
        
        # Find target at clicked position
        target = self.get_knight_at(tile_x, tile_y)
        if target and target.player_id != self.current_player:
            # Store original positions
            start_x, start_y = self.selected_knight.x, self.selected_knight.y
            target_start_x, target_start_y = target.x, target.y
            
            # Execute charge
            success, message = self.selected_knight.execute_charge(target, self)
            if success:
                # Create animation for charge
                from game.animation import MoveAnimation
                
                # Check if target was pushed (compare positions)
                if target.x != target_start_x or target.y != target_start_y:
                    # Target was pushed, cavalry moves to target's original position
                    anim = MoveAnimation(self.selected_knight, start_x, start_y, target_start_x, target_start_y, game_state=self)
                    self.animation_manager.add_animation(anim)
                    self.selected_knight.x = target_start_x
                    self.selected_knight.y = target_start_y
                # If target wasn't pushed, cavalry stays in place (crushing charge)
                
                self.add_message(message, priority=2)  # Higher priority for special abilities
                return True
        
        return False
    
    def end_turn(self):
        for knight in self.knights:
            if knight.player_id == self.current_player:
                knight.end_turn()
        
        for castle in self.castles:
            if castle.player_id == self.current_player:
                enemies = castle.get_enemies_in_range(self.knights)
                if enemies:
                    damages = castle.shoot_arrows(enemies)
                    
                    # Create arrow animation - animation will apply damage when arrows hit
                    if damages:
                        anim = ArrowAnimation(castle, enemies, [d[1] for d in damages])
                        self.animation_manager.add_animation(anim)
                        
                        # Add message for castle archer volleys
                        total_damage = sum(d[1] for d in damages)
                        self.add_message(f"Castle archers fire! {total_damage} total damage dealt.")
        
        self.current_player = 2 if self.current_player == 1 else 1
        if self.current_player == 1:
            self.turn_number += 1
        
        self.deselect_knight()
        
        for castle in self.castles:
            if castle.player_id == self.current_player:
                castle.end_turn()
    
    def check_victory(self):
        player1_knights = [k for k in self.knights if k.player_id == 1]
        player2_knights = [k for k in self.knights if k.player_id == 2]
        
        if not player1_knights or self.castles[0].is_destroyed():
            return 2
        elif not player2_knights or self.castles[1].is_destroyed():
            return 1
        
        return None
    
    def set_action_mode(self, action):
        if action == 'move' and self.selected_knight and self.selected_knight.can_move():
            self.current_action = 'move'
            self.possible_moves = self.selected_knight.get_possible_moves(self.board_width, self.board_height, self.terrain_map, self)
            self.possible_moves = self._filter_valid_moves(self.possible_moves)
        elif action == 'attack' and self.selected_knight and self.selected_knight.can_attack():
            self.current_action = 'attack'
            self.attack_targets = self._get_attack_targets()
        elif action == 'charge' and self.selected_knight:
            self.current_action = 'charge'
            self.attack_targets = self._get_charge_targets()
        elif action == 'enter_garrison':
            self._enter_garrison()
        elif action == 'exit_garrison':
            self._exit_garrison()
        elif action == 'rotate_cw':
            self._rotate_selected_knight('clockwise')
        elif action == 'rotate_ccw':
            self._rotate_selected_knight('counter_clockwise')
        elif action == 'info':
            pass
        elif action == 'cancel':
            self.deselect_knight()
    
    def _enter_garrison(self):
        if not self.selected_knight or self.selected_knight.is_garrisoned:
            return
        
        # Find nearby castle
        for castle in self.castles:
            for tile_x, tile_y in castle.occupied_tiles:
                if abs(self.selected_knight.x - tile_x) + abs(self.selected_knight.y - tile_y) <= 1:
                    if castle.add_unit_to_garrison(self.selected_knight):
                        self.deselect_knight()
                        return
    
    def _exit_garrison(self):
        if not self.selected_knight or not self.selected_knight.is_garrisoned:
            return
        
        castle = self.selected_knight.garrison_location
        if castle:
            # Find empty adjacent tile
            for tile_x, tile_y in castle.occupied_tiles:
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_x, new_y = tile_x + dx, tile_y + dy
                    if (0 <= new_x < self.board_width and 0 <= new_y < self.board_height and
                        not self._is_position_occupied(new_x, new_y)):
                        castle.remove_unit_from_garrison(self.selected_knight)
                        self.selected_knight.x = new_x
                        self.selected_knight.y = new_y
                        return
    
    def _rotate_selected_knight(self, direction):
        """Rotate the selected knight in the specified direction"""
        if not self.selected_knight:
            return
            
        if hasattr(self.selected_knight, 'behaviors') and 'rotate' in self.selected_knight.behaviors:
            rotate_behavior = self.selected_knight.behaviors['rotate']
            result = rotate_behavior.execute(self.selected_knight, self, direction)
            
            if result['success']:
                self.add_message(result['message'])
            else:
                self.add_message(f"Cannot rotate: {result['reason']}")
    
    def _get_attack_targets(self):
        if not self.selected_knight:
            return []
        
        targets = []
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3
        hex_grid = HexGrid()
        attacker_hex = hex_grid.offset_to_axial(self.selected_knight.x, self.selected_knight.y)
        
        for knight in self.knights:
            if knight.player_id != self.current_player:
                # Check fog of war visibility
                if hasattr(self, 'fog_of_war'):
                    visibility = self.fog_of_war.get_visibility_state(self.current_player, knight.x, knight.y)
                    if visibility != VisibilityState.VISIBLE:
                        continue  # Skip invisible units
                
                target_hex = hex_grid.offset_to_axial(knight.x, knight.y)
                distance = attacker_hex.distance_to(target_hex)
                if distance <= attack_range:
                    targets.append((knight.x, knight.y))
        
        return targets
    
    def _get_charge_targets(self):
        """Get valid targets for cavalry charge"""
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return []
        
        targets = []
        hex_grid = HexGrid()
        cavalry_hex = hex_grid.offset_to_axial(self.selected_knight.x, self.selected_knight.y)
        
        # Check all adjacent hex positions
        neighbors = cavalry_hex.get_neighbors()
        for neighbor_hex in neighbors:
            check_x, check_y = hex_grid.axial_to_offset(neighbor_hex)
            
            # Check for enemy at this position
            for knight in self.knights:
                if (knight.player_id != self.current_player and 
                    knight.x == check_x and knight.y == check_y and 
                    not knight.is_garrisoned):
                    # Check fog of war visibility
                    if hasattr(self, 'fog_of_war'):
                        visibility = self.fog_of_war.get_visibility_state(self.current_player, knight.x, knight.y)
                        if visibility != VisibilityState.VISIBLE:
                            continue  # Skip invisible units
                    
                    # Check if we can actually charge this target
                    can_charge, _ = self.selected_knight.can_charge(knight, self)
                    if can_charge:
                        targets.append((check_x, check_y))
                    break
        
        return targets
    
    def _update_all_fog_of_war(self):
        """Update fog of war for all players"""
        for player_id in range(self.fog_of_war.num_players):
            self.fog_of_war.update_player_visibility(self, player_id)
    
    def _update_fog_of_war_for_player(self, player_id):
        """Update fog of war for a specific player"""
        self.fog_of_war.update_player_visibility(self, player_id)
    
    def get_unit_at(self, x, y):
        """Get unit at position (needed by fog of war system)"""
        return self.get_knight_at(x, y)
    
    @property
    def units(self):
        """Alias for knights to work with fog of war system"""
        return self.knights