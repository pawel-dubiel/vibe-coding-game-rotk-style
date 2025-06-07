#!/usr/bin/env python3
"""
Tile-based Terrain Generator for Large Regions

This approach downloads map tiles and analyzes their colors to classify terrain.
Much more reliable than Overpass API for large areas.

Usage: python tile_terrain_generator.py --bounds west,south,east,north --hex-size-km 30
"""

import json
import os
import sys
import math
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import urllib.request
import urllib.parse
from PIL import Image
import io

# Import campaign terrain types
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from game.campaign.campaign_state import CampaignTerrainType

@dataclass
class GeographicBounds:
    """Geographic boundaries for the map"""
    west_lon: float
    east_lon: float
    south_lat: float
    north_lat: float

class MapTileFetcher:
    """Fetches map tiles from OpenStreetMap tile servers"""
    
    def __init__(self):
        # Use multiple tile servers for reliability
        self.tile_servers = [
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png", 
            "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
        ]
        self.current_server = 0
        self.request_delay = 0.1  # Be respectful to tile servers
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile numbers"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y

    def deg2num_float(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[float, float]:
        """Convert lat/lon to fractional tile coordinates"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = (lon_deg + 180.0) / 360.0 * n
        y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
        return x, y
    
    def num2deg(self, x: int, y: int, zoom: int) -> Tuple[float, float]:
        """Convert tile numbers to lat/lon"""
        n = 2.0 ** zoom
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg
    
    def fetch_tile(self, x: int, y: int, zoom: int) -> Optional[Image.Image]:
        """Fetch a single map tile"""
        for attempt in range(len(self.tile_servers)):
            server_url = self.tile_servers[(self.current_server + attempt) % len(self.tile_servers)]
            url = server_url.format(z=zoom, x=x, y=y)
            
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Medieval Campaign Map Generator/1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    image_data = response.read()
                    return Image.open(io.BytesIO(image_data))
                    
            except Exception as e:
                print(f"   ⚠️  Tile server {attempt+1} failed: {e}")
                continue
        
        return None
    
    def fetch_area_tiles(self, bounds: GeographicBounds, zoom: int = 8) -> Optional[Image.Image]:
        """Fetch and stitch together tiles for the given area"""
        print(f"🗺️  Fetching map tiles at zoom level {zoom}...")
        
        # Calculate tile bounds
        min_x, max_y = self.deg2num(bounds.south_lat, bounds.west_lon, zoom)
        max_x, min_y = self.deg2num(bounds.north_lat, bounds.east_lon, zoom)
        
        tiles_x = max_x - min_x + 1
        tiles_y = max_y - min_y + 1
        total_tiles = tiles_x * tiles_y
        
        print(f"📊 Need {tiles_x}×{tiles_y} = {total_tiles} tiles")
        
        if total_tiles > 100:
            print(f"⚠️  Warning: {total_tiles} tiles is a lot. Consider using lower zoom or smaller area.")
        
        # Create combined image
        tile_size = 256  # Standard tile size
        combined_width = tiles_x * tile_size
        combined_height = tiles_y * tile_size
        combined_image = Image.new('RGB', (combined_width, combined_height))
        
        successful_tiles = 0
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                tile_image = self.fetch_tile(x, y, zoom)
                
                if tile_image:
                    # Calculate position in combined image
                    pos_x = (x - min_x) * tile_size
                    pos_y = (y - min_y) * tile_size
                    combined_image.paste(tile_image, (pos_x, pos_y))
                    successful_tiles += 1
                else:
                    print(f"   ❌ Failed to fetch tile {x},{y}")
                
                # Be respectful to servers
                time.sleep(self.request_delay)
                
                if (successful_tiles + 1) % 10 == 0:
                    print(f"   📈 Progress: {successful_tiles}/{total_tiles} tiles")
        
        print(f"✅ Successfully fetched {successful_tiles}/{total_tiles} tiles")
        
        if successful_tiles < total_tiles * 0.8:
            print("⚠️  Less than 80% of tiles fetched - map may have gaps")
            return None
        
        return combined_image

class TileTerrainClassifier:
    """Classifies terrain from map tile images using color analysis"""
    
    def __init__(self):
        # Define color ranges for different terrain types based on OSM rendering
        self.terrain_colors = {
            CampaignTerrainType.WATER: [
                (170, 211, 223),  # Light blue water
                (181, 208, 208),  # Grayish water
                (153, 204, 255),  # Bright blue water
                (100, 150, 255),  # Deep blue water
            ],
            CampaignTerrainType.FOREST: [
                (173, 209, 158),  # Light green forest
                (157, 202, 138),  # Forest green
                (130, 180, 120),  # Dark forest
                (100, 150, 100),  # Dense forest
            ],
            CampaignTerrainType.MOUNTAINS: [
                (221, 220, 204),  # Mountain brown
                (200, 190, 180),  # Rock color
                (180, 170, 160),  # Dark mountain
                (160, 150, 140),  # Steep terrain
            ],
            CampaignTerrainType.DESERT: [
                (238, 220, 180),  # Sand color
                (220, 200, 160),  # Desert brown
                (240, 230, 200),  # Light sand
                (210, 190, 150),  # Dark sand
            ],
            CampaignTerrainType.SNOW: [
                (255, 255, 255),  # Pure white
                (245, 245, 255),  # Snow white
                (240, 248, 255),  # Ice blue
                (230, 240, 250),  # Glacier
            ]
            # PLAINS and HILLS default to everything else
        }
    
    def color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two colors"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))
    
    def classify_pixel(self, r: int, g: int, b: int) -> CampaignTerrainType:
        """Classify a pixel color into terrain type"""
        pixel_color = (r, g, b)
        
        # Check against known terrain colors
        for terrain_type, color_list in self.terrain_colors.items():
            for terrain_color in color_list:
                if self.color_distance(pixel_color, terrain_color) < 30:
                    return terrain_type
        
        # Determine terrain based on color characteristics
        brightness = (r + g + b) / 3
        
        # Water: Blue dominant
        if b > r + 20 and b > g + 10:
            return CampaignTerrainType.WATER
        
        # Forest: Green dominant and not too bright
        if g > r + 10 and g > b + 10 and brightness < 180:
            return CampaignTerrainType.FOREST
        
        # Mountains: Brown-ish colors
        if r > g and g > b and brightness < 160:
            return CampaignTerrainType.MOUNTAINS
        
        # Desert: Yellow-ish bright colors
        if r > g and g > b and brightness > 180:
            return CampaignTerrainType.DESERT
        
        # Snow: Very bright white
        if brightness > 240 and abs(r-g) < 10 and abs(g-b) < 10:
            return CampaignTerrainType.SNOW
        
        # Hills: Medium brightness, balanced colors
        if 120 < brightness < 180:
            return CampaignTerrainType.HILLS
        
        # Default: Plains
        return CampaignTerrainType.PLAINS

def load_medieval_cities(cities_file_path: str) -> List[Dict]:
    """Load medieval cities from JSON file"""
    try:
        with open(cities_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('cities', [])
    except FileNotFoundError:
        print(f"⚠️  Cities file not found: {cities_file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️  Error parsing cities file: {e}")
        return []

def filter_cities_in_bounds(cities: List[Dict], bounds: GeographicBounds) -> List[Dict]:
    """Filter cities that fall within the map boundaries"""
    filtered_cities = []
    for city in cities:
        lat = city.get('latitude')
        lon = city.get('longitude')
        
        if (lat is not None and lon is not None and
            bounds.south_lat <= lat <= bounds.north_lat and
            bounds.west_lon <= lon <= bounds.east_lon):
            filtered_cities.append(city)
    
    return filtered_cities

def convert_cities_to_hex_coordinates(cities: List[Dict], bounds: GeographicBounds, 
                                    hex_grid_width: int, hex_grid_height: int, 
                                    zoom: int, terrain_map: Dict = None, 
                                    map_image: Image.Image = None, 
                                    classifier: TileTerrainClassifier = None) -> Tuple[Dict, int, int]:
    """Convert city coordinates to hex grid using Web Mercator projection and format for game"""
    game_cities = {}
    
    def advanced_coordinate_mapping(lat: float, lon: float) -> Tuple[int, int]:
        """Advanced coordinate mapping that matches the tile system exactly"""
        # Use the same deg2num function as the tile fetcher to ensure consistency
        fetcher = MapTileFetcher()

        # Convert city lat/lon to tile coordinates at the same zoom level
        city_tile_x, city_tile_y = fetcher.deg2num_float(lat, lon, zoom)
        
        # Get map bounds in tile coordinates. Use integer tile numbers here
        # because the tile image fetched by ``fetch_area_tiles`` is aligned to
        # full tile boundaries.  Using the same integer bounds ensures that
        # city positions line up perfectly with the generated terrain map.
        # IMPORTANT: In tile coordinates, Y increases from north to south!
        # So north latitude gives us the MIN tile Y, south latitude gives us MAX tile Y
        west_x, south_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
        east_x, north_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
        
        # Correct the min/max for the inverted Y axis
        min_tile_x = west_x
        max_tile_x = east_x
        min_tile_y = north_y  # North is MIN Y in tile coords
        max_tile_y = south_y  # South is MAX Y in tile coords
        
        # Ensure we handle the tile coordinate space correctly
        # Note: tile Y increases from north to south
        tile_x_normalized = (city_tile_x - min_tile_x) / (max_tile_x - min_tile_x) if max_tile_x != min_tile_x else 0
        tile_y_normalized = (city_tile_y - min_tile_y) / (max_tile_y - min_tile_y) if max_tile_y != min_tile_y else 0
        
        # Convert to hex grid coordinates with proper rounding
        # Use round() instead of int() for better distribution
        hex_x = round(tile_x_normalized * (hex_grid_width - 1))
        hex_y = round(tile_y_normalized * (hex_grid_height - 1))
        
        # Clamp to grid bounds
        hex_x = max(0, min(hex_x, hex_grid_width - 1))
        hex_y = max(0, min(hex_y, hex_grid_height - 1))
        
        return hex_x, hex_y
    
    def validate_city_terrain(hex_x: int, hex_y: int, city_name: str) -> Tuple[int, int]:
        """Validate city placement and adjust if on water"""
        if terrain_map and (hex_x, hex_y) in terrain_map:
            terrain = terrain_map[(hex_x, hex_y)]
            
            # If city is on water, try to find nearby land
            if terrain == CampaignTerrainType.WATER:
                print(f"   ⚠️  {city_name} placed on water at ({hex_x}, {hex_y}), searching for nearby land...")
                
                # Search in expanding radius for land
                for radius in range(1, 4):
                    for dx in range(-radius, radius + 1):
                        for dy in range(-radius, radius + 1):
                            if dx == 0 and dy == 0:
                                continue
                                
                            new_x = hex_x + dx
                            new_y = hex_y + dy
                            
                            if (0 <= new_x < hex_grid_width and 
                                0 <= new_y < hex_grid_height and
                                (new_x, new_y) in terrain_map and
                                (new_x, new_y) not in occupied_hexes):  # Check for city collisions too
                                
                                new_terrain = terrain_map[(new_x, new_y)]
                                if new_terrain != CampaignTerrainType.WATER:
                                    print(f"   ✅ Moved {city_name} to land at ({new_x}, {new_y}) - {new_terrain.value}")
                                    return new_x, new_y
                
                print(f"   ⚠️  Could not find land near {city_name}, keeping water placement")
        
        return hex_x, hex_y
    
    # Income based on city type and population
    def calculate_income(city_type: str, population: int) -> int:
        base_income = {
            'capital': 150,
            'major_city': 100,
            'medium_city': 60,
            'port': 80,
            'fortress': 40,
            'small_city': 30
        }
        base = base_income.get(city_type, 50)
        # Scale by population (rough estimate)
        population_factor = max(0.5, min(2.0, population / 10000))
        return int(base * population_factor)
    
    # Castle level based on city type and population
    def calculate_castle_level(city_type: str, population: int) -> int:
        if city_type == 'capital':
            return 3 if population > 50000 else 2
        elif city_type == 'major_city':
            return 2 if population > 30000 else 1
        elif city_type == 'fortress':
            return 2
        elif city_type == 'port':
            return 1 if population > 10000 else 0
        else:
            return 1 if population > 15000 else 0
    
    # Specialization based on city type and characteristics
    def determine_specialization(city_type: str, description: str, population: int) -> str:
        description_lower = description.lower()
        
        if city_type == 'port' or 'port' in description_lower:
            return 'trade'
        elif 'trading' in description_lower or 'commercial' in description_lower:
            return 'trade'
        elif 'university' in description_lower or 'learning' in description_lower:
            return 'education'
        elif 'fortress' in city_type or 'fortress' in description_lower:
            return 'military'
        elif 'archbishopric' in description_lower or 'cathedral' in description_lower:
            return 'religious'
        elif 'banking' in description_lower or 'finance' in description_lower:
            return 'trade'
        elif population > 50000:
            return 'trade'  # Large cities tend to be trading centers
        else:
            return 'agriculture'  # Default for smaller cities
    
    print(f"\n🎯 Using tile-system coordinate mapping (zoom level {zoom}, bounds: {bounds.west_lon:.1f}°W to {bounds.east_lon:.1f}°E, {bounds.south_lat:.1f}°N to {bounds.north_lat:.1f}°N)")
    
    # Track occupied hexes to avoid collisions
    occupied_hexes = {}
    collision_count = 0
    
    # Sort cities by importance (capitals first, then by population)
    sorted_cities = sorted(cities, key=lambda c: (
        0 if c.get('city_type') == 'capital' else 1,
        -c.get('estimated_population', 0)
    ))
    
    for city in sorted_cities:
        lat = city['latitude']
        lon = city['longitude']
        
        # Use advanced coordinate mapping
        hex_x, hex_y = advanced_coordinate_mapping(lat, lon)
        
        # Check for collision with already placed cities
        original_hex = (hex_x, hex_y)
        if original_hex in occupied_hexes:
            collision_count += 1
            # Try to find a nearby free hex
            found_free = False
            for radius in range(1, 4):  # Search up to 3 hexes away
                candidates = []
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if abs(dx) + abs(dy) <= radius * 1.5:  # Roughly circular search
                            new_x = hex_x + dx
                            new_y = hex_y + dy
                            if (0 <= new_x < hex_grid_width and 
                                0 <= new_y < hex_grid_height and
                                (new_x, new_y) not in occupied_hexes):
                                # Check terrain if available
                                if terrain_map and (new_x, new_y) in terrain_map:
                                    if terrain_map[(new_x, new_y)] != CampaignTerrainType.WATER:
                                        candidates.append((new_x, new_y))
                                else:
                                    candidates.append((new_x, new_y))
                
                if candidates:
                    # Choose the closest free hex
                    hex_x, hex_y = min(candidates, key=lambda h: abs(h[0] - original_hex[0]) + abs(h[1] - original_hex[1]))
                    found_free = True
                    break
            
            if found_free:
                print(f"   ⚠️  {city['name']} collision at {original_hex}, moved to ({hex_x}, {hex_y})")
        
        # Additional terrain validation
        if terrain_map:
            hex_x, hex_y = validate_city_terrain(hex_x, hex_y, city['name'])
        
        # Mark this hex as occupied
        occupied_hexes[(hex_x, hex_y)] = city['name']
        
        city_id = city['name'].lower().replace(' ', '_').replace('-', '_')
        city_type = city.get('city_type', 'medium_city')
        population = city.get('estimated_population', 5000)
        description = city.get('description', '')
        
        game_cities[city_id] = {
            "name": city['name'],
            "position": [hex_x, hex_y],
            "country": city.get('country', 'neutral'),
            "type": city_type,
            "population": population,
            "income": calculate_income(city_type, population),
            "castle_level": calculate_castle_level(city_type, population),
            "specialization": determine_specialization(city_type, description, population),
            "description": description,
            "modern_name": city.get('modern_name', city['name'])
        }
    
    return game_cities, collision_count, len(occupied_hexes)

def merge_adjacent_rectangles(rectangles: List[List[int]]) -> List[List[int]]:
    """Merge adjacent rectangles to reduce terrain data size and improve performance"""
    if not rectangles:
        return []
    
    # Sort rectangles by y, then x for easier merging
    rectangles.sort(key=lambda r: (r[2], r[0]))  # Sort by min_y, then min_x
    
    merged = []
    
    # Merge rectangles row by row
    current_row_rects = []
    current_y = rectangles[0][2]
    
    for rect in rectangles:
        min_x, max_x, min_y, max_y = rect
        
        # If we're in a new row, process the current row
        if min_y != current_y:
            merged.extend(merge_horizontal_rectangles(current_row_rects))
            current_row_rects = []
            current_y = min_y
        
        current_row_rects.append(rect)
    
    # Process the last row
    if current_row_rects:
        merged.extend(merge_horizontal_rectangles(current_row_rects))
    
    return merged

def merge_horizontal_rectangles(row_rectangles: List[List[int]]) -> List[List[int]]:
    """Merge horizontally adjacent rectangles in the same row"""
    if not row_rectangles:
        return []
    
    # Sort by x coordinate
    row_rectangles.sort(key=lambda r: r[0])
    
    merged_row = []
    current_rect = row_rectangles[0][:]
    
    for rect in row_rectangles[1:]:
        min_x, max_x, min_y, max_y = rect
        curr_min_x, curr_max_x, curr_min_y, curr_max_y = current_rect
        
        # Check if rectangles are adjacent horizontally and same height
        if curr_max_x == min_x and curr_min_y == min_y and curr_max_y == max_y:
            # Merge: extend the current rectangle
            current_rect[1] = max_x  # Update max_x
        else:
            # Can't merge: add current to result and start new one
            merged_row.append(current_rect)
            current_rect = rect[:]
    
    # Add the last rectangle
    merged_row.append(current_rect)
    return merged_row

def export_to_json(terrain_map: Dict, width: int, height: int, hex_size_km: float, 
                  output_path: str, bounds: GeographicBounds, zoom: int = 10, 
                  map_image: Image.Image = None, classifier: TileTerrainClassifier = None):
    """Export terrain map to game-compatible JSON format"""
    # Group terrain by type (initially as individual hexes)
    terrain_groups = {}
    for (hex_x, hex_y), terrain_type in terrain_map.items():
        terrain_name = terrain_type.value
        if terrain_name not in terrain_groups:
            terrain_groups[terrain_name] = []
        terrain_groups[terrain_name].append([hex_x, hex_x + 1, hex_y, hex_y + 1])
    
    # Merge adjacent rectangles for better performance
    print("🔄 Optimizing terrain rectangles...")
    original_count = sum(len(rects) for rects in terrain_groups.values())
    
    for terrain_name in terrain_groups:
        terrain_groups[terrain_name] = merge_adjacent_rectangles(terrain_groups[terrain_name])
    
    optimized_count = sum(len(rects) for rects in terrain_groups.values())
    reduction_percent = ((original_count - optimized_count) / original_count) * 100 if original_count > 0 else 0
    
    print(f"   📊 Rectangles: {original_count} → {optimized_count} ({reduction_percent:.1f}% reduction)")
    
    # Basic country definitions (same as OSM tool)
    countries = {
        "holy_roman_empire": {"name": "Holy Roman Empire", "color": [255, 215, 0], "capital": "aachen", "description": "Germanic empire", "starting_resources": {"gold": 3000}, "bonuses": {}},
        "france": {"name": "Kingdom of France", "color": [0, 0, 139], "capital": "paris", "description": "Capetian kingdom", "starting_resources": {"gold": 2500}, "bonuses": {}},
        "england": {"name": "Kingdom of England", "color": [255, 0, 0], "capital": "london", "description": "Norman kingdom", "starting_resources": {"gold": 2000}, "bonuses": {}},
        "poland": {"name": "Kingdom of Poland", "color": [220, 20, 60], "capital": "kraków", "description": "Piast kingdom", "starting_resources": {"gold": 1500}, "bonuses": {}},
        "hungary": {"name": "Kingdom of Hungary", "color": [0, 128, 0], "capital": "esztergom", "description": "Árpád kingdom", "starting_resources": {"gold": 1500}, "bonuses": {}},
        "denmark": {"name": "Kingdom of Denmark", "color": [139, 0, 0], "capital": "roskilde", "description": "Scandinavian kingdom", "starting_resources": {"gold": 1200}, "bonuses": {}},
        "byzantium": {"name": "Byzantine Empire", "color": [128, 0, 128], "capital": "konstantinoupolis", "description": "Eastern Roman Empire", "starting_resources": {"gold": 4000}, "bonuses": {}},
        "venice": {"name": "Republic of Venice", "color": [255, 165, 0], "capital": "venezia", "description": "Maritime republic", "starting_resources": {"gold": 2000}, "bonuses": {}},
    }
    
    # Load and process cities from medieval_cities_1200ad.json
    cities_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medieval_cities_1200ad.json')
    all_cities = load_medieval_cities(cities_file)
    filtered_cities = filter_cities_in_bounds(all_cities, bounds)
    cities, collision_count, unique_positions = convert_cities_to_hex_coordinates(
        filtered_cities, bounds, width, height, zoom, terrain_map, map_image, classifier)
    
    print(f"\n🏘️  Cities processing:")
    print(f"   Total cities in database: {len(all_cities)}")
    print(f"   Cities within map bounds: {len(filtered_cities)}")
    print(f"   Cities added to map: {len(cities)}")
    if collision_count > 0:
        print(f"   ⚠️  City collisions resolved: {collision_count}")
        print(f"   📍 Unique city positions: {unique_positions}")
    
    export_data = {
        "map": {"width": width, "height": height, "hex_size_km": hex_size_km, "terrain": terrain_groups},
        "countries": countries,
        "cities": cities,
        "neutral_regions": []
    }
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    # Print terrain statistics
    print("\n📊 Terrain distribution:")
    for terrain_type, hexes in sorted(terrain_groups.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(hexes)
        percentage = (count / len(terrain_map)) * 100
        print(f"   {terrain_type}: {count} hexes ({percentage:.1f}%)")
    
    # Print city statistics
    if cities:
        print("\n🏘️  City types distribution:")
        city_types = {}
        for city_data in cities.values():
            city_type = city_data['type']
            city_types[city_type] = city_types.get(city_type, 0) + 1
        
        for city_type, count in sorted(city_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {city_type}: {count} cities")

def main():
    """Main entry point for tile-based terrain generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate terrain map from OpenStreetMap tiles')
    parser.add_argument('--bounds', required=True,
                       help='Geographic bounds as west,south,east,north (e.g., 14,49,24,55)')
    parser.add_argument('--zoom', type=int, default=10,
                       help='Map zoom level (8-12 recommended for detailed terrain, default: 10)')
    parser.add_argument('-o', '--output', default='terrain_tiles.json',
                       help='Output JSON file (default: terrain_tiles.json)')
    parser.add_argument('--hex-size-km', type=float, default=30,
                       help='Target hex size in kilometers (default: 30)')
    parser.add_argument('--save-image', action='store_true',
                       help='Save the combined tile image for inspection')
    
    args = parser.parse_args()
    
    # Parse bounds
    try:
        west, south, east, north = map(float, args.bounds.split(','))
        bounds = GeographicBounds(west, east, south, north)
    except ValueError:
        print("❌ Error: bounds must be in format 'west,south,east,north' (e.g., 14,49,24,55)")
        return 1
    
    print("🗺️  Tile-Based Terrain Generator")
    print(f"   Bounds: {west:.1f}°W to {east:.1f}°E, {south:.1f}°S to {north:.1f}°N")
    print(f"   Zoom level: {args.zoom}")
    print(f"   Target hex size: {args.hex_size_km}km")
    
    fetcher = MapTileFetcher()
    classifier = TileTerrainClassifier()
    
    # Fetch tiles for the area
    map_image = fetcher.fetch_area_tiles(bounds, zoom=args.zoom)
    
    if map_image:
        print(f"🖼️  Generated map image: {map_image.size[0]}×{map_image.size[1]} pixels")
        
        if args.save_image:
            image_path = args.output.replace('.json', '_tiles.png')
            map_image.save(image_path)
            print(f"💾 Saved tile image as {image_path}")
        
        # Convert to hex-based terrain map
        print("\n🧩 Converting to hex grid...")
        
        # Calculate hex grid dimensions
        center_lat = (bounds.north_lat + bounds.south_lat) / 2
        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
        
        total_width_km = (bounds.east_lon - bounds.west_lon) * km_per_deg_lon
        total_height_km = (bounds.north_lat - bounds.south_lat) * km_per_deg_lat
        
        hex_grid_width = int(round(total_width_km / args.hex_size_km))
        hex_grid_height = int(round(total_height_km / args.hex_size_km))
        
        print(f"   Map dimensions: {hex_grid_width}×{hex_grid_height} hexes")
        print(f"   Actual hex size: {total_width_km/hex_grid_width:.1f}×{total_height_km/hex_grid_height:.1f}km")
        
        # Create terrain map by analyzing full hex areas
        terrain_map = {}
        img_width, img_height = map_image.size
        
        for hex_y in range(hex_grid_height):
            if hex_y % 20 == 0:
                print(f"   Processing row {hex_y}/{hex_grid_height}")
            
            for hex_x in range(hex_grid_width):
                # Calculate the full area covered by this hex
                hex_pixel_width = img_width / hex_grid_width
                hex_pixel_height = img_height / hex_grid_height
                
                # Define hex boundaries
                left = int(hex_x * hex_pixel_width)
                right = int((hex_x + 1) * hex_pixel_width)
                top = int(hex_y * hex_pixel_height)
                bottom = int((hex_y + 1) * hex_pixel_height)
                
                # Ensure we don't go out of bounds
                right = min(right, img_width - 1)
                bottom = min(bottom, img_height - 1)
                
                # Sample multiple points within the hex area
                terrain_votes = {}
                sample_count = 0
                
                # Sample every 2nd or 4th pixel to get good coverage without being too slow
                step = max(1, min(3, int(hex_pixel_width / 6)))
                
                for y in range(top, bottom, step):
                    for x in range(left, right, step):
                        try:
                            r, g, b = map_image.getpixel((x, y))
                            terrain_type = classifier.classify_pixel(r, g, b)
                            terrain_votes[terrain_type] = terrain_votes.get(terrain_type, 0) + 1
                            sample_count += 1
                        except IndexError:
                            # Skip out-of-bounds pixels
                            continue
                
                # Choose the most common terrain type
                if terrain_votes:
                    terrain_type = max(terrain_votes, key=terrain_votes.get)
                else:
                    # Fallback to center pixel if no samples
                    pixel_x = int((hex_x + 0.5) * img_width / hex_grid_width)
                    pixel_y = int((hex_y + 0.5) * img_height / hex_grid_height)
                    r, g, b = map_image.getpixel((pixel_x, pixel_y))
                    terrain_type = classifier.classify_pixel(r, g, b)
                
                terrain_map[(hex_x, hex_y)] = terrain_type
        
        # Export to JSON
        print(f"\n💾 Exporting to {args.output}...")
        export_to_json(terrain_map, hex_grid_width, hex_grid_height, args.hex_size_km, args.output, bounds, 
                      args.zoom, map_image, classifier)
        
        print(f"\n✅ Terrain generation complete!")
        print(f"   Generated: {args.output}")
        print(f"   Map size: {hex_grid_width}×{hex_grid_height} hexes")
        print(f"   Terrain hexes: {len(terrain_map)}")
        
        # For now, show sample classification
        width, height = map_image.size
        sample_points = [
            (width//4, height//4),      # NW
            (3*width//4, height//4),    # NE  
            (width//4, 3*height//4),    # SW
            (3*width//4, 3*height//4),  # SE
            (width//2, height//2),      # Center
        ]
        
        print("\n🔍 Sample terrain classification:")
        for i, (x, y) in enumerate(sample_points):
            r, g, b = map_image.getpixel((x, y))
            terrain = classifier.classify_pixel(r, g, b)
            print(f"   Point {i+1}: RGB({r},{g},{b}) -> {terrain.value}")
        
        return 0
    
    else:
        print("❌ Failed to fetch enough tiles")
        return 1

if __name__ == "__main__":
    sys.exit(main())