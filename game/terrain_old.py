from enum import Enum
import random

class TerrainType(Enum):
    PLAINS = "Plains"
    FOREST = "Forest"
    HILLS = "Hills"
    WATER = "Water"
    BRIDGE = "Bridge"
    SWAMP = "Swamp"
    ROAD = "Road"

class Terrain:
    def __init__(self, terrain_type):
        self.type = terrain_type
        self.movement_cost = self._get_movement_cost()
        self.defense_bonus = self._get_defense_bonus()
        self.passable = self._is_passable()
        
    def _get_movement_cost(self):
        costs = {
            TerrainType.PLAINS: 1,
            TerrainType.FOREST: 2,
            TerrainType.HILLS: 2,
            TerrainType.WATER: float('inf'),  # Impassable
            TerrainType.BRIDGE: 1,
            TerrainType.SWAMP: 3,
            TerrainType.ROAD: 0.5  # Faster movement
        }
        return costs.get(self.type, 1)
    
    def _get_defense_bonus(self):
        bonuses = {
            TerrainType.PLAINS: 0,
            TerrainType.FOREST: 5,
            TerrainType.HILLS: 10,
            TerrainType.WATER: 0,
            TerrainType.BRIDGE: -5,  # Exposed position
            TerrainType.SWAMP: -3,
            TerrainType.ROAD: -2
        }
        return bonuses.get(self.type, 0)
    
    def _is_passable(self):
        return self.type != TerrainType.WATER
    
    def get_movement_cost_for_unit(self, unit):
        """Get movement cost for a unit using its terrain behavior"""
        base_cost = self.movement_cost
        
        # Check if unit has terrain movement behavior
        if hasattr(unit, 'get_behavior'):
            terrain_behavior = unit.get_behavior('TerrainMovementBehavior')
            if terrain_behavior:
                modifier = terrain_behavior.get_movement_cost_modifier(self.type)
                return base_cost * modifier
        
        # Fallback for units without the behavior or legacy code
        return base_cost
    
    def get_combat_modifier_for_unit(self, unit):
        """Get combat modifier for a unit using its terrain behavior"""
        # Check if unit has terrain movement behavior
        if hasattr(unit, 'get_behavior'):
            terrain_behavior = unit.get_behavior('TerrainMovementBehavior')
            if terrain_behavior:
                return terrain_behavior.get_combat_modifier(self.type)
        
        # Fallback
        return 1.0

class TerrainMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.terrain_grid = [[None for _ in range(width)] for _ in range(height)]
        self._generate_terrain()
    
    def _generate_terrain(self):
        # Initialize with plains
        for y in range(self.height):
            for x in range(self.width):
                self.terrain_grid[y][x] = Terrain(TerrainType.PLAINS)
        
        # Add a river with bridges
        self._add_river()
        
        # Add forests
        self._add_terrain_patches(TerrainType.FOREST, 3, 2, 3)
        
        # Add hills
        self._add_terrain_patches(TerrainType.HILLS, 2, 2, 2)
        
        # Add swamps near water
        self._add_swamps()
        
        # Add roads connecting castles
        self._add_roads()
    
    def _add_river(self):
        # Create a river flowing vertically through the middle
        river_x = self.width // 2
        bridge_positions = [3, 6, 9]  # Y positions for bridges
        
        for y in range(self.height):
            x = river_x
            # Add some meandering
            if y % 3 == 0:
                x += random.choice([-1, 0, 1])
                x = max(river_x - 1, min(river_x + 1, x))
            
            if 0 <= x < self.width:
                if y in bridge_positions:
                    self.terrain_grid[y][x] = Terrain(TerrainType.BRIDGE)
                else:
                    self.terrain_grid[y][x] = Terrain(TerrainType.WATER)
    
    def _add_terrain_patches(self, terrain_type, num_patches, min_size, max_size):
        for _ in range(num_patches):
            center_x = random.randint(1, self.width - 2)
            center_y = random.randint(1, self.height - 2)
            size = random.randint(min_size, max_size)
            
            for dy in range(-size, size + 1):
                for dx in range(-size, size + 1):
                    if abs(dx) + abs(dy) <= size:
                        x, y = center_x + dx, center_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            # Don't overwrite water or bridges
                            if self.terrain_grid[y][x].type not in [TerrainType.WATER, TerrainType.BRIDGE]:
                                self.terrain_grid[y][x] = Terrain(terrain_type)
    
    def _add_swamps(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.terrain_grid[y][x].type == TerrainType.WATER:
                    # Add swamps adjacent to water
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.terrain_grid[ny][nx].type == TerrainType.PLAINS:
                                if random.random() < 0.3:  # 30% chance
                                    self.terrain_grid[ny][nx] = Terrain(TerrainType.SWAMP)
    
    def _add_roads(self):
        # Add horizontal roads at castle heights
        road_y_positions = [6]  # Where castles are
        for y in road_y_positions:
            for x in range(self.width):
                if self.terrain_grid[y][x].type in [TerrainType.PLAINS, TerrainType.BRIDGE]:
                    self.terrain_grid[y][x] = Terrain(TerrainType.ROAD)
    
    def get_terrain(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.terrain_grid[y][x]
        return None
    
    def set_terrain(self, x, y, terrain_type):
        """Set terrain at specific location (for testing)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.terrain_grid[y][x] = Terrain(terrain_type)
    
    def is_passable(self, x, y, unit=None):
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return False
        return terrain.passable
    
    def get_movement_cost(self, x, y, unit):
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return float('inf')
        return terrain.get_movement_cost_for_unit(unit)