#!/usr/bin/env python3
"""
Analyze why multiple cities are being placed in the same hex
"""

import json
from collections import defaultdict

def analyze_duplicate_positions():
    """Find cities that share the same hex position"""
    
    # Load current map
    with open('game/campaign/medieval_europe.json', 'r') as f:
        map_data = json.load(f)
    
    # Load city database to get original coordinates
    with open('medieval_cities_1200ad.json', 'r') as f:
        cities_data = json.load(f)
    
    # Create lookup for original coordinates
    city_coords = {city['name'].lower().replace(' ', '_'): city for city in cities_data['cities']}
    
    # Group cities by position
    position_groups = defaultdict(list)
    for city_id, city_data in map_data['cities'].items():
        pos = tuple(city_data['position'])
        position_groups[pos].append((city_id, city_data['name']))
    
    # Find duplicates
    duplicates = {pos: cities for pos, cities in position_groups.items() if len(cities) > 1}
    
    print(f"🔍 Duplicate Position Analysis")
    print(f"=" * 80)
    print(f"Total cities: {len(map_data['cities'])}")
    print(f"Unique positions: {len(position_groups)}")
    print(f"Positions with multiple cities: {len(duplicates)}")
    print(f"Cities affected by duplicates: {sum(len(cities) for cities in duplicates.values())}")
    
    # Show worst duplicates
    print(f"\n📍 Worst duplicate positions (top 10):")
    sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    
    for pos, cities in sorted_dups:
        print(f"\nPosition {pos}: {len(cities)} cities")
        
        # Get original coordinates for these cities
        coords_info = []
        for city_id, city_name in cities:
            if city_id in city_coords:
                orig = city_coords[city_id]
                coords_info.append((city_name, orig['latitude'], orig['longitude']))
        
        # Sort by latitude to see geographic spread
        coords_info.sort(key=lambda x: x[1], reverse=True)
        
        for name, lat, lon in coords_info:
            print(f"  - {name:20} ({lat:.2f}°N, {lon:.2f}°E)")
        
        # Calculate spread
        if coords_info:
            lats = [c[1] for c in coords_info]
            lons = [c[2] for c in coords_info]
            lat_spread = max(lats) - min(lats)
            lon_spread = max(lons) - min(lons)
            print(f"  Geographic spread: {lat_spread:.2f}° lat × {lon_spread:.2f}° lon")

def analyze_map_resolution():
    """Analyze the effective resolution of the hex grid"""
    
    with open('game/campaign/medieval_europe.json', 'r') as f:
        map_data = json.load(f)
    
    map_width = map_data['map']['width']
    map_height = map_data['map']['height']
    hex_size_km = map_data['map']['hex_size_km']
    
    print(f"\n\n📏 Map Resolution Analysis")
    print(f"=" * 80)
    print(f"Map dimensions: {map_width} × {map_height} hexes")
    print(f"Hex size: {hex_size_km} km")
    print(f"Total coverage: {map_width * hex_size_km:.0f} × {map_height * hex_size_km:.0f} km")
    
    # Estimate geographic coverage based on extreme cities
    # (This is approximate since we don't have the exact bounds used)
    cities = map_data['cities']
    if cities:
        positions = [city['position'] for city in cities.values()]
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]
        
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        
        print(f"\nCity position range: {x_range} × {y_range} hexes")
        print(f"Average cities per hex (if evenly distributed): {len(cities) / (x_range * y_range):.2f}")
        
        # At 50° latitude, 1° ≈ 111km lat, 71km lon
        if hex_size_km > 0:
            degrees_per_hex_lat = hex_size_km / 111
            degrees_per_hex_lon = hex_size_km / 71
            
            print(f"\nApproximate resolution at 50°N:")
            print(f"  Each hex covers: {degrees_per_hex_lat:.3f}° latitude × {degrees_per_hex_lon:.3f}° longitude")
            print(f"  Cities within {degrees_per_hex_lat*60:.1f}' lat × {degrees_per_hex_lon*60:.1f}' lon may share a hex")

if __name__ == "__main__":
    analyze_duplicate_positions()
    analyze_map_resolution()