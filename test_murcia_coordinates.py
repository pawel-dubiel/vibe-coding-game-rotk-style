#!/usr/bin/env python3
"""
Test script to analyze coordinate transformation for Murcia placement
"""

import math
import json
import os

# Murcia coordinates from the cities database
MURCIA_LAT = 37.9922
MURCIA_LON = -1.1307

# Bounds used for Europe map (typical Europe bounds)
# These are estimated bounds that would include Western Europe
EUROPE_BOUNDS = {
    'west_lon': -10.0,   # Western Ireland/Portugal
    'east_lon': 30.0,    # Eastern Poland/Baltic
    'south_lat': 35.0,   # Southern Spain/Sicily
    'north_lat': 60.0,   # Northern Scandinavia
}

# Map dimensions from the generated file
MAP_WIDTH = 81
MAP_HEIGHT = 78
ZOOM = 10  # Typical zoom level for Europe

def lat_lon_to_web_mercator(lat: float, lon: float) -> tuple[float, float]:
    """Convert lat/lon to Web Mercator coordinates (EPSG:3857)"""
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return x, y

def web_mercator_to_tile_coords(x: float, y: float, zoom: int) -> tuple[float, float]:
    """Convert Web Mercator to tile coordinates"""
    n = 2.0 ** zoom
    tile_x = (x + 20037508.34) / (2 * 20037508.34) * n
    tile_y = (20037508.34 - y) / (2 * 20037508.34) * n
    return tile_x, tile_y

def get_tile_bounds_web_mercator(bounds: dict, zoom: int) -> tuple[float, float, float, float]:
    """Get tile coordinate bounds in Web Mercator"""
    # Convert geographic bounds to Web Mercator
    west_merc, south_merc = lat_lon_to_web_mercator(bounds['south_lat'], bounds['west_lon'])
    east_merc, north_merc = lat_lon_to_web_mercator(bounds['north_lat'], bounds['east_lon'])
    
    # Convert to tile coordinates
    min_tile_x, max_tile_y = web_mercator_to_tile_coords(west_merc, south_merc, zoom)
    max_tile_x, min_tile_y = web_mercator_to_tile_coords(east_merc, north_merc, zoom)
    
    return min_tile_x, min_tile_y, max_tile_x, max_tile_y

def convert_coordinate_to_hex(lat: float, lon: float, bounds: dict, map_width: int, map_height: int, zoom: int):
    """Convert city coordinates to hex grid using Web Mercator projection"""
    print(f"\n=== Converting {lat:.4f}°N, {lon:.4f}°W to hex coordinates ===")
    
    # Step 1: Convert city coordinates to Web Mercator
    city_x_merc, city_y_merc = lat_lon_to_web_mercator(lat, lon)
    print(f"1. Web Mercator: ({city_x_merc:.2f}, {city_y_merc:.2f})")
    
    # Step 2: Convert to tile coordinates
    city_tile_x, city_tile_y = web_mercator_to_tile_coords(city_x_merc, city_y_merc, zoom)
    print(f"2. Tile coordinates: ({city_tile_x:.4f}, {city_tile_y:.4f})")
    
    # Step 3: Get map bounds in tile coordinates
    min_tile_x, min_tile_y, max_tile_x, max_tile_y = get_tile_bounds_web_mercator(bounds, zoom)
    print(f"3. Map bounds (tiles): X[{min_tile_x:.4f}, {max_tile_x:.4f}], Y[{min_tile_y:.4f}, {max_tile_y:.4f}]")
    
    # Step 4: Convert to hex grid coordinates
    hex_x = int((city_tile_x - min_tile_x) / (max_tile_x - min_tile_x) * map_width)
    hex_y = int((city_tile_y - min_tile_y) / (max_tile_y - min_tile_y) * map_height)
    
    print(f"4. Raw hex coordinates: ({hex_x}, {hex_y})")
    
    # Step 5: Clamp to grid bounds
    hex_x_clamped = max(0, min(hex_x, map_width - 1))
    hex_y_clamped = max(0, min(hex_y, map_height - 1))
    
    print(f"5. Clamped hex coordinates: ({hex_x_clamped}, {hex_y_clamped})")
    
    # Calculate relative position within bounds
    rel_x = (city_tile_x - min_tile_x) / (max_tile_x - min_tile_x)
    rel_y = (city_tile_y - min_tile_y) / (max_tile_y - min_tile_y)
    
    print(f"6. Relative position: ({rel_x:.4f}, {rel_y:.4f})")
    
    return hex_x_clamped, hex_y_clamped

def analyze_current_placement():
    """Analyze the current placement from the generated file"""
    campaign_file = '/Users/pawel/work/game/campaign/medieval_europe.json'
    
    try:
        with open(campaign_file, 'r') as f:
            data = json.load(f)
        
        murcia_data = data['cities'].get('murcia')
        if murcia_data:
            print(f"\n=== Current placement in medieval_europe.json ===")
            print(f"Murcia position: {murcia_data['position']}")
            print(f"Map dimensions: {data['map']['width']}x{data['map']['height']}")
            print(f"Hex size: {data['map']['hex_size_km']}km")
            
            # Calculate relative position
            rel_x = murcia_data['position'][0] / data['map']['width']
            rel_y = murcia_data['position'][1] / data['map']['height']
            print(f"Relative position: ({rel_x:.4f}, {rel_y:.4f})")
            
            return murcia_data['position']
        else:
            print("Murcia not found in current campaign file")
            return None
            
    except Exception as e:
        print(f"Error reading campaign file: {e}")
        return None

