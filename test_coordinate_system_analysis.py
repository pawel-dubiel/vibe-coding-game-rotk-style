#!/usr/bin/env python3
"""
Comprehensive coordinate system analysis for multiple cities
"""

import math
import json
import os

# Load cities and campaign data
def load_data():
    """Load cities and campaign data"""
    # Load cities database
    with open('/Users/pawel/work/game/medieval_cities_1200ad.json', 'r') as f:
        cities_data = json.load(f)
    
    # Load campaign map
    with open('/Users/pawel/work/game/campaign/medieval_europe.json', 'r') as f:
        campaign_data = json.load(f)
    
    return cities_data['cities'], campaign_data

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

def reverse_engineer_bounds(cities_data: list, campaign_data: dict, zoom: int = 10):
    """Try to reverse engineer the bounds used for generation"""
    print("🔍 Reverse engineering map bounds from city placements")
    
    map_width = campaign_data['map']['width']
    map_height = campaign_data['map']['height']
    campaign_cities = campaign_data['cities']
    
    # Collect city coordinate pairs
    coord_pairs = []
    
    for city in cities_data:
        city_id = city['name'].lower().replace(' ', '_').replace('-', '_')
        if city_id in campaign_cities:
            lat = city['latitude']
            lon = city['longitude']
            hex_x, hex_y = campaign_cities[city_id]['position']
            
            coord_pairs.append({
                'name': city['name'],
                'lat': lat,
                'lon': lon,
                'hex_x': hex_x,
                'hex_y': hex_y,
                'rel_x': hex_x / map_width,
                'rel_y': hex_y / map_height
            })
    
    print(f"Found {len(coord_pairs)} cities with coordinate data")
    
    # Analyze geographic extents
    if coord_pairs:
        min_lat = min(city['lat'] for city in coord_pairs)
        max_lat = max(city['lat'] for city in coord_pairs)
        min_lon = min(city['lon'] for city in coord_pairs)
        max_lon = max(city['lon'] for city in coord_pairs)
        
        print(f"\n📍 Geographic extent of placed cities:")
        print(f"   Latitude: {min_lat:.2f}° to {max_lat:.2f}°")
        print(f"   Longitude: {min_lon:.2f}° to {max_lon:.2f}°")
        
        # Analyze hex extents
        min_hex_x = min(city['hex_x'] for city in coord_pairs)
        max_hex_x = max(city['hex_x'] for city in coord_pairs)
        min_hex_y = min(city['hex_y'] for city in coord_pairs)
        max_hex_y = max(city['hex_y'] for city in coord_pairs)
        
        print(f"\n🗺️  Hex extent of placed cities:")
        print(f"   X: {min_hex_x} to {max_hex_x} (of {map_width})")
        print(f"   Y: {min_hex_y} to {max_hex_y} (of {map_height})")
        
        # Try to infer bounds by finding cities at extremes
        # Find corner cities
        sw_city = min(coord_pairs, key=lambda c: c['lat'] + c['lon'])  # Southwest
        ne_city = max(coord_pairs, key=lambda c: c['lat'] + c['lon'])  # Northeast
        nw_city = max(coord_pairs, key=lambda c: c['lat'] - c['lon'])  # Northwest  
        se_city = min(coord_pairs, key=lambda c: c['lat'] - c['lon'])  # Southeast
        
        print(f"\n🧭 Corner cities:")
        print(f"   SW: {sw_city['name']} ({sw_city['lat']:.2f}, {sw_city['lon']:.2f}) -> hex ({sw_city['hex_x']}, {sw_city['hex_y']})")
        print(f"   NE: {ne_city['name']} ({ne_city['lat']:.2f}, {ne_city['lon']:.2f}) -> hex ({ne_city['hex_x']}, {ne_city['hex_y']})")
        print(f"   NW: {nw_city['name']} ({nw_city['lat']:.2f}, {nw_city['lon']:.2f}) -> hex ({nw_city['hex_x']}, {nw_city['hex_y']})")
        print(f"   SE: {se_city['name']} ({se_city['lat']:.2f}, {se_city['lon']:.2f}) -> hex ({se_city['hex_x']}, {se_city['hex_y']})")
    
    return coord_pairs

