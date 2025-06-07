# Tools

## OSM Terrain Generator

Generates accurate campaign maps using OpenStreetMap data.

### Usage

```bash
python osm_terrain_generator.py --bounds="west,south,east,north" --hex-size-km=30 -o output.json
```

### Europe + North Africa Coordinates

**Full Europe + North Africa:**
```bash
python osm_terrain_generator.py --bounds="-15,25,45,72" --hex-size-km=30 -o medieval_europe.json
```

**Real working example:**
```bash
cd /Users/pawel/work/game
python tools/osm_terrain_generator.py --bounds="-15,25,45,72" --hex-size-km=30 -o medieval_europe_full.json
```

**Result**: 148×174 hexes at exactly 29.9×30.1km per hex

**Central Europe (detailed):**
```bash
python osm_terrain_generator.py --bounds="-5,40,35,65" --hex-size-km=20 -o central_europe.json
```

**Mediterranean Basin:**
```bash
python osm_terrain_generator.py --bounds="-10,30,40,50" --hex-size-km=25 -o mediterranean.json
```

**Poland Only (may timeout - try smaller regions):**
```bash
python osm_terrain_generator.py --bounds="14,49,24,55" --hex-size-km=15 -o poland.json
```

**Warsaw Region (reliable OSM data):**
```bash
python osm_terrain_generator.py --bounds="20.8,52.1,21.2,52.3" --hex-size-km=5 -o warsaw.json
```

### Geographic Bounds Reference

**Europe + North Africa:**
- **West**: -15° (Atlantic coast)
- **East**: 45° (Ural Mountains, Black Sea)  
- **South**: 25° (North Africa - Morocco to Egypt)
- **North**: 72° (Northern Scandinavia)

**Poland:**
- **West**: 14° (Western border)
- **East**: 24° (Eastern border)
- **South**: 49° (Southern border)
- **North**: 55° (Baltic coast)

### Features

- **Accurate city placement** from `medieval_cities_1200ad.json` (179 cities)
- **Real terrain from OpenStreetMap** - water, forests, mountains, hills, desert, snow, plains  
- **Fails fast** - stops immediately if OSM API is unavailable (no fake terrain)
- **Exact hex size** - map dimensions auto-calculated to match requested km/hex
- **No manual steps** - just coordinates and run
- **Flexible override** - can force specific map dimensions if needed

### Important Notes

⚠️ **OSM API limitations** - Overpass API fails for large areas (country-scale)
💡 **For large regions** - use tile-based approach instead (see tile_terrain_generator.py)
🔄 **OSM API works** - for city/regional scale areas only

### Tile Terrain Generator (For Large Regions)

When OSM API fails for large areas, use the tile-based approach:

**Usage:**
```bash
python tools/tile_terrain_generator.py --bounds="west,south,east,north" --zoom=8 -o output.json
```

**Examples:**

**Poland (Country-scale):**
```bash
python tools/tile_terrain_generator.py --bounds="14,49,24,55" --zoom=8 -o poland_tiles.json
```

**Europe (Continental-scale):**
```bash
python tools/tile_terrain_generator.py --bounds="-15,35,45,70" --zoom=6 -o europe_tiles.json
```

**Parameters:**
- `--bounds`: Geographic bounds as "west,south,east,north"
- `--zoom`: Map zoom level (6-10 recommended, higher = more detail)
- `-o`: Output JSON file

**How it works:**
1. Downloads map tiles from OpenStreetMap tile servers
2. Stitches tiles together into one large image
3. Analyzes pixel colors to classify terrain (water, forest, mountains, etc.)
4. Generates hex-based terrain map with accurate coastlines

**Advantages:**
- ✅ **No size limits** - works for any area size
- ✅ **No API timeouts** - tile servers are fast and reliable
- ✅ **Visual accuracy** - uses actual rendered map data
- ✅ **Real coastlines** - Baltic Sea, Mediterranean, etc.

### Terrain Generated

- ✅ **Baltic Sea** - Gdansk now correctly on coast
- ✅ **Mediterranean Sea** - accurate water placement
- ✅ **Major mountain ranges** - Alps, Pyrenees, Carpathians
- ✅ **Forest regions** - Scandinavia, Central Europe, Russia  
- ✅ **Desert** - North Africa (Sahara)
- ✅ **Atlantic/North Sea** coastlines