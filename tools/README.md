# Tools

## Campaign Map Generation

### Quick Start

**Generate all predefined maps:**
```bash
python tools/generate_campaign_maps.py
```

**Generate specific maps:**
```bash
python tools/generate_campaign_maps.py --map "British Isles 20km" --map "Western Europe 20km"
```

**See available maps:**
```bash
python tools/generate_campaign_maps.py --list
```

**Generate single map manually:**
```bash
python tools/tile_terrain_generator.py --bounds=14,49,24,55 --hex-size-km 30 --zoom 8
```

**Generate all maps from definitions (no arguments):**
```bash
python tools/tile_terrain_generator.py
```

**List available map definitions:**
```bash
python tools/tile_terrain_generator.py --list-maps
```

### Campaign Map Generator

The `generate_campaign_maps.py` tool automatically generates multiple campaign maps based on predefined regions in `map_definitions.json`.

**Available Predefined Maps:**
- **Europe 30km** - Full Europe at 30km per hex resolution
- **Europe 50km** - Full Europe at 50km per hex resolution  
- **Central Europe + Baltic 25km** - Central Europe including Baltic region
- **Western Europe 20km** - France, England, Low Countries at high detail
- **Eastern Europe 30km** - Poland, Hungary, Balkans
- **Mediterranean 35km** - Mediterranean basin including North Africa
- **Holy Roman Empire 15km** - High detail map of HRE region
- **British Isles 20km** - England, Scotland, Ireland, Wales
- **Iberian Peninsula 25km** - Spain and Portugal
- **Scandinavia 40km** - Nordic countries

**Features:**
- ✅ **Real-time progress** - shows tile fetching and processing progress
- ✅ **Automatic naming** - generates descriptive filenames with bounds and dimensions
- ✅ **Respectful delays** - 2-second delays between maps to respect tile servers
- ✅ **Error handling** - continues with remaining maps if one fails
- ✅ **Dry run mode** - see what would be generated without actually generating

### Tile Terrain Generator (Core Engine)

The underlying engine that powers map generation:

**Usage:**
```bash
# Manual bounds (use = for negative coordinates)
python tools/tile_terrain_generator.py --bounds=-15,35,45,70 --hex-size-km 50 --zoom 6

# Generate all predefined maps
python tools/tile_terrain_generator.py

# List available map definitions
python tools/tile_terrain_generator.py --list-maps
```

**Parameters:**
- `--bounds`: Geographic bounds as "west,south,east,north" (use `--bounds=-10,35,40,70` for negative coordinates)
- `--hex-size-km`: Target hex size in kilometers (default: 30)
- `--zoom`: Map zoom level (6-10 recommended, higher = more detail, default: 10)
- `-o`: Output JSON file (auto-generated if not specified)
- `--save-image`: Save the combined tile image for inspection
- `--list-maps`: List available map definitions and exit

**How it works:**
1. Downloads map tiles from OpenStreetMap tile servers
2. Stitches tiles together into one large image
3. Analyzes pixel colors to classify terrain (water, forest, mountains, etc.)
4. Places historical cities from `medieval_cities_1200ad.json`
5. Generates hex-based terrain map with accurate coastlines
6. Saves to `/game/campaign/data/` with descriptive filename

**Advantages:**
- ✅ **No size limits** - works for any area size
- ✅ **No API timeouts** - tile servers are fast and reliable
- ✅ **Visual accuracy** - uses actual rendered map data
- ✅ **Real coastlines** - Baltic Sea, Mediterranean, etc.
- ✅ **Historical cities** - 179 medieval cities with correct positioning
- ✅ **Game integration** - maps appear automatically in campaign selection

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

**Note:** For negative coordinates, use the equals syntax: `--bounds=-10,35,40,70`

### Terrain Generated

- ✅ **Baltic Sea** - Gdansk now correctly on coast
- ✅ **Mediterranean Sea** - accurate water placement
- ✅ **Major mountain ranges** - Alps, Pyrenees, Carpathians
- ✅ **Forest regions** - Scandinavia, Central Europe, Russia  
- ✅ **Desert** - North Africa (Sahara)
- ✅ **Atlantic/North Sea** coastlines