def test_bounds_hypothesis(coord_pairs: list, test_bounds: dict, zoom: int = 10):
    """Test a bounds hypothesis against all city placements"""
    map_width = 81
    map_height = 78
    
    def get_tile_bounds_web_mercator(bounds: dict, zoom: int):
        west_merc, south_merc = lat_lon_to_web_mercator(bounds['south_lat'], bounds['west_lon'])
        east_merc, north_merc = lat_lon_to_web_mercator(bounds['north_lat'], bounds['east_lon'])
        
        min_tile_x, max_tile_y = web_mercator_to_tile_coords(west_merc, south_merc, zoom)
        max_tile_x, min_tile_y = web_mercator_to_tile_coords(east_merc, north_merc, zoom)
        
        return min_tile_x, min_tile_y, max_tile_x, max_tile_y
    
    def convert_to_hex(lat: float, lon: float):
        city_x_merc, city_y_merc = lat_lon_to_web_mercator(lat, lon)
        city_tile_x, city_tile_y = web_mercator_to_tile_coords(city_x_merc, city_y_merc, zoom)
        
        min_tile_x, min_tile_y, max_tile_x, max_tile_y = get_tile_bounds_web_mercator(test_bounds, zoom)
        
        hex_x = int((city_tile_x - min_tile_x) / (max_tile_x - min_tile_x) * map_width)
        hex_y = int((city_tile_y - min_tile_y) / (max_tile_y - min_tile_y) * map_height)
        
        hex_x = max(0, min(hex_x, map_width - 1))
        hex_y = max(0, min(hex_y, map_height - 1))
        
        return hex_x, hex_y
    
    total_error = 0
    results = []
    
    for city in coord_pairs:
        predicted_x, predicted_y = convert_to_hex(city['lat'], city['lon'])
        actual_x, actual_y = city['hex_x'], city['hex_y']
        
        error_x = abs(predicted_x - actual_x)
        error_y = abs(predicted_y - actual_y)
        total_error_city = error_x + error_y
        total_error += total_error_city
        
        results.append({
            'name': city['name'],
            'predicted': (predicted_x, predicted_y),
            'actual': (actual_x, actual_y),
            'error': (error_x, error_y),
            'total_error': total_error_city
        })
    
    avg_error = total_error / len(coord_pairs) if coord_pairs else 0
    
    return results, avg_error, total_error

def find_best_bounds(coord_pairs: list):
    """Try different bounds to find the best fit"""
    print("\n🎯 Testing different bounds to find best fit")
    
    bounds_to_test = [
        {'name': 'Wide Europe', 'west_lon': -10.0, 'east_lon': 30.0, 'south_lat': 35.0, 'north_lat': 60.0},
        {'name': 'Central Europe', 'west_lon': -5.0, 'east_lon': 25.0, 'south_lat': 40.0, 'north_lat': 55.0},
        {'name': 'Extended Europe', 'west_lon': -15.0, 'east_lon': 35.0, 'south_lat': 30.0, 'north_lat': 65.0},
        {'name': 'Western Focus', 'west_lon': -10.0, 'east_lon': 20.0, 'south_lat': 35.0, 'north_lat': 60.0},
        {'name': 'Atlantic Europe', 'west_lon': -12.0, 'east_lon': 28.0, 'south_lat': 36.0, 'north_lat': 62.0},
        {'name': 'Narrow Europe', 'west_lon': -8.0, 'east_lon': 32.0, 'south_lat': 38.0, 'north_lat': 58.0},
    ]
    
    best_bounds = None
    best_error = float('inf')
    
    for bounds in bounds_to_test:
        results, avg_error, total_error = test_bounds_hypothesis(coord_pairs, bounds)
        
        print(f"\n--- {bounds['name']} ---")
        print(f"Bounds: {bounds['west_lon']:.1f}°W to {bounds['east_lon']:.1f}°E, {bounds['south_lat']:.1f}°S to {bounds['north_lat']:.1f}°N")
        print(f"Average error: {avg_error:.2f} hexes")
        print(f"Total error: {total_error} hexes")
        
        # Show worst mismatches
        worst_cities = sorted(results, key=lambda x: x['total_error'], reverse=True)[:3]
        print("Worst matches:")
        for city in worst_cities:
            print(f"   {city['name']}: predicted {city['predicted']} vs actual {city['actual']} (error: {city['total_error']})")
        
        if avg_error < best_error:
            best_error = avg_error
            best_bounds = bounds
    
    print(f"\n🏆 Best bounds: {best_bounds['name']} with average error {best_error:.2f} hexes")
    return best_bounds

