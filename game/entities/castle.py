import pygame

class Castle:
    def __init__(self, center_x, center_y, player_id):
        self.center_x = center_x
        self.center_y = center_y
        self.player_id = player_id
        self.health = 1000
        self.max_health = 1000
        self.defense = 30
        
        # Castle occupies multiple hexes (3x3)
        self.occupied_tiles = self._get_occupied_tiles()
        
        # Garrison
        self.garrison_slots = 3
        self.garrisoned_units = []
        
        # Castle defenses
        self.arrow_damage_per_archer = 2  # Per archer soldier
        self.arrow_range = 3
        self.has_shot = False
        
    def _get_occupied_tiles(self):
        """Get all tiles occupied by the castle"""
        tiles = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if abs(dx) + abs(dy) <= 1:  # Diamond shape
                    tiles.append((self.center_x + dx, self.center_y + dy))
        return tiles
    
    def contains_position(self, x, y):
        """Check if a position is part of the castle"""
        return (x, y) in self.occupied_tiles
        
    def add_unit_to_garrison(self, unit):
        if len(self.garrisoned_units) < self.garrison_slots and unit.player_id == self.player_id:
            self.garrisoned_units.append(unit)
            unit.is_garrisoned = True
            unit.garrison_location = self
            # Move unit to castle center
            unit.x = self.center_x
            unit.y = self.center_y
            return True
        return False
    
    def remove_unit_from_garrison(self, unit):
        if unit in self.garrisoned_units:
            self.garrisoned_units.remove(unit)
            unit.is_garrisoned = False
            unit.garrison_location = None
            return True
        return False
    
    def get_total_archer_soldiers(self):
        """Get total archer soldiers in garrison for arrow attacks"""
        total = 0
        from game.entities.knight import KnightClass
        for unit in self.garrisoned_units:
            if unit.knight_class == KnightClass.ARCHER:
                total += unit.soldiers
        return total
    
    def take_damage(self, damage):
        actual_damage = max(0, damage - self.defense)
        self.health -= actual_damage
        return actual_damage
    
    def is_destroyed(self):
        return self.health <= 0
    
    def get_enemies_in_range(self, knights):
        enemies = []
        for knight in knights:
            if knight.player_id != self.player_id and not knight.is_garrisoned:
                # Check distance from any castle tile
                min_distance = float('inf')
                for tile_x, tile_y in self.occupied_tiles:
                    distance = abs(knight.x - tile_x) + abs(knight.y - tile_y)
                    min_distance = min(min_distance, distance)
                if min_distance <= self.arrow_range:
                    enemies.append(knight)
        return enemies
    
    def shoot_arrows(self, enemies):
        if not enemies or self.has_shot:
            return []
        
        # Calculate total arrow damage based on garrisoned archers
        total_archers = self.get_total_archer_soldiers()
        if total_archers == 0:
            return []  # No archers to shoot
        
        # Each archer can target enemies
        total_damage = total_archers * self.arrow_damage_per_archer
        damage_per_enemy = total_damage // len(enemies)
        remaining_damage = total_damage % len(enemies)
        
        damages = []
        for i, enemy in enumerate(enemies):
            damage = damage_per_enemy
            if i < remaining_damage:
                damage += 1
            # Convert to casualties
            casualties = min(damage // 10, enemy.soldiers)  # Roughly 10 damage = 1 casualty
            damages.append((enemy, casualties))
        
        self.has_shot = True
        return damages
    
    def end_turn(self):
        self.has_shot = False