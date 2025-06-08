#!/usr/bin/env python3
"""
Test the fixed coordinate mapping
"""

import sys
import os
import math
sys.path.append('tools')
from tile_terrain_generator import MapTileFetcher, GeographicBounds

def test_fixed_mapping():
    """Test the fixed coordinate mapping"""
    
    # Your exact command bounds: --bounds="-15,35,45,70"
    bounds = GeographicBounds(west_lon=-15, east_lon=45, south_lat=35, north_lat=70)
    zoom = 6
    hex_size_km = 20
    
    print("🔧 Testing FIXED Coordinate Mapping")
    print("=" * 80)
    
    fetcher = MapTileFetcher()
    
    # Calculate hex grid dimensions (matching the actual code)
    center_lat = (bounds.north_lat + bounds.south_lat) / 2
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    total_width_km = (bounds.east_lon - bounds.west_lon) * km_per_deg_lon
    hex_grid_width = int(round(total_width_km / hex_size_km))
    
    # Use exact tile spans for height
    west_tile_x_float, south_tile_y_float = fetcher.deg2num_float(bounds.south_lat, bounds.west_lon, zoom)
    east_tile_x_float, north_tile_y_float = fetcher.deg2num_float(bounds.north_lat, bounds.east_lon, zoom)
    exact_tiles_x = east_tile_x_float - west_tile_x_float
    exact_tiles_y = south_tile_y_float - north_tile_y_float
    exact_aspect_ratio = exact_tiles_y / exact_tiles_x
    hex_grid_height = int(round(hex_grid_width * exact_aspect_ratio))
    
    print(f"Hex Grid: {hex_grid_width} × {hex_grid_height}")
    
    # Test cities with FIXED mapping
    test_cities = [
        {"name": "London", "lat": 51.51, "lon": -0.13},
        {"name": "Paris", "lat": 48.86, "lon": 2.35},
        {"name": "Rome", "lat": 41.90, "lon": 12.50},
        {"name": "Madrid", "lat": 40.42, "lon": -3.70},
        {"name": "Berlin", "lat": 52.52, "lon": 13.41},
        {"name": "Warsaw", "lat": 52.23, "lon": 21.01},
    ]
    
    # Get integer bounds (for image)
    west_x_int, south_y_int = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
    east_x_int, north_y_int = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
    
    # Image dimensions in tiles
    image_tiles_x = east_x_int - west_x_int + 1
    image_tiles_y = south_y_int - north_y_int + 1
    
    print(f"\nImage tile grid: {image_tiles_x} × {image_tiles_y}")
    print(f"Integer bounds: X: {west_x_int} to {east_x_int}, Y: {north_y_int} to {south_y_int}")
    
    print(f"\n📍 City Mappings with FIXED normalization:")
    
    for city in test_cities:
        # Get fractional tile coordinates
        city_tile_x, city_tile_y = fetcher.deg2num_float(city['lat'], city['lon'], zoom)
        
        # FIXED normalization (matching the code)
        city_x_in_image = (city_tile_x - west_x_int) / image_tiles_x
        city_y_in_image = (city_tile_y - north_y_int) / image_tiles_y
        
        hex_x = round(city_x_in_image * (hex_grid_width - 1))
        hex_y = round(city_y_in_image * (hex_grid_height - 1))
        
        print(f"\n{city['name']} ({city['lat']}°, {city['lon']}°):")
        print(f"   Tile: ({city_tile_x:.3f}, {city_tile_y:.3f})")
        print(f"   Normalized: ({city_x_in_image:.3f}, {city_y_in_image:.3f})")
        print(f"   Hex: ({hex_x}, {hex_y})")
        
        # Compare with old method
        old_x_norm = (city_tile_x - west_x_int) / (east_x_int - west_x_int)
        old_y_norm = (city_tile_y - north_y_int) / (south_y_int - north_y_int)
        old_hex_x = round(old_x_norm * (hex_grid_width - 1))
        old_hex_y = round(old_y_norm * (hex_grid_height - 1))
        
        print(f"   Old hex: ({old_hex_x}, {old_hex_y})")
        print(f"   Difference: ({hex_x - old_hex_x}, {hex_y - old_hex_y})")

if __name__ == "__main__":
    test_fixed_mapping()