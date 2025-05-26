#!/usr/bin/env python3
"""Test terrain coordinate transformation"""

import sys
sys.path.append('.')

from game.hex_layout import HexLayout
from game.terrain import TerrainMap, TerrainType

# Create a small test map
width, height = 10, 10
terrain_map = TerrainMap(width, height, use_legacy_generation=True)
hex_layout = HexLayout(hex_size=36, orientation='flat')

# Set specific terrain at known positions for testing
terrain_map.set_terrain(0, 0, TerrainType.WATER)
terrain_map.set_terrain(5, 5, TerrainType.FOREST)
terrain_map.set_terrain(9, 9, TerrainType.HILLS)

print("Terrain grid setup:")
print(f"(0,0) = {terrain_map.get_terrain(0, 0).type.value}")
print(f"(5,5) = {terrain_map.get_terrain(5, 5).type.value}")
print(f"(9,9) = {terrain_map.get_terrain(9, 9).type.value}")
print()

# Test hex_to_pixel and pixel_to_hex round trip
print("Testing coordinate transformations:")
for test_col, test_row in [(0, 0), (5, 5), (9, 9)]:
    # Convert to pixel
    pixel_x, pixel_y = hex_layout.hex_to_pixel(test_col, test_row)
    print(f"\nHex ({test_col},{test_row}) -> Pixel ({pixel_x:.2f},{pixel_y:.2f})")
    
    # Convert back to hex
    result_col, result_row = hex_layout.pixel_to_hex(pixel_x, pixel_y)
    print(f"Pixel ({pixel_x:.2f},{pixel_y:.2f}) -> Hex ({result_col},{result_row})")
    
    # Check if round trip is correct
    if result_col == test_col and result_row == test_row:
        print("✓ Round trip successful")
    else:
        print(f"✗ Round trip failed! Expected ({test_col},{test_row}), got ({result_col},{result_row})")
    
    # Get terrain at converted position
    terrain = terrain_map.get_terrain(result_col, result_row)
    if terrain:
        print(f"Terrain at ({result_col},{result_row}): {terrain.type.value}")
    else:
        print(f"No terrain at ({result_col},{result_row})")

# Test some offset positions (like clicking slightly off-center)
print("\n\nTesting offset clicks:")
for test_col, test_row in [(5, 5)]:
    pixel_x, pixel_y = hex_layout.hex_to_pixel(test_col, test_row)
    
    # Test clicking at various offsets
    offsets = [(0, 0), (10, 0), (-10, 0), (0, 10), (0, -10)]
    for dx, dy in offsets:
        click_x = pixel_x + dx
        click_y = pixel_y + dy
        result_col, result_row = hex_layout.pixel_to_hex(click_x, click_y)
        print(f"Click at ({click_x:.1f},{click_y:.1f}) -> Hex ({result_col},{result_row})")