def test_different_bounds():
    """Test different possible bounds to see which might have been used"""
    print("\n=== Testing different possible bounds ===")
    
    # Current placement from file
    current_pos = analyze_current_placement()
    
    if current_pos:
        target_x, target_y = current_pos
        print(f"\nTarget position: ({target_x}, {target_y})")
        
        # Test different bounds
        test_bounds = [
            {'name': 'Wide Europe', 'west_lon': -10.0, 'east_lon': 30.0, 'south_lat': 35.0, 'north_lat': 60.0},
            {'name': 'Central Europe', 'west_lon': -5.0, 'east_lon': 25.0, 'south_lat': 40.0, 'north_lat': 55.0},
            {'name': 'Extended Europe', 'west_lon': -15.0, 'east_lon': 35.0, 'south_lat': 30.0, 'north_lat': 65.0},
            {'name': 'Western Focus', 'west_lon': -10.0, 'east_lon': 20.0, 'south_lat': 35.0, 'north_lat': 60.0},
        ]
        
        for bounds_test in test_bounds:
            print(f"\n--- Testing {bounds_test['name']} ---")
            print(f"Bounds: {bounds_test['west_lon']:.1f}°W to {bounds_test['east_lon']:.1f}°E, {bounds_test['south_lat']:.1f}°S to {bounds_test['north_lat']:.1f}°N")
            
            hex_x, hex_y = convert_coordinate_to_hex(
                MURCIA_LAT, MURCIA_LON, bounds_test, MAP_WIDTH, MAP_HEIGHT, ZOOM
            )
            
            diff_x = abs(hex_x - target_x)
            diff_y = abs(hex_y - target_y)
            total_diff = diff_x + diff_y
            
            print(f"Result: ({hex_x}, {hex_y}) - Difference: ({diff_x}, {diff_y}) = {total_diff}")

def test_coordinate_reversal():
    """Test if there might be a coordinate reversal issue"""
    print("\n=== Testing coordinate reversal scenarios ===")
    
    current_pos = analyze_current_placement()
    if not current_pos:
        return
        
    target_x, target_y = current_pos
    bounds = EUROPE_BOUNDS
    
    # Test normal coordinates
    print("\n1. Normal coordinates:")
    hex_x, hex_y = convert_coordinate_to_hex(MURCIA_LAT, MURCIA_LON, bounds, MAP_WIDTH, MAP_HEIGHT, ZOOM)
    print(f"Result: ({hex_x}, {hex_y}) vs target ({target_x}, {target_y})")
    
    # Test Y-axis flipped
    print("\n2. Y-axis flipped (hex_y = height - hex_y):")
    hex_x, hex_y_flipped = convert_coordinate_to_hex(MURCIA_LAT, MURCIA_LON, bounds, MAP_WIDTH, MAP_HEIGHT, ZOOM)
    hex_y_flipped = MAP_HEIGHT - 1 - hex_y_flipped
    print(f"Result: ({hex_x}, {hex_y_flipped}) vs target ({target_x}, {target_y})")
    
    # Test X-axis flipped  
    print("\n3. X-axis flipped (hex_x = width - hex_x):")
    hex_x_flipped, hex_y = convert_coordinate_to_hex(MURCIA_LAT, MURCIA_LON, bounds, MAP_WIDTH, MAP_HEIGHT, ZOOM)
    hex_x_flipped = MAP_WIDTH - 1 - hex_x_flipped
    print(f"Result: ({hex_x_flipped}, {hex_y}) vs target ({target_x}, {target_y})")
    
    # Test both axes flipped
    print("\n4. Both axes flipped:")
    hex_x_both, hex_y_both = convert_coordinate_to_hex(MURCIA_LAT, MURCIA_LON, bounds, MAP_WIDTH, MAP_HEIGHT, ZOOM)
    hex_x_both = MAP_WIDTH - 1 - hex_x_both
    hex_y_both = MAP_HEIGHT - 1 - hex_y_both
    print(f"Result: ({hex_x_both}, {hex_y_both}) vs target ({target_x}, {target_y})")

def main():
    print("🔍 Analyzing Murcia coordinate transformation")
    print(f"Murcia location: {MURCIA_LAT:.4f}°N, {MURCIA_LON:.4f}°W (southeastern Spain)")
    
    # Analyze current placement
    analyze_current_placement()
    
    # Test basic conversion with estimated bounds
    print(f"\n=== Basic conversion with estimated Europe bounds ===")
    convert_coordinate_to_hex(MURCIA_LAT, MURCIA_LON, EUROPE_BOUNDS, MAP_WIDTH, MAP_HEIGHT, ZOOM)
    
    # Test different bounds
    test_different_bounds()
    
    # Test coordinate reversal scenarios
    test_coordinate_reversal()

if __name__ == "__main__":
    main()