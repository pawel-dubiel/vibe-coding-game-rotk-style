"""Enhanced terrain system with layers and realistic generation"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple
import random
import math


class TerrainType(Enum):
    """Base terrain types"""
    # Basic terrains (keeping compatibility)
    PLAINS = "Plains"
    FOREST = "Forest"
    HILLS = "Hills"
    WATER = "Water"
    BRIDGE = "Bridge"
    SWAMP = "Swamp"
    ROAD = "Road"
    
    # New terrain types
    LIGHT_FOREST = "Light Forest"
    DENSE_FOREST = "Dense Forest"
    HIGH_HILLS = "High Hills"
    MOUNTAINS = "Mountains"
    DEEP_WATER = "Deep Water"
    MARSH = "Marsh"
    DESERT = "Desert"
    SNOW = "Snow"
    

class TerrainFeature(Enum):
    """Terrain features that can overlay base terrain"""
    NONE = "None"
    STREAM = "Stream"
    RIVER = "River"
    ROAD = "Road"
    BRIDGE = "Bridge"
    RUINS = "Ruins"
    VILLAGE = "Village"
    FORTIFICATION = "Fortification"
    

@dataclass
class TerrainProperties:
    """Properties for each terrain type"""
    movement_cost: float
    defense_bonus: int
    passable: bool
    blocks_vision: bool
    elevation: int  # 0=sea level, positive=higher
    allows_features: List[TerrainFeature]


# Define terrain properties
TERRAIN_PROPERTIES = {
    TerrainType.PLAINS: TerrainProperties(1.0, 0, True, False, 1, 
        [TerrainFeature.STREAM, TerrainFeature.RIVER, TerrainFeature.ROAD, TerrainFeature.VILLAGE]),
    
    TerrainType.LIGHT_FOREST: TerrainProperties(1.5, 3, True, False, 1,
        [TerrainFeature.STREAM, TerrainFeature.ROAD, TerrainFeature.RUINS]),
    
    TerrainType.FOREST: TerrainProperties(2.0, 5, True, True, 1,
        [TerrainFeature.STREAM, TerrainFeature.ROAD, TerrainFeature.RUINS]),
    
    TerrainType.DENSE_FOREST: TerrainProperties(3.0, 8, True, True, 1,
        [TerrainFeature.STREAM, TerrainFeature.RUINS]),
    
    TerrainType.HILLS: TerrainProperties(2.0, 10, True, False, 2,
        [TerrainFeature.STREAM, TerrainFeature.ROAD, TerrainFeature.FORTIFICATION]),
    
    TerrainType.HIGH_HILLS: TerrainProperties(3.0, 15, True, True, 3,
        [TerrainFeature.STREAM, TerrainFeature.FORTIFICATION]),
    
    TerrainType.MOUNTAINS: TerrainProperties(float('inf'), 20, False, True, 4,
        [TerrainFeature.FORTIFICATION]),
    
    TerrainType.WATER: TerrainProperties(float('inf'), 0, False, False, 0,
        [TerrainFeature.BRIDGE]),
    
    TerrainType.DEEP_WATER: TerrainProperties(float('inf'), 0, False, False, -1,
        []),
    
    TerrainType.SWAMP: TerrainProperties(3.0, -3, True, False, 0,
        [TerrainFeature.ROAD]),
    
    TerrainType.MARSH: TerrainProperties(2.5, -2, True, False, 0,
        [TerrainFeature.STREAM, TerrainFeature.ROAD]),
    
    TerrainType.DESERT: TerrainProperties(1.5, -1, True, False, 1,
        [TerrainFeature.ROAD, TerrainFeature.RUINS]),
    
    TerrainType.SNOW: TerrainProperties(2.0, 0, True, False, 2,
        [TerrainFeature.ROAD]),
        
    # Legacy terrain types mapped to features
    TerrainType.BRIDGE: TerrainProperties(1.0, -5, True, False, 0,
        []),
    
    TerrainType.ROAD: TerrainProperties(0.5, -2, True, False, 0,
        [TerrainFeature.BRIDGE]),
}


class Terrain:
    """Represents a single terrain tile with base terrain and optional features"""
    
    def __init__(self, terrain_type: TerrainType, feature: TerrainFeature = TerrainFeature.NONE):
        # Handle legacy terrain types
        if terrain_type == TerrainType.BRIDGE:
            self.type = TerrainType.WATER
            self.feature = TerrainFeature.BRIDGE
        elif terrain_type == TerrainType.ROAD:
            self.type = TerrainType.PLAINS
            self.feature = TerrainFeature.ROAD
        else:
            self.type = terrain_type
            self.feature = feature
            
        self._properties = TERRAIN_PROPERTIES.get(self.type, TERRAIN_PROPERTIES[TerrainType.PLAINS])
        
    @property
    def movement_cost(self) -> float:
        """Get movement cost considering features"""
        base_cost = self._properties.movement_cost
        
        # Features can modify movement
        if self.feature == TerrainFeature.ROAD:
            return min(base_cost * 0.5, 0.5)  # Roads halve cost, minimum 0.5
        elif self.feature == TerrainFeature.BRIDGE:
            return 1.0  # Bridges normalize cost
        elif self.feature == TerrainFeature.STREAM:
            return base_cost + 0.5  # Streams add cost
        elif self.feature == TerrainFeature.RIVER:
            return float('inf')  # Rivers block unless bridged
            
        return base_cost
        
    def _get_movement_cost(self):
        """Legacy compatibility method"""
        return self.movement_cost
        
    @property
    def defense_bonus(self) -> int:
        """Get defense bonus considering features"""
        base_bonus = self._properties.defense_bonus
        
        # Features can add defense
        if self.feature == TerrainFeature.FORTIFICATION:
            return base_bonus + 10
        elif self.feature == TerrainFeature.VILLAGE:
            return base_bonus + 3
        elif self.feature == TerrainFeature.RUINS:
            return base_bonus + 5
        elif self.feature == TerrainFeature.BRIDGE:
            return max(base_bonus - 5, -5)  # Exposed on bridges
            
        return base_bonus
        
    def _get_defense_bonus(self):
        """Legacy compatibility method"""
        return self.defense_bonus
        
    @property
    def passable(self) -> bool:
        """Check if terrain is passable"""
        if self.feature == TerrainFeature.BRIDGE:
            return True  # Bridges make water passable
        if self.feature == TerrainFeature.RIVER and self.type != TerrainType.WATER:
            return False  # Rivers block unless bridged
        return self._properties.passable
        
    def _is_passable(self):
        """Legacy compatibility method"""
        return self.passable
        
    @property
    def blocks_vision(self) -> bool:
        """Check if terrain blocks line of sight"""
        return self._properties.blocks_vision
        
    @property
    def elevation(self) -> int:
        """Get terrain elevation"""
        return self._properties.elevation
        
    def can_support_feature(self, feature: TerrainFeature) -> bool:
        """Check if this terrain can support a given feature"""
        return feature in self._properties.allows_features
        
    def get_movement_cost_for_unit(self, unit) -> float:
        """Get movement cost for a specific unit using its terrain behavior"""
        base_cost = self.movement_cost
        
        # Check if unit has terrain movement behavior
        if hasattr(unit, 'get_behavior'):
            terrain_behavior = unit.get_behavior('TerrainMovementBehavior')
            if terrain_behavior:
                modifier = terrain_behavior.get_movement_cost_modifier(self.type)
                return base_cost * modifier
        
        return base_cost
        
    def get_combat_modifier_for_unit(self, unit) -> float:
        """Get combat modifier for a specific unit using its terrain behavior"""
        if hasattr(unit, 'get_behavior'):
            terrain_behavior = unit.get_behavior('TerrainMovementBehavior')
            if terrain_behavior:
                return terrain_behavior.get_combat_modifier(self.type)
        
        return 1.0


class TerrainGenerator:
    """Generates realistic terrain using various algorithms"""
    
    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 1000000)
        random.seed(self.seed)
        self._noise_cache = {}
        
    def _simple_noise(self, x: float, y: float, seed_offset: int = 0) -> float:
        """Simple pseudo-random noise function"""
        # Create a hash from coordinates
        hash_val = hash((int(x * 1000), int(y * 1000), self.seed + seed_offset))
        # Convert to float in range -1 to 1
        return (hash_val % 10000) / 5000.0 - 1.0
        
    @staticmethod
    def _interpolate(a: float, b: float, t: float) -> float:
        """Smooth interpolation between two values"""
        # Smoothstep interpolation
        t = t * t * (3 - 2 * t)
        return a + t * (b - a)
        
    def _perlin_noise(self, x: float, y: float, seed_offset: int = 0) -> float:
        """Simple Perlin-like noise implementation"""
        # Grid coordinates
        x0 = int(math.floor(x))
        y0 = int(math.floor(y))
        x1 = x0 + 1
        y1 = y0 + 1
        
        # Interpolation weights
        sx = x - x0
        sy = y - y0
        
        # Get noise values at grid corners
        n00 = self._simple_noise(x0, y0, seed_offset)
        n10 = self._simple_noise(x1, y0, seed_offset)
        n01 = self._simple_noise(x0, y1, seed_offset)
        n11 = self._simple_noise(x1, y1, seed_offset)
        
        # Interpolate
        nx0 = self._interpolate(n00, n10, sx)
        nx1 = self._interpolate(n01, n11, sx)
        
        return self._interpolate(nx0, nx1, sy)
        
    def generate_height_map(self, scale: float = 0.1, octaves: int = 4) -> List[List[float]]:
        """Generate height map using Perlin noise"""
        height_map = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Use multiple octaves for more realistic terrain
                value = 0
                amplitude = 1
                frequency = scale
                
                for octave in range(octaves):
                    value += self._perlin_noise(
                        x * frequency,
                        y * frequency,
                        octave * 1000
                    ) * amplitude
                    amplitude *= 0.5
                    frequency *= 2
                    
                # Normalize to 0-1 range
                row.append((value + 1) / 2)
            height_map.append(row)
            
        return height_map
        
    def generate_moisture_map(self, scale: float = 0.15) -> List[List[float]]:
        """Generate moisture map for vegetation distribution"""
        moisture_map = []
        offset = 10000  # Different offset for different noise
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                value = self._perlin_noise(
                    x * scale,
                    y * scale,
                    offset
                )
                row.append((value + 1) / 2)
            moisture_map.append(row)
            
        return moisture_map
        
    @staticmethod
    def classify_terrain(height: float, moisture: float) -> TerrainType:
        """Classify terrain for battle-appropriate maps (mostly grassland with natural features)"""
        # Water bodies - only for streams/rivers, very rare
        if height < 0.05:
            return TerrainType.WATER
            
        # Low elevation - mixed terrain with plains base (0.05 - 0.6)
        elif height < 0.6:
            if moisture < 0.15:
                return TerrainType.PLAINS
            elif moisture < 0.45:
                return TerrainType.PLAINS  # Still majority plains
            elif moisture < 0.65:
                return TerrainType.LIGHT_FOREST  # More light forest
            elif moisture < 0.8:
                return TerrainType.FOREST  # Regular forest areas
            else:
                return TerrainType.SWAMP  # Swamps in very wet areas
                
        # Medium elevation - mixed terrain (0.6 - 0.75)
        elif height < 0.75:
            if moisture < 0.25:
                return TerrainType.PLAINS
            elif moisture < 0.5:
                return TerrainType.HILLS
            elif moisture < 0.75:
                return TerrainType.LIGHT_FOREST
            else:
                return TerrainType.FOREST
                
        # Medium-high elevation - hills (0.75 - 0.9)
        elif height < 0.9:
            if moisture < 0.3:
                return TerrainType.HILLS
            elif moisture < 0.6:
                return TerrainType.HILLS
            else:
                return TerrainType.LIGHT_FOREST  # Forested hills
                
        # High elevation - rare high features (0.9+)
        else:
            if moisture < 0.5:
                return TerrainType.HIGH_HILLS
            else:
                return TerrainType.HILLS
            
    def generate_rivers(self, terrain_grid: List[List[Terrain]], 
                       height_map: List[List[float]]) -> None:
        """Generate rivers that flow from high to low elevation"""
        # Find potential stream sources (moderate elevation)
        sources = []
        for y in range(self.height):
            for x in range(self.width):
                # Look for moderate elevation areas for stream sources (less extreme than rivers)
                if 0.5 < height_map[y][x] < 0.8 and random.random() < 0.03:  # Increased chance for more streams
                    sources.append((x, y))
                    
        # Flow rivers downhill
        for source_x, source_y in sources:
            x, y = source_x, source_y
            river_tiles = set()
            
            while 0 <= x < self.width and 0 <= y < self.height:
                river_tiles.add((x, y))
                
                # Find lowest neighbor
                neighbors = [
                    (x-1, y), (x+1, y), (x, y-1), (x, y+1),
                    (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)
                ]
                
                valid_neighbors = [
                    (nx, ny) for nx, ny in neighbors
                    if 0 <= nx < self.width and 0 <= ny < self.height
                    and (nx, ny) not in river_tiles
                ]
                
                if not valid_neighbors:
                    break
                    
                # Flow to lowest neighbor
                lowest = min(valid_neighbors, key=lambda pos: height_map[pos[1]][pos[0]])
                
                # Stop if we hit water or go uphill
                if height_map[lowest[1]][lowest[0]] >= height_map[y][x]:
                    break
                if terrain_grid[lowest[1]][lowest[0]].type in [TerrainType.WATER, TerrainType.DEEP_WATER]:
                    break
                    
                x, y = lowest
                
                # Add stream feature for battle-appropriate water (avoid blocking rivers)
                if terrain_grid[y][x].can_support_feature(TerrainFeature.STREAM):
                    terrain_grid[y][x].feature = TerrainFeature.STREAM
                    
    def generate_roads(self, terrain_grid: List[List[Terrain]], 
                      important_points: List[Tuple[int, int]]) -> None:
        """Generate roads connecting important points (like castles)"""
        if len(important_points) < 2:
            return
            
        # Connect each point to the nearest other point
        for i, start in enumerate(important_points):
            # Find nearest unconnected point
            best_end = None
            best_distance = float('inf')
            
            for j, end in enumerate(important_points):
                if i != j:
                    dist = abs(end[0] - start[0]) + abs(end[1] - start[1])
                    if dist < best_distance:
                        best_distance = dist
                        best_end = end
                        
            if best_end:
                self._create_road(terrain_grid, start, best_end)
                
    def _create_road(self, terrain_grid: List[List[Terrain]], 
                    start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """Create a road between two points using A* pathfinding"""
        from heapq import heappush, heappop
        
        # Simple A* to find good path for road
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            _, current = heappop(open_set)
            
            if current == end:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                
                # Add road to tiles
                for x, y in path:
                    tile = terrain_grid[y][x]
                    if tile.can_support_feature(TerrainFeature.ROAD):
                        tile.feature = TerrainFeature.ROAD
                    elif tile.type == TerrainType.WATER and tile.can_support_feature(TerrainFeature.BRIDGE):
                        tile.feature = TerrainFeature.BRIDGE
                return
                
            # Check neighbors
            x, y = current
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbor = (nx, ny)
                    
                    # Cost based on terrain
                    terrain = terrain_grid[ny][nx]
                    if not terrain.passable and terrain.type != TerrainType.WATER:
                        continue
                        
                    move_cost = 1
                    if terrain.type in [TerrainType.FOREST, TerrainType.DENSE_FOREST]:
                        move_cost = 3  # Prefer to avoid forests
                    elif terrain.type == TerrainType.WATER:
                        move_cost = 5  # Expensive to bridge
                        
                    tentative_g = g_score[current] + move_cost
                    
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + abs(end[0] - nx) + abs(end[1] - ny)
                        heappush(open_set, (f_score, neighbor))
    
    def generate_forest_clusters(self, terrain_grid: List[List[Terrain]]) -> None:
        """Generate realistic forest clusters with light -> forest -> dense progression"""
        # Find existing light forest areas to expand into clusters
        light_forest_seeds = []
        for y in range(self.height):
            for x in range(self.width):
                if terrain_grid[y][x].type == TerrainType.LIGHT_FOREST:
                    light_forest_seeds.append((x, y))
        
        # Create forest clusters from each seed
        for seed_x, seed_y in light_forest_seeds:
            if random.random() < 0.6:  # More forests become clusters
                self._create_forest_cluster(terrain_grid, seed_x, seed_y)
        
        # Also create some additional forest clusters in plain areas
        num_extra_forests = random.randint(1, 3)
        for _ in range(num_extra_forests):
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            if terrain_grid[y][x].type == TerrainType.PLAINS:
                self._create_forest_cluster(terrain_grid, x, y)
    
    def _create_forest_cluster(self, terrain_grid: List[List[Terrain]], center_x: int, center_y: int) -> None:
        """Create a forest cluster with realistic progression from light to dense"""
        cluster_size = random.randint(2, 4)  # Smaller, more realistic clusters
        
        # Create concentric rings: light forest -> forest -> dense forest
        for radius in range(cluster_size + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    distance = abs(dx) + abs(dy)  # Manhattan distance
                    if distance <= radius:
                        x, y = center_x + dx, center_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            current_terrain = terrain_grid[y][x]
                            
                            # Only convert plains or existing light forest
                            if current_terrain.type in [TerrainType.PLAINS, TerrainType.LIGHT_FOREST]:
                                # Determine forest type based on distance from center
                                if distance == 0:
                                    # Center: dense forest
                                    terrain_grid[y][x] = Terrain(TerrainType.DENSE_FOREST)
                                elif distance <= 1:
                                    # Inner ring: regular forest
                                    terrain_grid[y][x] = Terrain(TerrainType.FOREST)
                                elif distance <= 2:
                                    # Outer ring: light forest
                                    terrain_grid[y][x] = Terrain(TerrainType.LIGHT_FOREST)
    
    def generate_streams(self, terrain_grid: List[List[Terrain]]) -> None:
        """Convert some water terrain to streams for more natural battlefield water features"""
        for y in range(self.height):
            for x in range(self.width):
                if terrain_grid[y][x].type == TerrainType.WATER:
                    # Convert isolated water tiles to streams (passable with movement penalty)
                    water_neighbors = 0
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if terrain_grid[ny][nx].type == TerrainType.WATER:
                                water_neighbors += 1
                    
                    # If water has 2 or fewer water neighbors, make it a stream
                    if water_neighbors <= 2:
                        terrain_grid[y][x] = Terrain(TerrainType.PLAINS, TerrainFeature.STREAM)
    
    def generate_hill_clusters(self, terrain_grid: List[List[Terrain]]) -> None:
        """Generate additional hill clusters for more varied terrain"""
        # Find existing hills to potentially expand
        hill_seeds = []
        for y in range(self.height):
            for x in range(self.width):
                if terrain_grid[y][x].type == TerrainType.HILLS:
                    hill_seeds.append((x, y))
        
        # Expand some existing hills
        for seed_x, seed_y in hill_seeds:
            if random.random() < 0.4:  # Expand some hills
                self._create_hill_cluster(terrain_grid, seed_x, seed_y)
        
        # Create new hill clusters in plains
        num_hill_clusters = random.randint(1, 2)
        for _ in range(num_hill_clusters):
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            if terrain_grid[y][x].type == TerrainType.PLAINS:
                self._create_hill_cluster(terrain_grid, x, y)
    
    def _create_hill_cluster(self, terrain_grid: List[List[Terrain]], center_x: int, center_y: int) -> None:
        """Create a hill cluster"""
        cluster_size = random.randint(1, 3)  # Smaller hill clusters
        
        for dy in range(-cluster_size, cluster_size + 1):
            for dx in range(-cluster_size, cluster_size + 1):
                distance = abs(dx) + abs(dy)
                if distance <= cluster_size:
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        current_terrain = terrain_grid[y][x]
                        
                        # Only convert plains
                        if current_terrain.type == TerrainType.PLAINS:
                            if distance == 0 and random.random() < 0.3:
                                # Chance for high hills at center
                                terrain_grid[y][x] = Terrain(TerrainType.HIGH_HILLS)
                            else:
                                terrain_grid[y][x] = Terrain(TerrainType.HILLS)
    
    def generate_controlled_features(self, terrain_grid: List[List[Terrain]]) -> None:
        """Generate terrain features in controlled amounts starting from plains base"""
        # 1. Add 1-2 hill clusters (strategic high ground)
        self._add_controlled_hills(terrain_grid)
        
        # 2. Add 2-4 forest clusters (cover and tactical positions)
        self._add_controlled_forests(terrain_grid)
        
        # 3. Add 1-2 streams (water features for tactical complexity)
        self._add_controlled_streams(terrain_grid)
        
        # 4. Add 0-1 swamp areas (difficult terrain, rare)
        self._add_controlled_swamps(terrain_grid)
    
    def _add_controlled_hills(self, terrain_grid: List[List[Terrain]]) -> None:
        """Add 1-2 hill clusters in strategic locations"""
        num_hill_clusters = random.randint(1, 2)
        
        for _ in range(num_hill_clusters):
            # Find a good location away from edges and other hills
            attempts = 0
            while attempts < 20:  # Prevent infinite loop
                x = random.randint(3, self.width - 4)
                y = random.randint(3, self.height - 4)
                
                # Check if area is mostly plains
                if self._is_area_clear(terrain_grid, x, y, 2, TerrainType.PLAINS):
                    self._create_strategic_hill_cluster(terrain_grid, x, y)
                    break
                attempts += 1
    
    def _add_controlled_forests(self, terrain_grid: List[List[Terrain]]) -> None:
        """Add 2-4 forest clusters with realistic progression"""
        num_forest_clusters = random.randint(2, 4)
        
        for _ in range(num_forest_clusters):
            attempts = 0
            while attempts < 20:
                x = random.randint(2, self.width - 3)
                y = random.randint(2, self.height - 3)
                
                # Check if area is mostly plains
                if self._is_area_clear(terrain_grid, x, y, 2, TerrainType.PLAINS):
                    self._create_strategic_forest_cluster(terrain_grid, x, y)
                    break
                attempts += 1
    
    def _add_controlled_streams(self, terrain_grid: List[List[Terrain]]) -> None:
        """Add 1-2 streams across the battlefield"""
        num_streams = random.randint(1, 2)
        
        for _ in range(num_streams):
            if random.random() < 0.5:
                # Horizontal stream
                y = random.randint(2, self.height - 3)
                start_x = random.randint(0, 2)
                end_x = random.randint(self.width - 3, self.width - 1)
                self._create_stream_line(terrain_grid, start_x, y, end_x, y)
            else:
                # Vertical stream
                x = random.randint(2, self.width - 3)
                start_y = random.randint(0, 2)
                end_y = random.randint(self.height - 3, self.height - 1)
                self._create_stream_line(terrain_grid, x, start_y, x, end_y)
    
    def _add_controlled_swamps(self, terrain_grid: List[List[Terrain]]) -> None:
        """Add 0-1 small swamp areas near streams"""
        if random.random() < 0.4:  # 40% chance for swamp
            # Find stream locations
            stream_locations = []
            for y in range(self.height):
                for x in range(self.width):
                    if terrain_grid[y][x].feature == TerrainFeature.STREAM:
                        stream_locations.append((x, y))
            
            if stream_locations:
                # Pick a random stream location
                stream_x, stream_y = random.choice(stream_locations)
                # Create small swamp area nearby
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = stream_x + dx, stream_y + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height and
                            terrain_grid[ny][nx].type == TerrainType.PLAINS and
                            random.random() < 0.6):  # 60% chance per adjacent tile
                            terrain_grid[ny][nx] = Terrain(TerrainType.SWAMP)
    
    def _is_area_clear(self, terrain_grid: List[List[Terrain]], center_x: int, center_y: int, 
                      radius: int, required_type: TerrainType) -> bool:
        """Check if an area is mostly the required terrain type"""
        total_tiles = 0
        matching_tiles = 0
        
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    total_tiles += 1
                    if terrain_grid[y][x].type == required_type:
                        matching_tiles += 1
        
        return matching_tiles / total_tiles >= 0.8  # 80% must be the required type
    
    def _create_strategic_hill_cluster(self, terrain_grid: List[List[Terrain]], center_x: int, center_y: int) -> None:
        """Create a hill cluster with strategic placement"""
        cluster_size = random.randint(2, 3)  # Medium-sized clusters
        
        for dy in range(-cluster_size, cluster_size + 1):
            for dx in range(-cluster_size, cluster_size + 1):
                distance = abs(dx) + abs(dy)
                if distance <= cluster_size:
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if terrain_grid[y][x].type == TerrainType.PLAINS:
                            if distance == 0 and random.random() < 0.4:
                                # Higher chance for high hills at center
                                terrain_grid[y][x] = Terrain(TerrainType.HIGH_HILLS)
                            elif distance <= 1:
                                terrain_grid[y][x] = Terrain(TerrainType.HILLS)
                            elif distance <= 2 and random.random() < 0.7:
                                terrain_grid[y][x] = Terrain(TerrainType.HILLS)
    
    def _create_strategic_forest_cluster(self, terrain_grid: List[List[Terrain]], center_x: int, center_y: int) -> None:
        """Create a forest cluster with natural progression"""
        cluster_size = random.randint(2, 4)  # Varied forest sizes
        
        for dy in range(-cluster_size, cluster_size + 1):
            for dx in range(-cluster_size, cluster_size + 1):
                distance = abs(dx) + abs(dy)
                if distance <= cluster_size:
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if terrain_grid[y][x].type == TerrainType.PLAINS:
                            if distance == 0:
                                # Center: dense forest
                                terrain_grid[y][x] = Terrain(TerrainType.DENSE_FOREST)
                            elif distance <= 1:
                                # Inner ring: regular forest
                                terrain_grid[y][x] = Terrain(TerrainType.FOREST)
                            elif distance <= 2:
                                # Outer ring: light forest
                                terrain_grid[y][x] = Terrain(TerrainType.LIGHT_FOREST)
                            elif distance <= cluster_size and random.random() < 0.5:
                                # Sparse outer edge
                                terrain_grid[y][x] = Terrain(TerrainType.LIGHT_FOREST)
    
    def _create_stream_line(self, terrain_grid: List[List[Terrain]], start_x: int, start_y: int, 
                           end_x: int, end_y: int) -> None:
        """Create a stream line between two points"""
        # Simple line drawing algorithm
        dx = abs(end_x - start_x)
        dy = abs(end_y - start_y)
        sx = 1 if start_x < end_x else -1
        sy = 1 if start_y < end_y else -1
        err = dx - dy
        
        x, y = start_x, start_y
        
        while True:
            # Add stream with some randomness
            if 0 <= x < self.width and 0 <= y < self.height:
                if terrain_grid[y][x].type == TerrainType.PLAINS:
                    terrain_grid[y][x] = Terrain(TerrainType.PLAINS, TerrainFeature.STREAM)
                
                # Occasionally add adjacent stream tiles for wider streams
                if random.random() < 0.3:
                    for dx_adj, dy_adj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        adj_x, adj_y = x + dx_adj, y + dy_adj
                        if (0 <= adj_x < self.width and 0 <= adj_y < self.height and
                            terrain_grid[adj_y][adj_x].type == TerrainType.PLAINS and
                            random.random() < 0.5):
                            terrain_grid[adj_y][adj_x] = Terrain(TerrainType.PLAINS, TerrainFeature.STREAM)
            
            if x == end_x and y == end_y:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
                        

class TerrainMap:
    """Enhanced terrain map with layered terrain system"""
    
    def __init__(self, width: int, height: int, seed: Optional[int] = None, 
                 use_legacy_generation: bool = False):
        self.width = width
        self.height = height
        self.terrain_grid: List[List[Terrain]] = []
        
        if use_legacy_generation:
            self._generate_legacy_terrain()
        else:
            self._generate_terrain(seed)
        
    def _generate_terrain(self, seed: Optional[int] = None):
        """Generate realistic battle terrain starting with plains base"""
        generator = TerrainGenerator(self.width, self.height, seed)
        
        # Start with all plains for consistent battle terrain
        self.terrain_grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(Terrain(TerrainType.PLAINS))
            self.terrain_grid.append(row)
        
        # Generate strategic terrain features in controlled amounts
        generator.generate_controlled_features(self.terrain_grid)
        
        # Add roads connecting castle positions (if standard size)
        if self.width >= 20 and self.height >= 20:
            castle_positions = [
                (2, 2),
                (self.width - 3, self.height - 3),
                (2, self.height - 3),
                (self.width - 3, 2)
            ]
            # Only use positions that are in bounds
            valid_positions = [
                pos for pos in castle_positions
                if pos[0] < self.width and pos[1] < self.height
            ]
            generator.generate_roads(self.terrain_grid, valid_positions[:2])
            
    def _generate_legacy_terrain(self):
        """Legacy terrain generation for compatibility"""
        # Initialize with plains
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(Terrain(TerrainType.PLAINS))
            self.terrain_grid.append(row)
        
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
        """Legacy river generation"""
        river_x = self.width // 2
        bridge_positions = [3, 6, 9]
        
        for y in range(self.height):
            x = river_x
            if y % 3 == 0:
                x += random.choice([-1, 0, 1])
                x = max(river_x - 1, min(river_x + 1, x))
            
            if 0 <= x < self.width:
                if y in bridge_positions:
                    self.terrain_grid[y][x] = Terrain(TerrainType.WATER, TerrainFeature.BRIDGE)
                else:
                    self.terrain_grid[y][x] = Terrain(TerrainType.WATER)
                    
    def _add_terrain_patches(self, terrain_type, num_patches, min_size, max_size):
        """Legacy terrain patch generation"""
        for _ in range(num_patches):
            center_x = random.randint(1, self.width - 2)
            center_y = random.randint(1, self.height - 2)
            size = random.randint(min_size, max_size)
            
            for dy in range(-size, size + 1):
                for dx in range(-size, size + 1):
                    if abs(dx) + abs(dy) <= size:
                        x, y = center_x + dx, center_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            if self.terrain_grid[y][x].type not in [TerrainType.WATER, TerrainType.BRIDGE]:
                                self.terrain_grid[y][x] = Terrain(terrain_type)
                                
    def _add_swamps(self):
        """Legacy swamp generation"""
        for y in range(self.height):
            for x in range(self.width):
                if self.terrain_grid[y][x].type == TerrainType.WATER:
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.terrain_grid[ny][nx].type == TerrainType.PLAINS:
                                if random.random() < 0.3:
                                    self.terrain_grid[ny][nx] = Terrain(TerrainType.SWAMP)
                                    
    def _add_roads(self):
        """Legacy road generation"""
        road_y_positions = [6]
        for y in road_y_positions:
            for x in range(self.width):
                if self.terrain_grid[y][x].type == TerrainType.PLAINS:
                    self.terrain_grid[y][x].feature = TerrainFeature.ROAD
                elif self.terrain_grid[y][x].type == TerrainType.WATER:
                    self.terrain_grid[y][x].feature = TerrainFeature.BRIDGE
            
    def get_terrain(self, x: int, y: int) -> Optional[Terrain]:
        """Get terrain at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.terrain_grid[y][x]
        return None
        
    def set_terrain(self, x: int, y: int, terrain_type: TerrainType, 
                   feature: TerrainFeature = TerrainFeature.NONE):
        """Set terrain at specific location"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.terrain_grid[y][x] = Terrain(terrain_type, feature)
            
    def is_passable(self, x: int, y: int, unit=None) -> bool:
        """Check if position is passable"""
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return False
        return terrain.passable
        
    def get_movement_cost(self, x: int, y: int, unit) -> float:
        """Get movement cost for unit at position"""
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return float('inf')
        return terrain.get_movement_cost_for_unit(unit)
        
    def get_elevation(self, x: int, y: int) -> int:
        """Get elevation at position"""
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return 0
        return terrain.elevation
        
    def has_feature(self, x: int, y: int, feature: TerrainFeature) -> bool:
        """Check if position has specific feature"""
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return False
        return terrain.feature == feature