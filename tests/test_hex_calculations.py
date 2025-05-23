import math

# For a regular hexagon with size (radius) = 30
hex_size = 30

# In a flat-top hex:
# - Width = 2 * size = 60
# - Height = sqrt(3) * size ≈ 51.96

# The distance between centers of adjacent hexes should be:
# - For neighbors sharing an edge: size * sqrt(3) ≈ 51.96
# - But with our column spacing of 1.5 * size = 45

# Let's calculate the actual geometry
print("Hex size:", hex_size)
print("Hex width:", 2 * hex_size)
print("Hex height:", math.sqrt(3) * hex_size)
print()

# For proper hex tessellation:
# Column spacing should be: 1.5 * size = 45
# Row spacing should be: sqrt(3) * size ≈ 51.96

# But this means diagonal neighbors won't be equidistant!
# Let's check actual distances:

# Center hex at (1, 1) using our layout
col_spacing = 1.5 * hex_size  # 45
row_spacing = math.sqrt(3) * hex_size  # 51.96
row_offset = 0.75 * hex_size  # 22.5

# Center position (odd row, so offset)
cx = 1 * col_spacing + row_offset  # 67.5
cy = 1 * row_spacing  # 51.96

print(f"Center hex (1,1) at ({cx:.2f}, {cy:.2f})")
print()

# East neighbor (2, 1)
nx = 2 * col_spacing + row_offset  # 112.5
ny = 1 * row_spacing  # 51.96
dist = math.sqrt((nx - cx)**2 + (ny - cy)**2)
print(f"East (2,1): distance = {dist:.2f}")

# Northeast neighbor (2, 0) for odd row
nx = 2 * col_spacing  # 90
ny = 0 * row_spacing  # 0
dist = math.sqrt((nx - cx)**2 + (ny - cy)**2)
print(f"Northeast (2,0): distance = {dist:.2f}")

# Northwest neighbor (1, 0) for odd row
nx = 1 * col_spacing  # 45
ny = 0 * row_spacing  # 0
dist = math.sqrt((nx - cx)**2 + (ny - cy)**2)
print(f"Northwest (1,0): distance = {dist:.2f}")

print()
print("For equidistant neighbors, all should be:", math.sqrt(3) * hex_size)