import random
from game.entities.knight import KnightClass

class AIPlayer:
    def __init__(self, player_id, difficulty='medium'):
        self.player_id = player_id
        self.difficulty = difficulty
        self.thinking_time = 0.5
        
    def evaluate_position(self, game_state):
        score = 0
        
        for knight in game_state.knights:
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
                        # Check distance to any castle tile
                        min_distance = float('inf')
                        for tile_x, tile_y in castle.occupied_tiles:
                            distance = abs(knight.x - tile_x) + abs(knight.y - tile_y)
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
        
        return bonus
    
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
                
                for enemy in game_state.knights:
                    if enemy.player_id == self.player_id:
                        continue
                    
                    distance = abs(knight.x - enemy.x) + abs(knight.y - enemy.y)
                    if distance <= attack_range:
                        moves.append(('attack', knight, enemy))
        
        return moves
    
    def minimax(self, game_state, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return self.evaluate_position(game_state), None
        
        possible_moves = self.get_all_possible_moves(game_state)
        
        if not possible_moves:
            return self.evaluate_position(game_state), None
        
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
        import copy
        
        # Create a simplified copy without UI elements
        class SimplifiedGameState:
            def get_knight_at(self, tile_x, tile_y):
                for knight in self.knights:
                    if knight.x == tile_x and knight.y == tile_y:
                        return knight
                return None
        
        state_copy = SimplifiedGameState()
        state_copy.knights = copy.deepcopy(game_state.knights)
        state_copy.castles = copy.deepcopy(game_state.castles)
        state_copy.board_width = game_state.board_width
        state_copy.board_height = game_state.board_height
        state_copy.current_player = game_state.current_player
        
        # Ensure castles have the needed attributes for AI evaluation
        for castle in state_copy.castles:
            if not hasattr(castle, 'arrow_range'):
                castle.arrow_range = 3
            if not hasattr(castle, 'occupied_tiles'):
                castle.occupied_tiles = castle._get_occupied_tiles()
            if not hasattr(castle, 'garrisoned_units'):
                castle.garrisoned_units = []
        
        move_type = move[0]
        knight = None
        for k in state_copy.knights:
            if k.name == move[1].name and k.x == move[1].x and k.y == move[1].y:
                knight = k
                break
        
        if move_type == 'move':
            knight.move(move[2], move[3])
        elif move_type == 'attack':
            target = None
            for k in state_copy.knights:
                if k.name == move[2].name and k.x == move[2].x and k.y == move[2].y:
                    target = k
                    break
            if target:
                # Simulate combat with casualties
                damage = knight.calculate_damage(target)
                knight.consume_attack_ap()
                target.take_casualties(damage)
                if target.soldiers <= 0:
                    state_copy.knights.remove(target)
        
        return state_copy
    
    def choose_action(self, game_state):
        depth = {'easy': 1, 'medium': 2, 'hard': 3}.get(self.difficulty, 2)
        
        _, best_move = self.minimax(game_state, depth, float('-inf'), float('inf'), True)
        
        if best_move:
            return best_move
        
        possible_moves = self.get_all_possible_moves(game_state)
        if possible_moves:
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
                    start_x, start_y = knight.x, knight.y
                    knight.consume_move_ap()
                    
                    # Track pending position
                    game_state.pending_positions[id(knight)] = (action[2], action[3])
                    
                    # Add animation - animation will update position when complete
                    anim = MoveAnimation(knight, start_x, start_y, action[2], action[3], game_state=game_state)
                    game_state.animation_manager.add_animation(anim)
                    
                    actions_taken.append(f"{knight.name} moved to ({action[2]}, {action[3]})")
            
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
                    game_state.animation_manager.add_animation(anim)
                    
                    actions_taken.append(f"{knight.name} attacked {target.name} for {damage} damage")
        
        return actions_taken