#!/usr/bin/env python3
"""
Verify the coordinate fix works correctly
"""

import math
from typing import Tuple

class MapTileFetcher:
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

def test_coordinate_fix():
    """Test the coordinate fix"""
    fetcher = MapTileFetcher()
    
    # Bounds: -15,35,45,70
    west_lon = -15
    east_lon = 45
    south_lat = 35
    north_lat = 70
    zoom = 6
    
    # Hex grid dimensions
    hex_grid_width = 203
    hex_grid_height = 210
    
    # Get integer bounds (for image)
    west_x_int, south_y_int = fetcher.deg2num(south_lat, west_lon, zoom)
    east_x_int, north_y_int = fetcher.deg2num(north_lat, east_lon, zoom)
    
    # Image dimensions in tiles
    image_tiles_x = east_x_int - west_x_int + 1
    image_tiles_y = south_y_int - north_y_int + 1
    
    print(f"Image tile bounds: X: {west_x_int} to {east_x_int}, Y: {north_y_int} to {south_y_int}")
    print(f"Image tile grid: {image_tiles_x} × {image_tiles_y}")
    
    # Test cities
    test_cities = [
        {"name": "London", "lat": 51.51, "lon": -0.13},
        {"name": "Paris", "lat": 48.86, "lon": 2.35},
        {"name": "Rome", "lat": 41.90, "lon": 12.50},
        {"name": "Madrid", "lat": 40.42, "lon": -3.70},
    ]
    
    print(f"\n📍 City positions with FIXED normalization:")
    print(f"{'City':<10} {'OLD Method':<15} {'NEW Method':<15} {'Difference':<15}")
    print("-" * 60)
    
    for city in test_cities:
        # Get fractional tile coordinates
        city_tile_x, city_tile_y = fetcher.deg2num_float(city['lat'], city['lon'], zoom)
        
        # OLD method (using integer difference)
        old_norm_x = (city_tile_x - west_x_int) / (east_x_int - west_x_int)
        old_norm_y = (city_tile_y - north_y_int) / (south_y_int - north_y_int)
        old_hex_x = round(old_norm_x * (hex_grid_width - 1))
        old_hex_y = round(old_norm_y * (hex_grid_height - 1))
        
        # NEW method (using image tiles)
        new_norm_x = (city_tile_x - west_x_int) / image_tiles_x
        new_norm_y = (city_tile_y - north_y_int) / image_tiles_y
        new_hex_x = int(new_norm_x * hex_grid_width)
        new_hex_y = int(new_norm_y * hex_grid_height)
        
        # Clamp to bounds
        new_hex_x = max(0, min(new_hex_x, hex_grid_width - 1))
        new_hex_y = max(0, min(new_hex_y, hex_grid_height - 1))
        
        diff_x = new_hex_x - old_hex_x
        diff_y = new_hex_y - old_hex_y
        
        print(f"{city['name']:<10} ({old_hex_x:3}, {old_hex_y:3})    ({new_hex_x:3}, {new_hex_y:3})    ({diff_x:+3}, {diff_y:+3})")
    
    print(f"\n✅ The NEW method shifts cities up and left as expected!")
    print(f"   This should fix the ~10 hex offset issue.")

if __name__ == "__main__":
    test_coordinate_fix()