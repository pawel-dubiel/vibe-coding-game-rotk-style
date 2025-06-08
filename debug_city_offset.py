#!/usr/bin/env python3
"""
Debug why cities are offset by ~10 hexes down and right
"""

import sys
import os
import math
sys.path.append('tools')
from tile_terrain_generator import MapTileFetcher, GeographicBounds

def debug_coordinate_mapping():
    """Debug the coordinate mapping to find the offset issue"""
    
    # Your exact command bounds: --bounds="-15,35,45,70"
    bounds = GeographicBounds(west_lon=-15, east_lon=45, south_lat=35, north_lat=70)
    zoom = 6
    hex_size_km = 20
    
    print("🔍 Debugging City Offset Issue")
    print("=" * 80)
    
    fetcher = MapTileFetcher()
    
    # Step 1: Calculate tile bounds (as done in fetch_area_tiles)
    min_x, max_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
    max_x, min_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
    
    print(f"\n1️⃣ INTEGER Tile Bounds (used for image fetching):")
    print(f"   West/South corner: {bounds.west_lon}°, {bounds.south_lat}° -> tile ({min_x}, {max_y})")
    print(f"   East/North corner: {bounds.east_lon}°, {bounds.north_lat}° -> tile ({max_x}, {min_y})")
    print(f"   Tile range: X: {min_x} to {max_x}, Y: {min_y} to {max_y}")
    print(f"   Grid: {max_x - min_x + 1} × {max_y - min_y + 1} tiles")
    
    # Step 2: Get FRACTIONAL tile coordinates (what we use for city mapping)
    west_tile_x_float, south_tile_y_float = fetcher.deg2num_float(bounds.south_lat, bounds.west_lon, zoom)
    east_tile_x_float, north_tile_y_float = fetcher.deg2num_float(bounds.north_lat, bounds.east_lon, zoom)
    
    print(f"\n2️⃣ FRACTIONAL Tile Coordinates (for precise mapping):")
    print(f"   West/South: {bounds.west_lon}°, {bounds.south_lat}° -> tile ({west_tile_x_float:.3f}, {south_tile_y_float:.3f})")
    print(f"   East/North: {bounds.east_lon}°, {bounds.north_lat}° -> tile ({east_tile_x_float:.3f}, {north_tile_y_float:.3f})")
    
    # Show the difference
    print(f"\n3️⃣ Fractional vs Integer Differences:")
    print(f"   West X: {west_tile_x_float:.3f} vs {min_x} (diff: {west_tile_x_float - min_x:.3f})")
    print(f"   East X: {east_tile_x_float:.3f} vs {max_x} (diff: {east_tile_x_float - max_x:.3f})")
    print(f"   North Y: {north_tile_y_float:.3f} vs {min_y} (diff: {north_tile_y_float - min_y:.3f})")
    print(f"   South Y: {south_tile_y_float:.3f} vs {max_y} (diff: {south_tile_y_float - max_y:.3f})")
    
    # Step 3: Test specific cities
    test_cities = [
        {"name": "London", "lat": 51.51, "lon": -0.13},
        {"name": "Paris", "lat": 48.86, "lon": 2.35},
        {"name": "Rome", "lat": 41.90, "lon": 12.50},
        {"name": "Madrid", "lat": 40.42, "lon": -3.70},
    ]
    
    # Calculate hex grid dimensions (matching the actual code)
    center_lat = (bounds.north_lat + bounds.south_lat) / 2
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    total_width_km = (bounds.east_lon - bounds.west_lon) * km_per_deg_lon
    hex_grid_width = int(round(total_width_km / hex_size_km))
    
    # Use exact tile spans for height
    exact_tiles_x = east_tile_x_float - west_tile_x_float
    exact_tiles_y = south_tile_y_float - north_tile_y_float
    exact_aspect_ratio = exact_tiles_y / exact_tiles_x
    hex_grid_height = int(round(hex_grid_width * exact_aspect_ratio))
    
    print(f"\n4️⃣ Hex Grid Dimensions:")
    print(f"   Grid: {hex_grid_width} × {hex_grid_height} hexes")
    
    print(f"\n5️⃣ Testing City Mappings:")
    print(f"   Using INTEGER tile bounds for normalization (current code)")
    
    for city in test_cities:
        # Get fractional tile coordinates
        city_tile_x, city_tile_y = fetcher.deg2num_float(city['lat'], city['lon'], zoom)
        
        # Current normalization (using INTEGER bounds)
        tile_x_normalized = (city_tile_x - min_x) / (max_x - min_x) if max_x != min_x else 0
        tile_y_normalized = (city_tile_y - min_y) / (max_y - min_y) if max_y != min_y else 0
        
        hex_x = round(tile_x_normalized * (hex_grid_width - 1))
        hex_y = round(tile_y_normalized * (hex_grid_height - 1))
        
        print(f"\n   {city['name']} ({city['lat']}°, {city['lon']}°):")
        print(f"      Tile coords: ({city_tile_x:.3f}, {city_tile_y:.3f})")
        print(f"      Normalized: ({tile_x_normalized:.3f}, {tile_y_normalized:.3f})")
        print(f"      Hex position: ({hex_x}, {hex_y})")
    
    print(f"\n6️⃣ CORRECTED City Mappings:")
    print(f"   Using FRACTIONAL tile bounds for normalization (proposed fix)")
    
    for city in test_cities:
        # Get fractional tile coordinates
        city_tile_x, city_tile_y = fetcher.deg2num_float(city['lat'], city['lon'], zoom)
        
        # CORRECTED normalization (using FRACTIONAL bounds)
        tile_x_normalized = (city_tile_x - west_tile_x_float) / (east_tile_x_float - west_tile_x_float)
        tile_y_normalized = (city_tile_y - north_tile_y_float) / (south_tile_y_float - north_tile_y_float)
        
        hex_x = round(tile_x_normalized * (hex_grid_width - 1))
        hex_y = round(tile_y_normalized * (hex_grid_height - 1))
        
        print(f"\n   {city['name']} ({city['lat']}°, {city['lon']}°):")
        print(f"      Tile coords: ({city_tile_x:.3f}, {city_tile_y:.3f})")
        print(f"      Normalized: ({tile_x_normalized:.3f}, {tile_y_normalized:.3f})")
        print(f"      Hex position: ({hex_x}, {hex_y})")
    
    # Calculate the offset
    print(f"\n7️⃣ The Problem:")
    print(f"   The image starts at INTEGER tile boundaries")
    print(f"   But our bounds have FRACTIONAL tile positions")
    print(f"   This creates an offset in the normalization!")

if __name__ == "__main__":
    debug_coordinate_mapping()