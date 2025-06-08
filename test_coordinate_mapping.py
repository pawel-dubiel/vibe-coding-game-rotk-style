#!/usr/bin/env python3
"""
Test coordinate mapping to understand why multiple cities end up in same hex
"""

import sys
import os
import math
sys.path.append('tools')
from tile_terrain_generator import MapTileFetcher, GeographicBounds, load_medieval_cities, filter_cities_in_bounds

def test_coordinate_mapping():
    """Test the coordinate mapping with the exact bounds from your command"""
    
    # Your exact command bounds: --bounds="-15,35,45,70"
    bounds = GeographicBounds(west_lon=-15, east_lon=45, south_lat=35, north_lat=70)
    zoom = 6
    hex_size_km = 20
    
    print(f"🗺️  Testing coordinate mapping")
    print(f"   Bounds: {bounds.west_lon}°W to {bounds.east_lon}°E, {bounds.south_lat}°N to {bounds.north_lat}°N")
    print(f"   Zoom: {zoom}")
    print(f"   Hex size: {hex_size_km}km")
    
    # Calculate hex grid dimensions (same as in main())
    center_lat = (bounds.north_lat + bounds.south_lat) / 2
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    
    total_width_km = (bounds.east_lon - bounds.west_lon) * km_per_deg_lon
    total_height_km = (bounds.north_lat - bounds.south_lat) * km_per_deg_lat
    
    hex_grid_width = int(round(total_width_km / hex_size_km))
    hex_grid_height = int(round(total_height_km / hex_size_km))
    
    print(f"\n📐 Grid calculations:")
    print(f"   Center latitude: {center_lat:.1f}°")
    print(f"   km/deg at center: {km_per_deg_lat:.1f} lat, {km_per_deg_lon:.1f} lon")
    print(f"   Total area: {total_width_km:.0f} × {total_height_km:.0f} km")
    print(f"   Hex grid: {hex_grid_width} × {hex_grid_height} hexes")
    print(f"   Actual hex size: {total_width_km/hex_grid_width:.1f} × {total_height_km/hex_grid_height:.1f} km")
    
    # Test tile coordinate mapping
    fetcher = MapTileFetcher()
    
    # Get map bounds in tile coordinates
    west_x, south_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
    east_x, north_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
    
    min_tile_x = west_x
    max_tile_x = east_x  
    min_tile_y = north_y  # North is MIN Y in tile coords
    max_tile_y = south_y  # South is MAX Y in tile coords
    
    print(f"\n🔢 Tile coordinate bounds (zoom {zoom}):")
    print(f"   X range: {min_tile_x} to {max_tile_x} ({max_tile_x - min_tile_x + 1} tiles)")
    print(f"   Y range: {min_tile_y} to {max_tile_y} ({max_tile_y - min_tile_y + 1} tiles)")
    
    # Calculate tile size in degrees
    tile_width_deg = (bounds.east_lon - bounds.west_lon) / (max_tile_x - min_tile_x)
    tile_height_deg = (bounds.north_lat - bounds.south_lat) / (max_tile_y - min_tile_y)
    
    print(f"   Tile size: {tile_width_deg:.3f}° × {tile_height_deg:.3f}°")
    
    # Load some sample cities and test their mapping
    cities_file = 'medieval_cities_1200ad.json'
    all_cities = load_medieval_cities(cities_file)
    filtered_cities = filter_cities_in_bounds(all_cities, bounds)
    
    print(f"\n🏘️  Testing city mapping:")
    print(f"   Total cities in bounds: {len(filtered_cities)}")
    
    # Test a few key cities
    test_cities = []
    for city in filtered_cities[:20]:  # Test first 20 cities
        lat = city['latitude']
        lon = city['longitude']
        
        # Convert to tile coordinates
        city_tile_x, city_tile_y = fetcher.deg2num(lat, lon, zoom)
        
        # Normalize
        tile_x_normalized = (city_tile_x - min_tile_x) / (max_tile_x - min_tile_x) if max_tile_x != min_tile_x else 0
        tile_y_normalized = (city_tile_y - min_tile_y) / (max_tile_y - min_tile_y) if max_tile_y != min_tile_y else 0
        
        # Convert to hex
        hex_x = round(tile_x_normalized * (hex_grid_width - 1))
        hex_y = round(tile_y_normalized * (hex_grid_height - 1))
        
        test_cities.append({
            'name': city['name'],
            'lat': lat,
            'lon': lon,
            'tile_x': city_tile_x,
            'tile_y': city_tile_y,
            'norm_x': tile_x_normalized,
            'norm_y': tile_y_normalized,
            'hex_x': hex_x,
            'hex_y': hex_y
        })
    
    # Show the mapping
    print(f"\n📍 Sample city mappings:")
    print(f"{'Name':<15} {'Lat':<7} {'Lon':<7} {'TileX':<6} {'TileY':<6} {'NormX':<6} {'NormY':<6} {'HexX':<5} {'HexY':<5}")
    print("-" * 80)
    
    for city in test_cities:
        print(f"{city['name']:<15} {city['lat']:<7.2f} {city['lon']:<7.2f} "
              f"{city['tile_x']:<6} {city['tile_y']:<6} "
              f"{city['norm_x']:<6.3f} {city['norm_y']:<6.3f} "
              f"{city['hex_x']:<5} {city['hex_y']:<5}")
    
    # Check for duplicates
    positions = [(city['hex_x'], city['hex_y']) for city in test_cities]
    unique_positions = set(positions)
    
    print(f"\n🎯 Duplicate analysis:")
    print(f"   Total cities tested: {len(test_cities)}")
    print(f"   Unique positions: {len(unique_positions)}")
    print(f"   Duplicates: {len(test_cities) - len(unique_positions)}")
    
    # Show duplicates
    from collections import Counter
    position_counts = Counter(positions)
    duplicates = {pos: count for pos, count in position_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n⚠️  Positions with multiple cities:")
        for (x, y), count in duplicates.items():
            cities_at_pos = [city['name'] for city in test_cities if city['hex_x'] == x and city['hex_y'] == y]
            print(f"   ({x}, {y}): {count} cities - {', '.join(cities_at_pos)}")
    
    # Calculate resolution analysis
    degrees_per_hex_x = (bounds.east_lon - bounds.west_lon) / hex_grid_width
    degrees_per_hex_y = (bounds.north_lat - bounds.south_lat) / hex_grid_height
    
    print(f"\n📏 Resolution analysis:")
    print(f"   Degrees per hex: {degrees_per_hex_x:.3f}° longitude × {degrees_per_hex_y:.3f}° latitude")
    print(f"   At 50°N: ~{degrees_per_hex_x * 71:.1f}km × {degrees_per_hex_y * 111:.1f}km per hex")
    print(f"   Cities closer than this will likely share a hex")

if __name__ == "__main__":
    test_coordinate_mapping()