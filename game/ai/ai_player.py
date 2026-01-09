import random
from game.entities.knight import KnightClass
from game.hex_utils import HexGrid
from game.visibility import VisibilityState

class AIPlayer:
    def __init__(self, player_id, difficulty='easy'):
        self.player_id = player_id
        self.difficulty = difficulty
        self.thinking_time = 0.5
        
    def evaluate_position(self, game_state):
        score = 0
        
        # Get fog of war system
        fog_of_war = getattr(game_state, 'fog_of_war', None)
        
        for knight in game_state.knights:
            # Only evaluate units we can see
            if fog_of_war and knight.player_id != self.player_id:
                visibility = fog_of_war.get_visibility_state(self.player_id, knight.x, knight.y)
                if visibility not in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                    continue  # Skip invisible units
            
            knight_value = self._get_knight_value(knight)
            position_bonus = self._get_position_bonus(knight, game_state)
            
            if knight.player_id == self.player_id:
                score += knight_value + position_bonus
            else:
                score -= knight_value + position_bonus
        
        for i, castle in enumerate(game_state.castles):
            castle_value = (castle.health / castle.max_health) * 1000
            if (i == 0 and self.player_id == 1) or (i == 1 and self.player_id == 2):
                score += castle_value
            else:
                score -= castle_value
                
            # Penalty for having knights in enemy castle range
            if castle.player_id != self.player_id:
                for knight in game_state.knights:
                    if knight.player_id == self.player_id:
                        # Check hex distance to any castle tile
                        hex_grid = HexGrid()
                        knight_hex = hex_grid.offset_to_axial(knight.x, knight.y)
                        min_distance = float('inf')
                        
                        for tile_x, tile_y in castle.occupied_tiles:
                            castle_hex = hex_grid.offset_to_axial(tile_x, tile_y)
                            distance = knight_hex.distance_to(castle_hex)
                            min_distance = min(min_distance, distance)
                        if min_distance <= castle.arrow_range and castle.get_total_archer_soldiers() > 0:
                            score -= 15
        
        return score
    
    def _get_knight_value(self, knight):
        base_values = {
            KnightClass.WARRIOR: 100,
            KnightClass.ARCHER: 120,
            KnightClass.CAVALRY: 110,
            KnightClass.MAGE: 150
        }
        
        base_value = base_values.get(knight.knight_class, 100)
        health_factor = knight.health / knight.max_health
        ap_factor = knight.action_points / knight.max_action_points
        
        return base_value * health_factor * (1 + ap_factor * 0.2)
    
    def _get_position_bonus(self, knight, game_state):
        bonus = 0
        
        center_x, center_y = game_state.board_width // 2, game_state.board_height // 2
        distance_to_center = abs(knight.x - center_x) + abs(knight.y - center_y)
        bonus += (10 - distance_to_center) * 2
        
        enemy_castle_idx = 0 if self.player_id == 2 else 1
        enemy_castle = game_state.castles[enemy_castle_idx]
        distance_to_enemy_castle = abs(knight.x - enemy_castle.center_x) + abs(knight.y - enemy_castle.center_y)
        bonus += (15 - distance_to_enemy_castle) * 3
        
        # Terrain position bonus
        if hasattr(game_state, 'terrain_map'):
            terrain = game_state.terrain_map.get_terrain(knight.x, knight.y)
            if terrain:
                # Defensive positions
                if terrain.defense_bonus > 0:
                    bonus += terrain.defense_bonus * 2
                # Avoid dangerous terrain
                if terrain.defense_bonus < 0:
                    bonus += terrain.defense_bonus * 3
        
        # Facing bonus - better to face enemies
        if hasattr(knight, 'facing'):
            facing_bonus = self._evaluate_facing_position(knight, game_state)
            bonus += facing_bonus
        
        return bonus
    
    def _evaluate_facing_position(self, knight, game_state):
        """Evaluate how well positioned unit is based on facing"""
        bonus = 0
        
        # Get fog of war system
        fog_of_war = getattr(game_state, 'fog_of_war', None)
        
        # Check threats from different directions
        for enemy in game_state.knights:
            if enemy.player_id == self.player_id:
                continue
                
            # Only consider visible enemies
            if fog_of_war:
                visibility = fog_of_war.get_visibility_state(self.player_id, enemy.x, enemy.y)
                if visibility not in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                    continue
                
            # Calculate distance
            dx = abs(knight.x - enemy.x)
            dy = abs(knight.y - enemy.y)
            distance = max(dx, dy)
            
            # Only consider nearby threats (but not on same position)
            if 0 < distance <= 3:
                # Check if enemy is behind us
                if hasattr(knight, 'facing'):
                    attack_angle = knight.facing.get_attack_angle(enemy.x, enemy.y, knight.x, knight.y)
                    
                    if attack_angle.is_rear:
                        # Heavy penalty for enemies behind us
                        bonus -= 30 / distance
                    elif attack_angle.is_flank:
                        # Moderate penalty for enemies on flank
                        bonus -= 15 / distance
                    else:
                        # Small bonus for facing enemies
                        bonus += 5 / distance
                        
                    # Extra penalty if enemy is cavalry behind us
                    if attack_angle.is_rear and enemy.knight_class == KnightClass.CAVALRY:
                        bonus -= 40 / distance
        
        return bonus
    
    def _evaluate_attack(self, attacker, target):
        """Evaluate the value of attacking a target, considering facing"""
        base_value = 100  # Base value for any attack
        
        # Value based on target
        target_value = self._get_knight_value(target)
        base_value += target_value * 0.5
        
        # Bonus for attacking damaged units
        health_percent = target.health / target.max_health
        if health_percent < 0.5:
            base_value += 50
        
        # Facing bonus
        if hasattr(target, 'facing'):
            attack_angle = target.facing.get_attack_angle(attacker.x, attacker.y, target.x, target.y)
            
            if attack_angle.is_rear:
                base_value += 100  # Huge bonus for rear attacks
                # Extra bonus if we're cavalry attacking rear
                if attacker.knight_class == KnightClass.CAVALRY:
                    base_value += 150
            elif attack_angle.is_flank:
                base_value += 50  # Good bonus for flank attacks
        
        # Consider if attack might cause routing
        if hasattr(target, 'morale') and target.morale < 50:
            base_value += 75  # Bonus for attacking low morale units
        
        return base_value
    
    def get_all_possible_moves(self, game_state):
        moves = []
        
        for knight in game_state.knights:
            if knight.player_id != self.player_id:
                continue
            
            if knight.can_move():
                terrain_map = game_state.terrain_map if hasattr(game_state, 'terrain_map') else None
                possible_positions = knight.get_possible_moves(game_state.board_width, game_state.board_height, terrain_map, game_state)
                for new_x, new_y in possible_positions:
                    # Check both current positions and pending positions
                    occupied = False
                    
                    # Check if position is currently occupied
                    if game_state.get_knight_at(new_x, new_y):
                        occupied = True
                    
                    # Check if position will be occupied (pending moves)
                    if hasattr(game_state, 'pending_positions'):
                        for pending_knight_id, pending_pos in game_state.pending_positions.items():
                            if pending_pos == (new_x, new_y) and pending_knight_id != id(knight):
                                occupied = True
                                break
                    
                    if not occupied:
                        moves.append(('move', knight, new_x, new_y))
            
            if knight.can_attack():
                attack_range = 1 if knight.knight_class != KnightClass.ARCHER else 3
                
                # Get fog of war system
                fog_of_war = getattr(game_state, 'fog_of_war', None)
                
                for enemy in game_state.knights:
                    if enemy.player_id == self.player_id:
                        continue
                    
                    # Only attack visible enemies
                    if fog_of_war:
                        visibility = fog_of_war.get_visibility_state(self.player_id, enemy.x, enemy.y)
                        if visibility != VisibilityState.VISIBLE:
                            continue  # Need full visibility to attack
                    
                    distance = abs(knight.x - enemy.x) + abs(knight.y - enemy.y)
                    if distance <= attack_range:
                        # Calculate attack value considering facing
                        attack_value = self._evaluate_attack(knight, enemy)
                        moves.append(('attack', knight, enemy, attack_value))
        
        return moves
    
    def minimax(self, game_state, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return self.evaluate_position(game_state), None
        
        possible_moves = self.get_all_possible_moves(game_state)
        
        if not possible_moves:
            return self.evaluate_position(game_state), None
            
        # Move Ordering: Sort moves to improve Alpha-Beta efficiency
        # 1. Attacks (prioritize higher heuristic value)
        # 2. Strategic moves
        def move_priority(m):
            if m[0] == 'attack':
                return 1000 + m[3] # Index 3 is attack value
            return 0
            
        possible_moves.sort(key=move_priority, reverse=True)
            
        # Optimization: Prune moves if too many
        if len(possible_moves) > 10 and depth > 1:
            possible_moves = possible_moves[:10]
        
        best_move = None
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in possible_moves:
                game_state_copy = self._simulate_move(game_state, move)
                eval_score, _ = self.minimax(game_state_copy, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in possible_moves:
                game_state_copy = self._simulate_move(game_state, move)
                eval_score, _ = self.minimax(game_state_copy, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    def _simulate_move(self, game_state, move):
        from game.interfaces.game_state import IGameState
        
        # Create a simplified copy without UI elements
        class SimplifiedGameState(IGameState):
            def __init__(self):
                self._knights = []
                self._castles = []
                self._board_width = 0
                self._board_height = 0
                self._current_player = 1
                self._terrain_map = None
                
            @property
            def board_width(self):
                return self._board_width
            
            @property
            def board_height(self):
                return self._board_height
                
            @property
            def knights(self):
                return self._knights
                
            @property
            def castles(self):
                return self._castles
                
            @property
            def terrain_map(self):
                return self._terrain_map
                
            @property
            def current_player(self):
                return self._current_player
                
            def get_knight_at(self, tile_x, tile_y):
                for knight in self.knights:
                    if knight.x == tile_x and knight.y == tile_y:
                        return knight
                return None
        
        state_copy = SimplifiedGameState()
        # FAST CLONING instead of deepcopy
        state_copy._knights = [k.clone_for_simulation() for k in game_state.knights]
        # Castles are mostly static in simulation, shallow copy is fine for now
        import copy
        state_copy._castles = copy.copy(game_state.castles)
        
        state_copy._board_width = game_state.board_width
        state_copy._board_height = game_state.board_height
        state_copy._current_player = game_state.current_player
        # Copy terrain_map reference (static)
        if hasattr(game_state, 'terrain_map'):
            state_copy._terrain_map = game_state.terrain_map
        
        move_type = move[0]
        knight = None
        original_knight = move[1]
        
        for k in state_copy.knights:
            if k.name == original_knight.name and k.x == original_knight.x and k.y == original_knight.y:
                knight = k
                break
        
        if not knight:
             return state_copy

        if move_type == 'move':
            knight.move(move[2], move[3])
        elif move_type == 'attack':
            target = None
            target_ref = move[2]
            for k in state_copy.knights:
                if k.name == target_ref.name and k.x == target_ref.x and k.y == target_ref.y:
                    target = k
                    break
            if target:
                attacker_terrain = None
                target_terrain = None
                if state_copy.terrain_map:
                    attacker_terrain = state_copy.terrain_map.get_terrain(knight.x, knight.y)
                    target_terrain = state_copy.terrain_map.get_terrain(target.x, target.y)
                
                damage = knight.calculate_damage(target, attacker_terrain, target_terrain)
                knight.consume_attack_ap()
                target.take_casualties(damage)
                if target.soldiers <= 0:
                    state_copy.knights.remove(target)
        
        return state_copy
    
    def choose_action(self, game_state):
        depth = {'easy': 1, 'medium': 2, 'hard': 3}.get(self.difficulty, 1)
        import time
        t0 = time.time()
        
        # Log start of thinking
        print(f"AI Thinking... Depth: {depth}")
        
        _, best_move = self.minimax(game_state, depth, float('-inf'), float('inf'), True)
        
        dt = time.time() - t0
        print(f"AI Action Chosen in {dt:.2f}s: {best_move[0] if best_move else 'None'}")
        
        if best_move:
            return best_move
        
        possible_moves = self.get_all_possible_moves(game_state)
        if possible_moves:
            # Sort attacks by value if difficulty is medium or hard
            if self.difficulty in ['medium', 'hard']:
                attack_moves = [m for m in possible_moves if m[0] == 'attack' and len(m) > 3]
                if attack_moves:
                    # Sort by attack value (highest first)
                    attack_moves.sort(key=lambda m: m[3], reverse=True)
                    # Take best attack with some randomness for medium difficulty
                    if self.difficulty == 'medium' and random.random() < 0.3:
                        return random.choice(attack_moves[:3] if len(attack_moves) >= 3 else attack_moves)
                    else:
                        return attack_moves[0]
            
            return random.choice(possible_moves)
        
        return None
    
    def execute_turn(self, game_state):
        from game.animation import MoveAnimation, AttackAnimation
        actions_taken = []
        
        for _ in range(5):
            action = self.choose_action(game_state)
            if not action:
                break
            
            move_type = action[0]
            knight = action[1]
            
            if move_type == 'move':
                if knight.can_move():
                    # Select the knight and use the game state's movement method to track paths
                    game_state.selected_knight = knight
                    game_state.possible_moves = knight.get_possible_moves(
                        game_state.board_width, game_state.board_height, 
                        game_state.terrain_map, game_state
                    )
                    
                    # Use the proper movement method that tracks paths
                    target_x, target_y = action[2], action[3]
                    success = game_state.move_selected_knight(target_x * 64, target_y * 64)
                    
                    if success:
                        actions_taken.append(f"{knight.name} moved to ({target_x}, {target_y})")
                    else:
                        # Fallback to direct movement if the proper method fails
                        start_x, start_y = knight.x, knight.y
                        knight.consume_move_ap()
                        game_state.pending_positions[id(knight)] = (target_x, target_y)
                        anim = MoveAnimation(knight, start_x, start_y, target_x, target_y, game_state=game_state)
                        game_state.animation_coordinator.animation_manager.add_animation(anim)
                        actions_taken.append(f"{knight.name} moved to ({target_x}, {target_y})")
            
            elif move_type == 'attack':
                if knight.can_attack():
                    target = action[2]
                    # Get terrain for combat calculation
                    attacker_terrain = None
                    target_terrain = None
                    if hasattr(game_state, 'terrain_map'):
                        attacker_terrain = game_state.terrain_map.get_terrain(knight.x, knight.y)
                        target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
                    
                    damage = knight.calculate_damage(target, attacker_terrain, target_terrain)
                    knight.consume_attack_ap()
                    
                    # Add animation - animation will apply damage when projectile hits
                    anim = AttackAnimation(knight, target, damage)
                    game_state.animation_coordinator.animation_manager.add_animation(anim)
                    
                    actions_taken.append(f"{knight.name} attacked {target.name} for {damage} damage")
        
        return actions_taken