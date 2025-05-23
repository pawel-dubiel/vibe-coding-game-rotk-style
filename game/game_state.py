import pygame
from game.entities.knight import Knight, KnightClass
from game.entities.castle import Castle
from game.ai.ai_player import AIPlayer
from game.ui.context_menu import ContextMenu
from game.animation import AnimationManager, MoveAnimation, AttackAnimation, ArrowAnimation
from game.terrain import TerrainMap

class GameState:
    def __init__(self, vs_ai=True):
        self.board_width = 16
        self.board_height = 12
        self.tile_size = 64
        
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
        
        self.animation_manager = AnimationManager()
        self.pending_positions = {}  # Track where knights are moving to
        
        self.terrain_map = TerrainMap(self.board_width, self.board_height)
        
        # Message system for combat feedback
        self.messages = []  # List of (message, timestamp, priority) tuples
        self.message_duration = 3.0  # Seconds to display each message
        
        self._init_game()
    
    def _init_game(self):
        self.castles.append(Castle(2, 6, 1))
        self.castles.append(Castle(13, 6, 2))
        
        self.knights.append(Knight("Sir Lancelot", KnightClass.WARRIOR, 4, 5))
        self.knights.append(Knight("Robin Hood", KnightClass.ARCHER, 4, 7))
        self.knights.append(Knight("Sir Galahad", KnightClass.CAVALRY, 3, 6))
        
        self.knights.append(Knight("Black Knight", KnightClass.WARRIOR, 11, 5))
        self.knights.append(Knight("Dark Archer", KnightClass.ARCHER, 11, 7))
        self.knights.append(Knight("Merlin", KnightClass.MAGE, 12, 6))
        
        for i, knight in enumerate(self.knights):
            knight.player_id = 1 if i < 3 else 2
    
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
        self.knights = [k for k in self.knights if k.soldiers > 0]
    
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
        
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        if (tile_x, tile_y) in self.possible_moves:
            # Consume AP without moving yet
            self.selected_knight.consume_move_ap()
            
            # Track pending position
            self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)
            
            # Create move animation - animation will update position when complete
            start_x, start_y = self.selected_knight.x, self.selected_knight.y
            anim = MoveAnimation(self.selected_knight, start_x, start_y, tile_x, tile_y, game_state=self)
            self.animation_manager.add_animation(anim)
            
            self.possible_moves = []
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
        
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        distance = abs(self.selected_knight.x - tile_x) + abs(self.selected_knight.y - tile_y)
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3
        
        if distance <= attack_range:
            target = self.get_knight_at(tile_x, tile_y)
            if target and target.player_id != self.current_player:
                # Get terrain for combat modifiers
                attacker_terrain = self.terrain_map.get_terrain(self.selected_knight.x, self.selected_knight.y)
                target_terrain = self.terrain_map.get_terrain(target.x, target.y)
                
                # Calculate damage with terrain modifiers and consume AP without applying damage yet
                damage = self.selected_knight.calculate_damage(target, attacker_terrain, target_terrain)
                self.selected_knight.consume_attack_ap()
                
                # Calculate counter damage for melee attacks (not ranged)
                counter_damage = 0
                if distance == 1:  # Melee range
                    counter_damage = target.calculate_counter_damage(self.selected_knight, attacker_terrain, target_terrain)
                
                # Create attack animation - animation will apply damage when projectile hits
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
        
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
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
    
    def _get_attack_targets(self):
        if not self.selected_knight:
            return []
        
        targets = []
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3
        
        for knight in self.knights:
            if knight.player_id != self.current_player:
                distance = abs(self.selected_knight.x - knight.x) + abs(self.selected_knight.y - knight.y)
                if distance <= attack_range:
                    targets.append((knight.x, knight.y))
        
        return targets
    
    def _get_charge_targets(self):
        """Get valid targets for cavalry charge"""
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return []
        
        targets = []
        # Check all adjacent positions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            check_x = self.selected_knight.x + dx
            check_y = self.selected_knight.y + dy
            
            # Check for enemy at this position
            for knight in self.knights:
                if (knight.player_id != self.current_player and 
                    knight.x == check_x and knight.y == check_y and 
                    not knight.is_garrisoned):
                    # Check if we can actually charge this target
                    can_charge, _ = self.selected_knight.can_charge(knight, self)
                    if can_charge:
                        targets.append((check_x, check_y))
                    break
        
        return targets