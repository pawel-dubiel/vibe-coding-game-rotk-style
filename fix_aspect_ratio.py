#!/usr/bin/env python3
"""
Compare different approaches to fix the aspect ratio issue
"""

import math

def compare_approaches():
    """Compare different ways to calculate hex grid dimensions"""
    
    # Your bounds: --bounds="-15,35,45,70"
    west_lon = -15
    east_lon = 45
    south_lat = 35
    north_lat = 70
    hex_size_km = 20
    zoom = 6
    
    print("🔧 Comparing Different Hex Grid Calculation Approaches")
    print("=" * 60)
    
    # 1. ORIGINAL approach (lat/lon based)
    center_lat = (north_lat + south_lat) / 2
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    
    total_width_km = (east_lon - west_lon) * km_per_deg_lon
    total_height_km = (north_lat - south_lat) * km_per_deg_lat
    
    hex_width_original = int(round(total_width_km / hex_size_km))
    hex_height_original = int(round(total_height_km / hex_size_km))
    
    print(f"\n1️⃣ ORIGINAL approach (geographic km):")
    print(f"   Real distances: {total_width_km:.0f} × {total_height_km:.0f} km")
    print(f"   Hex grid: {hex_width_original} × {hex_height_original}")
    print(f"   Total hexes: {hex_width_original * hex_height_original:,}")
    
    # 2. IMAGE ASPECT approach (current broken one)
    # Tile grid is 12×12 (square)
    tiles_x = 12
    tiles_y = 12
    img_width = tiles_x * 256
    img_height = tiles_y * 256
    image_aspect_ratio = img_height / img_width  # This is 1.0!
    
    hex_width_image = hex_width_original  # 203
    hex_height_image = int(round(hex_width_image * image_aspect_ratio))  # 203!
    
    print(f"\n2️⃣ IMAGE ASPECT approach (current):")
    print(f"   Image: {img_width} × {img_height} pixels (aspect: {image_aspect_ratio:.3f})")
    print(f"   Hex grid: {hex_width_image} × {hex_height_image}")
    print(f"   Total hexes: {hex_width_image * hex_height_image:,}")
    print(f"   ⚠️  Problem: Forces square grid due to Mercator!")
    
    # 3. FIXED approach - use geographic aspect ratio
    geographic_aspect = total_height_km / total_width_km
    hex_width_fixed = hex_width_original
    hex_height_fixed = int(round(hex_width_fixed * geographic_aspect))
    
    print(f"\n3️⃣ GEOGRAPHIC ASPECT approach (proposed fix):")
    print(f"   Geographic aspect: {geographic_aspect:.3f}")
    print(f"   Hex grid: {hex_width_fixed} × {hex_height_fixed}")
    print(f"   Total hexes: {hex_width_fixed * hex_height_fixed:,}")
    
    # 4. PIXEL-PERFECT approach - match exact tile boundaries
    # Calculate fractional tile positions
    n = 2.0 ** zoom
    
    # Fractional tile positions
    west_tile_x = (west_lon + 180.0) / 360.0 * n
    east_tile_x = (east_lon + 180.0) / 360.0 * n
    
    def lat_to_tile_y_float(lat):
        lat_rad = math.radians(lat)
        return (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    
    north_tile_y = lat_to_tile_y_float(north_lat)
    south_tile_y = lat_to_tile_y_float(south_lat)
    
    # Exact tile spans
    exact_tiles_x = east_tile_x - west_tile_x
    exact_tiles_y = south_tile_y - north_tile_y
    
    # Use exact spans for aspect ratio
    exact_aspect = exact_tiles_y / exact_tiles_x
    hex_width_exact = hex_width_original
    hex_height_exact = int(round(hex_width_exact * exact_aspect))
    
    print(f"\n4️⃣ EXACT TILE approach (most accurate):")
    print(f"   Exact tile spans: {exact_tiles_x:.3f} × {exact_tiles_y:.3f}")
    print(f"   Exact aspect: {exact_aspect:.3f}")
    print(f"   Hex grid: {hex_width_exact} × {hex_height_exact}")
    print(f"   Total hexes: {hex_width_exact * hex_height_exact:,}")
    
    # Show the differences
    print(f"\n📊 Comparison Summary:")
    print(f"   Original:        {hex_width_original} × {hex_height_original}")
    print(f"   Image (broken):  {hex_width_image} × {hex_height_image} ❌")
    print(f"   Geographic fix:  {hex_width_fixed} × {hex_height_fixed} ✓")
    print(f"   Exact tile fix:  {hex_width_exact} × {hex_height_exact} ✓✓")
    
    print(f"\n💡 Recommendation:")
    print(f"   Use approach #4 (exact tile spans) for most accurate mapping")
    print(f"   This accounts for Mercator projection properly")

if __name__ == "__main__":
    compare_approaches()