def analyze_coordinate_patterns(coord_pairs: list):
    """Look for systematic patterns in coordinate transformations"""
    print("\n🔍 Analyzing coordinate transformation patterns")
    
    # Extract coordinates
    lats = [city['lat'] for city in coord_pairs]
    lons = [city['lon'] for city in coord_pairs]
    hex_xs = [city['hex_x'] for city in coord_pairs]
    hex_ys = [city['hex_y'] for city in coord_pairs]
    
    # Calculate basic statistics
    print(f"\n📊 Coordinate statistics:")
    print(f"   Latitude range: {min(lats):.2f}° to {max(lats):.2f}° (span: {max(lats)-min(lats):.2f}°)")
    print(f"   Longitude range: {min(lons):.2f}° to {max(lons):.2f}° (span: {max(lons)-min(lons):.2f}°)")
    print(f"   Hex X range: {min(hex_xs)} to {max(hex_xs)} (span: {max(hex_xs)-min(hex_xs)})")
    print(f"   Hex Y range: {min(hex_ys)} to {max(hex_ys)} (span: {max(hex_ys)-min(hex_ys)})")
    
    # Simple correlation calculation
    def correlation(x_vals, y_vals):
        n = len(x_vals)
        if n == 0:
            return 0
        
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x2 = sum(x * x for x in x_vals)
        sum_y2 = sum(y * y for y in y_vals)
        
        num = n * sum_xy - sum_x * sum_y
        den = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        return num / den if den != 0 else 0
    
    # Check latitude vs hex_y correlation (should be inversely correlated if Y increases southward)
    lat_hex_y_corr = correlation(lats, hex_ys)
    lon_hex_x_corr = correlation(lons, hex_xs)
    
    print(f"\n🔗 Correlations:")
    print(f"   Latitude vs Hex Y: {lat_hex_y_corr:.3f}")
    print(f"   Longitude vs Hex X: {lon_hex_x_corr:.3f}")
    
    if lat_hex_y_corr < -0.8:
        print("   ✅ Strong negative correlation: Y increases southward (normal)")
    elif lat_hex_y_corr > 0.8:
        print("   ⚠️  Strong positive correlation: Y increases northward (reversed)")
    else:
        print("   ❓ Weak correlation: coordinate system unclear")
    
    if lon_hex_x_corr > 0.8:
        print("   ✅ Strong positive correlation: X increases eastward (normal)")
    elif lon_hex_x_corr < -0.8:
        print("   ⚠️  Strong negative correlation: X increases westward (reversed)")
    else:
        print("   ❓ Weak correlation: coordinate system unclear")

def main():
    print("🗺️  Comprehensive Coordinate System Analysis")
    print("=" * 50)
    
    # Load data
    cities_data, campaign_data = load_data()
    
    # Reverse engineer bounds from city placements
    coord_pairs = reverse_engineer_bounds(cities_data, campaign_data)
    
    if not coord_pairs:
        print("❌ No coordinate pairs found")
        return
    
    # Analyze patterns
    analyze_coordinate_patterns(coord_pairs)
    
    # Find best bounds
    best_bounds = find_best_bounds(coord_pairs)
    
    # Test the best bounds in detail
    if best_bounds:
        print(f"\n🔬 Detailed analysis of best bounds: {best_bounds['name']}")
        results, avg_error, total_error = test_bounds_hypothesis(coord_pairs, best_bounds)
        
        print(f"\nAll city mappings:")
        for result in sorted(results, key=lambda x: x['total_error'], reverse=True):
            print(f"   {result['name']:20} {result['predicted']} -> {result['actual']} (error: {result['total_error']})")

if __name__ == "__main__":
    main()