#!/usr/bin/env python3
"""
Test the improved coordinate mapping using image aspect ratio
"""

import sys
import os
import math
sys.path.append('tools')
from tile_terrain_generator import MapTileFetcher, GeographicBounds, load_medieval_cities, filter_cities_in_bounds

def test_improved_mapping():
    """Test the improved mapping with the exact bounds from your command"""
    
    # Your exact command bounds: --bounds="-15,35,45,70"
    bounds = GeographicBounds(west_lon=-15, east_lon=45, south_lat=35, north_lat=70)
    zoom = 6
    hex_size_km = 20
    
    print(f"🗺️  Testing IMPROVED coordinate mapping")
    print(f"   Bounds: {bounds.west_lon}°W to {bounds.east_lon}°E, {bounds.south_lat}°N to {bounds.north_lat}°N")
    print(f"   Zoom: {zoom}")
    print(f"   Hex size: {hex_size_km}km")
    
    # Calculate tile dimensions to simulate the image aspect ratio approach
    fetcher = MapTileFetcher()
    
    # Calculate tile bounds (same as in fetch_area_tiles)
    min_x, max_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
    max_x, min_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
    
    tiles_x = max_x - min_x + 1
    tiles_y = max_y - min_y + 1
    
    # Standard tile size is 256 pixels
    tile_size = 256
    img_width = tiles_x * tile_size
    img_height = tiles_y * tile_size
    
    print(f"\n📐 Image-based grid calculations:")
    print(f"   Tile grid: {tiles_x} × {tiles_y} tiles")
    print(f"   Image size: {img_width} × {img_height} pixels")
    
    # Use the NEW approach: width from km, height from aspect ratio
    center_lat = (bounds.north_lat + bounds.south_lat) / 2
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    total_width_km = (bounds.east_lon - bounds.west_lon) * km_per_deg_lon
    
    hex_grid_width = int(round(total_width_km / hex_size_km))
    
    # NEW: Calculate height based on image aspect ratio
    image_aspect_ratio = img_height / img_width
    hex_grid_height = int(round(hex_grid_width * image_aspect_ratio))
    
    print(f"   Image aspect ratio: {image_aspect_ratio:.3f}")
    print(f"   NEW hex grid: {hex_grid_width} × {hex_grid_height} hexes")
    print(f"   Width hex size: {total_width_km/hex_grid_width:.1f}km")
    
    # Compare with OLD approach
    km_per_deg_lat = 111.32
    total_height_km = (bounds.north_lat - bounds.south_lat) * km_per_deg_lat
    old_hex_grid_height = int(round(total_height_km / hex_size_km))
    
    print(f"\n📊 Comparison:")
    print(f"   OLD approach: {hex_grid_width} × {old_hex_grid_height} hexes")
    print(f"   NEW approach: {hex_grid_width} × {hex_grid_height} hexes")
    print(f"   Height difference: {hex_grid_height - old_hex_grid_height} hexes")
    
    # Test coordinate mapping with the new approach
    print(f"\n🎯 Testing coordinate mapping with NEW approach:")
    
    # Get map bounds in tile coordinates
    west_x, south_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
    east_x, north_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
    
    min_tile_x = west_x
    max_tile_x = east_x
    min_tile_y = north_y  # North is MIN Y in tile coords
    max_tile_y = south_y  # South is MAX Y in tile coords
    
    # Load some sample cities and test their mapping
    cities_file = 'medieval_cities_1200ad.json'
    all_cities = load_medieval_cities(cities_file)
    filtered_cities = filter_cities_in_bounds(all_cities, bounds)
    
    print(f"   Cities to test: {len(filtered_cities)}")
    
    # Test a few key cities with NEW mapping
    test_cities = []
    for city in filtered_cities[:30]:  # Test first 30 cities
        lat = city['latitude']
        lon = city['longitude']
        
        # Convert to tile coordinates (using float for better precision)
        city_tile_x, city_tile_y = fetcher.deg2num_float(lat, lon, zoom)
        
        # Normalize
        tile_x_normalized = (city_tile_x - min_tile_x) / (max_tile_x - min_tile_x) if max_tile_x != min_tile_x else 0
        tile_y_normalized = (city_tile_y - min_tile_y) / (max_tile_y - min_tile_y) if max_tile_y != min_tile_y else 0
        
        # Convert to hex using NEW grid dimensions
        hex_x = round(tile_x_normalized * (hex_grid_width - 1))
        hex_y = round(tile_y_normalized * (hex_grid_height - 1))
        
        test_cities.append({
            'name': city['name'],
            'lat': lat,
            'lon': lon,
            'hex_x': hex_x,
            'hex_y': hex_y
        })
    
    # Check for duplicates with NEW approach
    positions = [(city['hex_x'], city['hex_y']) for city in test_cities]
    unique_positions = set(positions)
    
    print(f"\n🎯 NEW approach duplicate analysis:")
    print(f"   Total cities tested: {len(test_cities)}")
    print(f"   Unique positions: {len(unique_positions)}")
    print(f"   Duplicates: {len(test_cities) - len(unique_positions)}")
    
    # Show duplicates
    from collections import Counter
    position_counts = Counter(positions)
    duplicates = {pos: count for pos, count in position_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n⚠️  Positions with multiple cities (NEW approach):")
        for (x, y), count in duplicates.items():
            cities_at_pos = [city['name'] for city in test_cities if city['hex_x'] == x and city['hex_y'] == y]
            print(f"   ({x}, {y}): {count} cities - {', '.join(cities_at_pos)}")
    else:
        print(f"\n✅ No duplicate positions with NEW approach!")
    
    # Calculate resolution analysis
    degrees_per_hex_x = (bounds.east_lon - bounds.west_lon) / hex_grid_width
    degrees_per_hex_y = (bounds.north_lat - bounds.south_lat) / hex_grid_height
    
    print(f"\n📏 NEW approach resolution:")
    print(f"   Degrees per hex: {degrees_per_hex_x:.3f}° longitude × {degrees_per_hex_y:.3f}° latitude")
    print(f"   At 50°N: ~{degrees_per_hex_x * 71:.1f}km × {degrees_per_hex_y * 111:.1f}km per hex")

if __name__ == "__main__":
    test_improved_mapping()