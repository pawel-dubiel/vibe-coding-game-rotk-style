import pygame
from enum import Enum
from game.hex_utils import HexCoord, HexGrid
from collections import deque

class KnightClass(Enum):
    WARRIOR = "Warrior"
    ARCHER = "Archer"
    CAVALRY = "Cavalry"
    MAGE = "Mage"

class Knight:
    def __init__(self, name, knight_class, x, y):
        self.name = name
        self.knight_class = knight_class
        self.x = x
        self.y = y
        
        self.max_action_points = self._get_max_ap()
        self.action_points = self.max_action_points
        
        # Unit composition
        self.max_soldiers = self._get_max_soldiers()
        self.soldiers = self.max_soldiers
        self.base_attack_per_soldier = self._get_attack_per_soldier()
        self.base_defense = self._get_defense()
        self.movement_range = self._get_movement_range()
        
        # Combat stats
        self.morale = 100  # Affects combat effectiveness
        self.will = 100  # Resource for special abilities
        self.max_will = 100
        self.formation_width = self._get_formation_width()  # How many can fight at once
        
        self.selected = False
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False  # For special abilities
        self.is_garrisoned = False
        self.garrison_location = None
        self.player_id = None  # Set by game state
        
        # Zone of Control and routing
        self.in_enemy_zoc = False
        self.is_routing = False  # Unit is fleeing
        self.engaged_with = None  # Enemy unit we're engaged with
        
    def _get_max_ap(self):
        ap_by_class = {
            KnightClass.WARRIOR: 8,   # High AP for heavy infantry
            KnightClass.ARCHER: 7,    # Good AP for ranged units
            KnightClass.CAVALRY: 10,  # Highest AP for mobile units
            KnightClass.MAGE: 6       # Moderate AP for spellcasters
        }
        return ap_by_class.get(self.knight_class, 7)
    
    def _get_max_soldiers(self):
        soldiers_by_class = {
            KnightClass.WARRIOR: 100,
            KnightClass.ARCHER: 80,
            KnightClass.CAVALRY: 50,
            KnightClass.MAGE: 30
        }
        return soldiers_by_class.get(self.knight_class, 100)
    
    def _get_attack_per_soldier(self):
        attack_by_class = {
            KnightClass.WARRIOR: 1.0,
            KnightClass.ARCHER: 1.5,
            KnightClass.CAVALRY: 2.0,
            KnightClass.MAGE: 3.0
        }
        return attack_by_class.get(self.knight_class, 1.0)
    
    def _get_formation_width(self):
        """How many soldiers can fight at once (frontage)"""
        width_by_class = {
            KnightClass.WARRIOR: 20,
            KnightClass.ARCHER: 30,  # Can shoot from multiple ranks
            KnightClass.CAVALRY: 15,  # Need space for horses
            KnightClass.MAGE: 10   # Area effect attacks
        }
        return width_by_class.get(self.knight_class, 20)
    
    def _get_defense(self):
        defense_by_class = {
            KnightClass.WARRIOR: 15,
            KnightClass.ARCHER: 5,
            KnightClass.CAVALRY: 10,
            KnightClass.MAGE: 5
        }
        return defense_by_class.get(self.knight_class, 10)
    
    def _get_movement_range(self):
        range_by_class = {
            KnightClass.WARRIOR: 3,
            KnightClass.ARCHER: 4,
            KnightClass.CAVALRY: 6,
            KnightClass.MAGE: 3
        }
        return range_by_class.get(self.knight_class, 3)
    
    def can_move(self):
        """Check if unit can move"""
        if self.action_points < 1 or self.has_moved:
            return False
        
        # Routing units always try to move
        if self.is_routing:
            return True
        
        # Check if in enemy ZOC and can't disengage
        if self.in_enemy_zoc and not self.can_disengage_from_zoc():
            return False
        
        return True
    
    def can_attack(self):
        # Check if we have enough AP for attack based on unit type
        ap_needed = 3  # Default
        if self.knight_class == KnightClass.WARRIOR:
            ap_needed = 4
        elif self.knight_class == KnightClass.ARCHER:
            ap_needed = 2
        elif self.knight_class == KnightClass.CAVALRY:
            ap_needed = 3
        elif self.knight_class == KnightClass.MAGE:
            ap_needed = 2
            
        return self.action_points >= ap_needed and not self.has_acted
    
    def move(self, new_x, new_y):
        if self.can_move():
            self.x = new_x
            self.y = new_y
            self.action_points -= 1
            self.has_moved = True
            return True
        return False
    
    def consume_move_ap(self):
        """Consume action points for move without changing position"""
        if self.can_move():
            self.action_points -= 1
            self.has_moved = True
            return True
        return False
    
    @property
    def health(self):
        """Health is now based on soldier count"""
        return (self.soldiers / self.max_soldiers) * 100
    
    @property
    def max_health(self):
        return 100
    
    @property
    def attack(self):
        """Total attack based on soldiers and formation"""
        return self.get_effective_soldiers() * self.base_attack_per_soldier
    
    @property 
    def defense(self):
        """Defense value with morale modifier"""
        return self.base_defense * (self.morale / 100)
    
    def get_effective_soldiers(self, terrain=None):
        """Get number of soldiers that can actually fight based on formation and terrain"""
        effective_width = self.formation_width
        
        # Terrain affects frontage
        if terrain:
            if terrain.type.value in ["Forest", "Hills"]:
                effective_width *= 0.7  # Reduced frontage in difficult terrain
            elif terrain.type.value == "Bridge":
                effective_width *= 0.5  # Very limited frontage on bridges
            elif terrain.type.value in ["Plains", "Road"]:
                if self.knight_class == KnightClass.CAVALRY:
                    effective_width *= 1.2  # Cavalry gets bonus frontage on open terrain
        
        # Can't have more effective soldiers than actual soldiers
        return min(int(effective_width), self.soldiers)
    
    def calculate_damage(self, target, attacker_terrain=None, target_terrain=None):
        """Calculate damage based on unit composition and terrain"""
        # Get effective soldiers that can fight
        attacking_soldiers = self.get_effective_soldiers(attacker_terrain)
        base_damage = attacking_soldiers * self.base_attack_per_soldier
        
        # Apply terrain combat modifier
        if attacker_terrain:
            base_damage *= attacker_terrain.get_combat_modifier_for_unit(self.knight_class)
        
        # Apply morale modifier
        base_damage *= (self.morale / 100)
        
        # Calculate defense
        target_defense = target.defense
        if target_terrain:
            target_defense += target_terrain.defense_bonus
            
        # Special case: garrisoned units get castle defense
        if target.is_garrisoned:
            target_defense += 20  # Castle walls bonus
        
        # Calculate casualties instead of HP damage - more decisive battles
        damage_ratio = base_damage / (base_damage + target_defense)
        
        # Base casualties increased to 25% of attacking force
        base_casualties = int(damage_ratio * attacking_soldiers * 0.25)
        
        # Bonus casualties for specific matchups
        if self.knight_class == KnightClass.CAVALRY and target.knight_class == KnightClass.ARCHER:
            base_casualties = int(base_casualties * 1.5)  # Cavalry devastates archers
        elif self.knight_class == KnightClass.ARCHER and self.knight_class == KnightClass.WARRIOR:
            base_casualties = int(base_casualties * 0.8)  # Warriors resist arrows better
        
        return min(base_casualties, target.soldiers)
    
    def calculate_counter_damage(self, attacker, attacker_terrain=None, defender_terrain=None):
        """Calculate damage defender deals back to attacker in melee"""
        # Archers being attacked in melee cannot counter effectively
        if self.knight_class == KnightClass.ARCHER:
            return 0
            
        # Counter damage calculations
        defending_soldiers = self.get_effective_soldiers(defender_terrain)
        base_damage = self.base_attack_per_soldier * defending_soldiers
        
        if defender_terrain:
            base_damage *= defender_terrain.get_combat_modifier_for_unit(self.knight_class)
        
        # Reduced morale effect for counter-attacks
        base_damage *= (self.morale / 200)  # Half morale effect
        
        # Calculate attacker's defense
        attacker_defense = self.base_defense
        if attacker_terrain:
            attacker_defense += attacker_terrain.defense_bonus
            
        # Calculate casualties - counter attacks deal less damage (15% instead of 25%)
        damage_ratio = base_damage / (base_damage + attacker_defense)
        base_casualties = int(damage_ratio * defending_soldiers * 0.15)
        
        # Bonus if defender is warrior against cavalry
        if self.knight_class == KnightClass.WARRIOR and attacker.knight_class == KnightClass.CAVALRY:
            base_casualties = int(base_casualties * 1.2)  # Warriors with spears vs cavalry
        
        return min(base_casualties, attacker.soldiers)
    
    def take_casualties(self, casualties):
        """Apply casualties to the unit"""
        self.soldiers = max(0, self.soldiers - casualties)
        
        # Morale loss based on casualties
        casualty_percent = casualties / self.max_soldiers
        self.morale = max(0, self.morale - casualty_percent * 20)
        
        return self.soldiers <= 0  # Return True if unit is destroyed
    
    def consume_attack_ap(self):
        """Consume action points for attack without dealing damage"""
        if self.can_attack():
            # Different AP costs by unit type
            ap_cost = 3  # Default melee cost
            if self.knight_class == KnightClass.WARRIOR:
                ap_cost = 4
            elif self.knight_class == KnightClass.ARCHER:
                ap_cost = 2  # Ranged is faster
            elif self.knight_class == KnightClass.CAVALRY:
                ap_cost = 3
            elif self.knight_class == KnightClass.MAGE:
                ap_cost = 2
                
            self.action_points -= ap_cost
            self.has_acted = True
            return True
        return False
    
    def end_turn(self):
        self.action_points = self.max_action_points
        self.has_moved = False
        self.has_acted = False
        self.has_used_special = False
        # Regenerate some will each turn
        self.will = min(self.max_will, self.will + 20)
    
    def get_possible_moves(self, board_width, board_height, terrain_map=None, game_state=None):
        if terrain_map is None:
            # Fallback to simple range calculation using hex distance
            moves = []
            hex_grid = HexGrid()
            current_hex = hex_grid.offset_to_axial(self.x, self.y)
            hex_neighbors = current_hex.get_neighbors_within_range(self.movement_range)
            
            for hex_coord in hex_neighbors:
                new_x, new_y = hex_grid.axial_to_offset(hex_coord)
                if 0 <= new_x < board_width and 0 <= new_y < board_height:
                    moves.append((new_x, new_y))
            return moves
        
        # Use Dijkstra's algorithm for terrain-based movement
        visited = {}
        queue = deque([(self.x, self.y, 0, False)])  # x, y, movement_cost, broke_formation
        visited[(self.x, self.y)] = 0
        moves = []
        hex_grid = HexGrid()  # Create hex grid instance
        
        # Check if we start adjacent to friendly units
        start_adjacent_to_friendly = self._has_adjacent_friendly(self.x, self.y, game_state)
        
        # Special handling for units in ZOC
        if self.in_enemy_zoc and game_state and not self.can_disengage_from_zoc():
            # Can only move to attack the engaging enemy or stay put
            in_zoc, enemy = self.is_in_enemy_zoc(game_state)
            if in_zoc and enemy:
                # Can only move adjacent to the enemy that has us in ZOC
                return [(enemy.x, enemy.y)]  # Move to attack
            return []  # Cannot move
        
        # Routing units move differently
        if self.is_routing:
            # Routing units move away from enemies
            return self._get_routing_moves(board_width, board_height, terrain_map, game_state)
        
        while queue:
            x, y, cost, broke_formation = queue.popleft()
            
            # For hex grid, get neighbors using hex coordinates
            current_hex = hex_grid.offset_to_axial(x, y)
            neighbors = current_hex.get_neighbors()
            
            for neighbor_hex in neighbors:
                new_x, new_y = hex_grid.axial_to_offset(neighbor_hex)
                
                if 0 <= new_x < board_width and 0 <= new_y < board_height:
                    # Check if terrain is passable
                    if not terrain_map.is_passable(new_x, new_y, self.knight_class):
                        continue
                    
                    # Check if enemy unit blocks the path
                    if game_state and self._is_enemy_at(new_x, new_y, game_state):
                        continue  # Cannot move through enemies
                    
                    # Calculate movement cost
                    terrain_cost = terrain_map.get_movement_cost(new_x, new_y, self.knight_class)
                    
                    # Check if moving into enemy ZOC
                    will_enter_zoc = False
                    if game_state:
                        for enemy in game_state.knights:
                            if enemy.player_id != self.player_id and enemy.has_zone_of_control():
                                # Check hex distance for ZOC
                                enemy_hex = hex_grid.offset_to_axial(enemy.x, enemy.y)
                                new_hex = hex_grid.offset_to_axial(new_x, new_y)
                                if enemy_hex.distance_to(new_hex) == 1:
                                    will_enter_zoc = True
                                    break
                    
                    # If entering ZOC, this must be the last move
                    if will_enter_zoc and (x, y) != (self.x, self.y):
                        continue  # Can't move through ZOC
                    
                    # Check if we're breaking formation
                    if (x, y) == (self.x, self.y) and start_adjacent_to_friendly:
                        # First move away from friendly units costs all movement
                        if not self._has_adjacent_friendly(new_x, new_y, game_state):
                            new_cost = self.movement_range  # Use all movement points
                            broke_formation = True
                        else:
                            new_cost = cost + terrain_cost
                    else:
                        new_cost = cost + terrain_cost
                    
                    # If entering ZOC, this uses all remaining movement
                    if will_enter_zoc:
                        new_cost = self.movement_range
                    
                    # Check if we can reach this tile with our movement points
                    if new_cost <= self.movement_range:
                        # Check if we found a better path to this tile
                        if (new_x, new_y) not in visited or visited[(new_x, new_y)] > new_cost:
                            visited[(new_x, new_y)] = new_cost
                            if not will_enter_zoc:  # Don't continue pathfinding from ZOC
                                queue.append((new_x, new_y, new_cost, broke_formation))
                            if (new_x, new_y) != (self.x, self.y):
                                moves.append((new_x, new_y))
        
        return moves
    
    def _has_adjacent_friendly(self, x, y, game_state):
        """Check if position has adjacent friendly units"""
        if not game_state:
            return False
        
        hex_grid = HexGrid()
        pos_hex = hex_grid.offset_to_axial(x, y)
        neighbors = pos_hex.get_neighbors()
        
        for neighbor_hex in neighbors:
            check_x, check_y = hex_grid.axial_to_offset(neighbor_hex)
            for knight in game_state.knights:
                if (knight != self and knight.player_id == self.player_id and 
                    knight.x == check_x and knight.y == check_y and not knight.is_garrisoned):
                    return True
        return False
    
    def _is_enemy_at(self, x, y, game_state):
        """Check if enemy unit is at position"""
        if not game_state:
            return False
        
        for knight in game_state.knights:
            if (knight.player_id != self.player_id and 
                knight.x == x and knight.y == y and not knight.is_garrisoned):
                return True
        return False
    
    def has_zone_of_control(self):
        """Check if unit is strong enough to exert Zone of Control"""
        strength_percent = self.soldiers / self.max_soldiers
        return strength_percent >= 0.6 and not self.is_routing and not self.is_garrisoned
    
    def get_enemies_in_zoc(self, game_state):
        """Get enemy units in this unit's Zone of Control"""
        enemies = []
        if not self.has_zone_of_control():
            return enemies
        
        # ZOC extends to all adjacent hexes
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1)]:
            check_x, check_y = self.x + dx, self.y + dy
            for knight in game_state.knights:
                if (knight.player_id != self.player_id and 
                    knight.x == check_x and knight.y == check_y and 
                    not knight.is_garrisoned):
                    enemies.append(knight)
        return enemies
    
    def is_in_enemy_zoc(self, game_state):
        """Check if this unit is in enemy Zone of Control"""
        hex_grid = HexGrid()
        my_hex = hex_grid.offset_to_axial(self.x, self.y)
        
        for knight in game_state.knights:
            if knight.player_id != self.player_id and knight.has_zone_of_control():
                enemy_hex = hex_grid.offset_to_axial(knight.x, knight.y)
                if my_hex.distance_to(enemy_hex) == 1:  # Adjacent in hex grid
                    return True, knight
        return False, None
    
    def can_disengage_from_zoc(self):
        """Check if unit can break from Zone of Control"""
        # Only cavalry can disengage, and only if not routing
        return self.knight_class == KnightClass.CAVALRY and not self.is_routing
    
    def check_routing(self):
        """Check if unit should rout based on morale and casualties"""
        strength_percent = self.soldiers / self.max_soldiers
        
        # Rout if: very low morale OR heavy casualties with low morale
        if self.morale < 30 or (strength_percent < 0.4 and self.morale < 50):
            self.is_routing = True
            return True
        
        # Rally if routing but conditions improve
        if self.is_routing and self.morale > 60 and strength_percent > 0.5:
            self.is_routing = False
            
        return self.is_routing
    
    def take_casualties(self, casualties):
        """Apply casualties to the unit"""
        self.soldiers = max(0, self.soldiers - casualties)
        
        # Morale loss based on casualties
        casualty_percent = casualties / self.max_soldiers
        self.morale = max(0, self.morale - casualty_percent * 20)
        
        # Check for routing
        self.check_routing()
        
        return self.soldiers <= 0  # Return True if unit is destroyed
    
    def _get_routing_moves(self, board_width, board_height, terrain_map, game_state):
        """Get movement options for routing units (moving away from enemies)"""
        moves = []
        
        # Find the nearest enemy using hex distance
        hex_grid = HexGrid()
        my_hex = hex_grid.offset_to_axial(self.x, self.y)
        nearest_enemy = None
        min_distance = float('inf')
        
        for enemy in game_state.knights:
            if enemy.player_id != self.player_id and not enemy.is_garrisoned:
                enemy_hex = hex_grid.offset_to_axial(enemy.x, enemy.y)
                distance = my_hex.distance_to(enemy_hex)
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
        
        if not nearest_enemy:
            # No enemies, can move normally but with reduced range
            return self.get_possible_moves(board_width, board_height, terrain_map, None)
        
        # Move away from nearest enemy using hex neighbors
        current_hex = hex_grid.offset_to_axial(self.x, self.y)
        neighbors = current_hex.get_neighbors()
        
        for neighbor_hex in neighbors:
            new_x, new_y = hex_grid.axial_to_offset(neighbor_hex)
            
            if (0 <= new_x < board_width and 0 <= new_y < board_height and
                terrain_map and terrain_map.is_passable(new_x, new_y, self.knight_class)):
                
                # Check if this move increases distance from enemy
                enemy_hex = hex_grid.offset_to_axial(nearest_enemy.x, nearest_enemy.y)
                new_distance = neighbor_hex.distance_to(enemy_hex)
                if new_distance > min_distance and not self._is_enemy_at(new_x, new_y, game_state):
                    moves.append((new_x, new_y))
        
        return moves
    
    def can_charge(self, target, game_state):
        """Check if cavalry can charge the target"""
        if self.knight_class != KnightClass.CAVALRY:
            return False, "Only cavalry can charge"
        
        if self.will < 40:
            return False, "Not enough will (need 40)"
        
        if self.has_used_special:
            return False, "Already used special ability"
        
        if self.is_routing:
            return False, "Routing units cannot charge"
        
        # Must be adjacent (including diagonals)
        dx = abs(self.x - target.x)
        dy = abs(self.y - target.y)
        if not (dx <= 1 and dy <= 1 and (dx + dy > 0)):
            return False, "Must be adjacent to charge"
        
        # Charges are always possible against adjacent enemies
        # The outcome (damage/push) depends on what's behind the target
        return True, "Can charge"
    
    def execute_charge(self, target, game_state):
        """Execute cavalry charge against target"""
        can_charge, reason = self.can_charge(target, game_state)
        if not can_charge:
            return False, reason
        
        # Consume will
        self.will -= 40
        self.has_used_special = True
        
        # Calculate push direction
        push_dir_x = target.x - self.x
        push_dir_y = target.y - self.y
        push_x = target.x + push_dir_x
        push_y = target.y + push_dir_y
        
        # Check what's behind the target
        obstacle_type = None
        obstacle_unit = None
        can_push = True
        
        # Check map edge
        if not (0 <= push_x < game_state.board_width and 0 <= push_y < game_state.board_height):
            can_push = False
            obstacle_type = 'wall'
        # Check castles
        elif any(castle.contains_position(push_x, push_y) for castle in game_state.castles):
            can_push = False
            obstacle_type = 'wall'
        # Check terrain
        elif game_state.terrain_map and not game_state.terrain_map.is_passable(push_x, push_y, target.knight_class):
            can_push = False
            obstacle_type = 'terrain'
        else:
            # Check for units
            for knight in game_state.knights:
                if knight.x == push_x and knight.y == push_y and not knight.is_garrisoned:
                    obstacle_unit = knight
                    can_push = False
                    obstacle_type = 'unit'
                    break
        
        # Calculate base charge damage
        base_charge_damage = int(self.soldiers * 0.8)  # 80% of cavalry as base damage
        
        # Apply damage based on obstacle type
        if not can_push:
            if obstacle_type == 'wall':
                # Crushing charge against wall/castle
                charge_damage = int(base_charge_damage * 1.5)
                self_damage = int(self.soldiers * 0.1)
                target.take_casualties(charge_damage)
                target.morale = max(0, target.morale - 30)
                self.take_casualties(self_damage)
                message = f"Devastating charge! {target.name} crushed against the wall!"
                
            elif obstacle_type == 'terrain':
                # Trapped by terrain
                charge_damage = int(base_charge_damage * 1.3)
                self_damage = int(self.soldiers * 0.08)
                target.take_casualties(charge_damage)
                target.morale = max(0, target.morale - 25)
                self.take_casualties(self_damage)
                message = f"Crushing charge! {target.name} trapped by terrain!"
                
            elif obstacle_type == 'unit' and obstacle_unit:
                # Slammed into another unit
                charge_damage = int(base_charge_damage * 1.2)
                self_damage = int(self.soldiers * 0.07)
                collateral_damage = int(base_charge_damage * 0.3)
                
                # Apply damages
                target.take_casualties(charge_damage)
                target.morale = max(0, target.morale - 20)
                self.take_casualties(self_damage)
                
                # Collateral damage to the unit behind
                obstacle_unit.take_casualties(collateral_damage)
                obstacle_unit.morale = max(0, obstacle_unit.morale - 10)
                
                message = f"Charge! {target.name} slammed into {obstacle_unit.name}!"
            else:
                # Fallback case
                charge_damage = base_charge_damage
                self_damage = int(self.soldiers * 0.05)
                target.take_casualties(charge_damage)
                target.morale = max(0, target.morale - 20)
                self.take_casualties(self_damage)
                message = f"Charge! {target.name} has nowhere to retreat!"
        else:
            # Normal charge with push
            target.take_casualties(base_charge_damage)
            target.morale = max(0, target.morale - 20)
            self.take_casualties(int(self.soldiers * 0.05))
            
            # Push the target
            target.x = push_x
            target.y = push_y
            
            message = f"Charge! Pushed {target.name} back!"
            
        return True, message