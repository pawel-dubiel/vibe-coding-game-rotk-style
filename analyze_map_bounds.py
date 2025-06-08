#!/usr/bin/env python3
"""
Analyze current map and suggest appropriate bounds for different regions
"""

import json
import os
import sys

def analyze_current_map():
    """Analyze the current medieval_europe.json to understand its geographic coverage"""
    map_file = 'game/campaign/medieval_europe.json'
    cities_file = 'medieval_cities_1200ad.json'
    
    if not os.path.exists(map_file):
        print(f"❌ {map_file} not found!")
        return
    
    if not os.path.exists(cities_file):
        print(f"❌ {cities_file} not found!")
        return
    
    # Load current map
    with open(map_file, 'r', encoding='utf-8') as f:
        map_data = json.load(f)
    
    # Load all cities
    with open(cities_file, 'r', encoding='utf-8') as f:
        all_cities_data = json.load(f)
    
    current_cities = map_data['cities']
    all_cities = {city['name'].lower().replace(' ', '_'): city for city in all_cities_data['cities']}
    
    print("🗺️  Current Map Analysis")
    print("=" * 50)
    print(f"Map dimensions: {map_data['map']['width']} × {map_data['map']['height']} hexes")
    print(f"Hex size: {map_data['map']['hex_size_km']} km")
    print(f"Cities on map: {len(current_cities)}")
    
    # Find extreme cities to estimate bounds
    print("\n📍 Extreme Cities (to estimate geographic coverage):")
    
    extreme_cities = {}
    for city_id, city_data in current_cities.items():
        if city_id in all_cities:
            original_city = all_cities[city_id]
            lat = original_city['latitude']
            lon = original_city['longitude']
            pos = city_data['position']
            
            # Track extremes
            if 'west' not in extreme_cities or lon < extreme_cities['west']['lon']:
                extreme_cities['west'] = {'name': city_data['name'], 'lat': lat, 'lon': lon, 'pos': pos}
            if 'east' not in extreme_cities or lon > extreme_cities['east']['lon']:
                extreme_cities['east'] = {'name': city_data['name'], 'lat': lat, 'lon': lon, 'pos': pos}
            if 'north' not in extreme_cities or lat > extreme_cities['north']['lat']:
                extreme_cities['north'] = {'name': city_data['name'], 'lat': lat, 'lon': lon, 'pos': pos}
            if 'south' not in extreme_cities or lat < extreme_cities['south']['lat']:
                extreme_cities['south'] = {'name': city_data['name'], 'lat': lat, 'lon': lon, 'pos': pos}
    
    for direction, data in extreme_cities.items():
        print(f"  {direction.upper()}: {data['name']} ({data['lat']:.2f}°, {data['lon']:.2f}°) at hex {data['pos']}")
    
    # Estimate bounds
    if extreme_cities:
        west_bound = extreme_cities['west']['lon'] - 2  # Add margin
        east_bound = extreme_cities['east']['lon'] + 2
        south_bound = extreme_cities['south']['lat'] - 2
        north_bound = extreme_cities['north']['lat'] + 2
        
        print(f"\n🎯 Estimated map bounds: {west_bound:.1f},{south_bound:.1f},{east_bound:.1f},{north_bound:.1f}")
        print(f"   Geographic coverage: {abs(east_bound - west_bound):.0f}° longitude × {abs(north_bound - south_bound):.0f}° latitude")
    
    # Check specific cities
    print("\n🏰 Key City Positions:")
    key_cities = ['paris', 'london', 'córdoba', 'murcia', 'roma', 'konstantinoupolis', 'kraków', 'moskva']
    
    for city_id in key_cities:
        if city_id in current_cities:
            city = current_cities[city_id]
            if city_id in all_cities:
                original = all_cities[city_id]
                print(f"  {city['name']}: hex {city['position']} (lat: {original['latitude']:.2f}°, lon: {original['longitude']:.2f}°)")
        else:
            if city_id in all_cities:
                original = all_cities[city_id]
                print(f"  {original['name']}: NOT ON MAP (lat: {original['latitude']:.2f}°, lon: {original['longitude']:.2f}°)")

def suggest_regional_bounds():
    """Suggest bounds for different regional focuses"""
    print("\n\n📐 Suggested Regional Bounds:")
    print("=" * 50)
    
    regions = {
        "Western Europe (France, Spain, Britain, Germany, Italy)": {
            "bounds": "-10,36,20,60",
            "description": "Focuses on the core of medieval Western Europe",
            "zoom": 9,
            "hex_size": 25
        },
        "Mediterranean (Spain, Italy, North Africa, Byzantium)": {
            "bounds": "-10,30,35,50",
            "description": "Centers on the Mediterranean world",
            "zoom": 9,
            "hex_size": 30
        },
        "Central Europe (Germany, Poland, Hungary, Bohemia)": {
            "bounds": "5,45,25,55",
            "description": "Holy Roman Empire and Eastern European kingdoms",
            "zoom": 10,
            "hex_size": 20
        },
        "Full Europe (Portugal to Russia)": {
            "bounds": "-15,35,40,65",
            "description": "Complete European coverage including Russia",
            "zoom": 8,
            "hex_size": 50
        },
        "Iberian Peninsula": {
            "bounds": "-10,36,4,44",
            "description": "Detailed view of Spain and Portugal",
            "zoom": 10,
            "hex_size": 15
        }
    }
    
    for region_name, config in regions.items():
        print(f"\n🌍 {region_name}")
        print(f"   Bounds: {config['bounds']}")
        print(f"   {config['description']}")
        print(f"   Command:")
        print(f"   python tools/tile_terrain_generator.py --bounds {config['bounds']} --zoom {config['zoom']} --hex-size-km {config['hex_size']} -o game/campaign/medieval_europe.json --save-image")

if __name__ == "__main__":
    analyze_current_map()
    suggest_regional_bounds()