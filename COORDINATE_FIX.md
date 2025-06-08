# Coordinate System Fix Documentation

## The Problem

Cities were being placed with inverted Y coordinates:
- Spanish cities (Murcia, Córdoba) appeared in the NORTH of the map
- Norwegian cities (Trondheim, Oslo) appeared in the SOUTH of the map

## Root Cause

The OpenStreetMap tile coordinate system has **Y increasing southward**:
- North Pole: Y = 0
- Equator: Y = 2^(zoom-1)
- South Pole: Y = 2^zoom

This is opposite to typical geographic coordinates where Y increases northward.

## The Bug

In `tile_terrain_generator.py`, the bounds were incorrectly calculated:
```python
# WRONG - treated south as min Y, north as max Y
min_tile_x, min_tile_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
max_tile_x, max_tile_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
```

## The Fix

Correctly handle the inverted Y axis:
```python
# CORRECT - north gives MIN tile Y, south gives MAX tile Y
west_x, south_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
east_x, north_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)

min_tile_x = west_x
max_tile_x = east_x
min_tile_y = north_y  # North is MIN Y in tile coords
max_tile_y = south_y  # South is MAX Y in tile coords
```

## Verification

After the fix:
- Northern cities have **low Y values** (correct)
- Southern cities have **high Y values** (correct)
- East-west positioning remains correct

## Regenerating Maps

To regenerate your campaign map with correct city placement:

### Western Europe Focus (recommended for medieval gameplay):
```bash
python tools/tile_terrain_generator.py --bounds -10,36,20,60 --zoom 9 --hex-size-km 25 -o game/campaign/medieval_europe.json --save-image
```

### Full Europe (includes Russia):
```bash
python tools/tile_terrain_generator.py --bounds -15,35,40,65 --zoom 8 --hex-size-km 50 -o game/campaign/medieval_europe.json --save-image
```

### Mediterranean Focus:
```bash
python tools/tile_terrain_generator.py --bounds -10,30,35,50 --zoom 9 --hex-size-km 30 -o game/campaign/medieval_europe.json --save-image
```

The coordinate system now correctly places cities based on their actual geographic locations!