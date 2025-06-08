#!/usr/bin/env python3
"""
Analyze why the map ends up square when bounds aren't square
"""

import math

def analyze_aspect_ratio():
    """Analyze the aspect ratio issue"""
    
    # Your bounds: --bounds="-15,35,45,70"
    west_lon = -15
    east_lon = 45
    south_lat = 35
    north_lat = 70
    
    print("🗺️  Analyzing Map Aspect Ratio Problem")
    print("=" * 60)
    
    # Geographic dimensions
    width_degrees = east_lon - west_lon  # 60°
    height_degrees = north_lat - south_lat  # 35°
    
    print(f"\n📐 Geographic bounds:")
    print(f"   Width:  {width_degrees}° longitude")
    print(f"   Height: {height_degrees}° latitude")
    print(f"   Aspect ratio: {width_degrees/height_degrees:.2f} (width/height)")
    
    # Real-world distances at center latitude
    center_lat = (north_lat + south_lat) / 2  # 52.5°
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    
    width_km = width_degrees * km_per_deg_lon
    height_km = height_degrees * km_per_deg_lat
    
    print(f"\n🌍 Real-world distances at {center_lat}°N:")
    print(f"   Width:  {width_km:.0f} km")
    print(f"   Height: {height_km:.0f} km")
    print(f"   Aspect ratio: {width_km/height_km:.2f}")
    
    # With 20km hex size
    hex_size_km = 20
    expected_hex_width = int(round(width_km / hex_size_km))
    expected_hex_height = int(round(height_km / hex_size_km))
    
    print(f"\n🔷 Expected hex grid (20km hexes):")
    print(f"   Width:  {expected_hex_width} hexes")
    print(f"   Height: {expected_hex_height} hexes")
    print(f"   Aspect ratio: {expected_hex_width/expected_hex_height:.2f}")
    
    # Web Mercator tile calculation at zoom 6
    zoom = 6
    n = 2.0 ** zoom
    
    # Tile X calculation (longitude)
    min_tile_x = int((west_lon + 180.0) / 360.0 * n)
    max_tile_x = int((east_lon + 180.0) / 360.0 * n)
    
    # Tile Y calculation (latitude) - uses Mercator projection
    def lat_to_tile_y(lat):
        lat_rad = math.radians(lat)
        return int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    
    min_tile_y = lat_to_tile_y(north_lat)  # North is MIN in tile coords
    max_tile_y = lat_to_tile_y(south_lat)  # South is MAX in tile coords
    
    tiles_x = max_tile_x - min_tile_x + 1
    tiles_y = max_tile_y - min_tile_y + 1
    
    print(f"\n🗺️  Web Mercator tiles (zoom {zoom}):")
    print(f"   Tile X range: {min_tile_x} to {max_tile_x} = {tiles_x} tiles")
    print(f"   Tile Y range: {min_tile_y} to {max_tile_y} = {tiles_y} tiles")
    print(f"   Tile grid: {tiles_x} × {tiles_y}")
    print(f"   Image would be: {tiles_x * 256} × {tiles_y * 256} pixels")
    
    # The problem!
    if tiles_x == tiles_y:
        print(f"\n⚠️  PROBLEM IDENTIFIED!")
        print(f"   Tile grid is SQUARE ({tiles_x}×{tiles_y}) even though:")
        print(f"   - Geographic bounds are NOT square (60° × 35°)")
        print(f"   - Real-world area is NOT square ({width_km:.0f}km × {height_km:.0f}km)")
        print(f"\n   This happens because Web Mercator stretches latitude!")
    
    # Show the Mercator stretching
    print(f"\n🔍 Mercator projection analysis:")
    
    # Calculate Y positions for different latitudes
    lats = [35, 40, 45, 50, 55, 60, 65, 70]
    print(f"   Latitude -> Tile Y mapping:")
    for lat in lats:
        tile_y = lat_to_tile_y(lat)
        print(f"   {lat}°N -> tile Y = {tile_y}")
    
    # Show the stretching factor
    mercator_height = max_tile_y - min_tile_y
    geographic_height = height_degrees
    stretch_factor = mercator_height / geographic_height
    
    print(f"\n   Mercator stretches {height_degrees}° of latitude")
    print(f"   into {mercator_height} tile units")
    print(f"   Average stretch: {stretch_factor:.2f} tile units per degree")

if __name__ == "__main__":
    analyze_aspect_ratio()