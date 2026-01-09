# Medieval Hex Strategy Game

A comprehensive turn-based strategy game featuring medieval combat on hexagonal grids, with both tactical battles and grand campaign modes. Experience historically accurate medieval Europe with real-world terrain, authentic city positioning, and strategic depth.

## Features

### Core Gameplay
- **Hexagonal Grid System**: Tactical movement and positioning on a hex-based battlefield
- **Turn-Based Combat**: Strategic combat with action points (AP) system
- **Multiple Unit Types**: Warriors, Archers, Cavalry, and Mages - each with unique abilities
- **Castle Sieges**: Attack and defend castles with garrison mechanics

### Tactical Systems
- **Action Points (AP)**: Units have limited actions per turn based on their class
- **Facing & Flanking**: Unit orientation matters - rear and flank attacks deal bonus damage
- **Line of Sight**: Realistic vision mechanics with terrain blocking
- **Fog of War**: Explore the battlefield with limited visibility
- **Zone of Control (ZOC)**: Enemy units restrict movement in adjacent hexes

### Terrain System
- **15 Terrain Types**: From plains and forests to mountains and deep water
- **Terrain Features**: Rivers, roads, bridges, villages, and fortifications
- **Movement Costs**: Different terrains affect movement speed
- **Height Advantage**: Units on hills gain combat bonuses for ranged attacks
- **Real-World Maps**: Generate campaign maps from OpenStreetMap data
- **Historical Cities**: 179 medieval cities with accurate positioning

### Special Abilities
- **Cavalry Charges**: Devastating charges that can push enemies back
- **Breakaway Mechanics**: Attempt to disengage from combat
- **General System**: Leaders provide passive bonuses and active abilities
- **Morale System**: Units can rout when taking heavy casualties

### Game Modes
- **Campaign Mode**: Grand strategy with historical maps and medieval cities
- **Battle Mode**: Custom battles with configurable settings
- **Test Scenarios**: Pre-configured scenarios for testing mechanics
- **Map Editor**: Create and edit custom maps
- **Multiplayer**: Hot-seat multiplayer support
- **AI Opponents**: Computer-controlled enemies

## Installation

### Requirements
- Python 3.10+
- Pygame 2.6+
- Pillow (PIL) - for map tile processing
- Internet connection - for downloading OpenStreetMap tiles

### Setup
```bash
# Clone the repository
git clone [repository-url]
cd game

# Create virtual environment
python -m venv env

# Activate virtual environment
# On macOS/Linux:
source env/bin/activate
# On Windows:
env\Scripts\activate

# Install dependencies
pip install pygame pillow
```

### Installation / Deployment

For the game to import the module, the compiled shared object file must be in the Python path (e.g., the root directory or the `game/` directory).

If you are distributing this game or setting it up on a new machine, **you must recompile the extension**. The compiled binary is specific to the Operating System, Processor Architecture, and Python version.

## Performance & Optimizations

This project includes high-performance C extensions for critical algorithms (like Pathfinding) that provide a **20x-30x speedup** over pure Python.

### C Extensions
- **Algorithms**: Optimized A* Pathfinding and Hex Math.
- **Toggle**: Use `game/config.py` to enable/disable (`USE_C_EXTENSIONS = True`).
- **Compilation**: Requires a C compiler and Python development headers.

For detailed build instructions and troubleshooting, see [**c_modules/README.md**](c_modules/README.md).

## Running the Game

```bash
python main.py
```

### Campaign Mode
Experience medieval Europe with historically accurate maps and cities:

1. **Select Campaign** from the main menu
2. **Choose a Map** from generated regional maps:
   - Europe (30km or 50km per hex)
   - Western Europe (20km per hex) 
   - Eastern Europe (30km per hex)
   - British Isles (20km per hex)
   - Holy Roman Empire (15km per hex)
   - And more...
3. **Select a Country** to play (Holy Roman Empire, France, England, Poland, etc.)
4. **Manage armies** and conquer territories across authentic medieval landscapes

### Generate Campaign Maps

**Quick generation of all predefined maps:**
```bash
python tools/generate_campaign_maps.py
```

**See available maps:**
```bash
python tools/generate_campaign_maps.py --list
```

**Generate custom regions:**
```bash
python tools/tile_terrain_generator.py --bounds=14,49,24,55 --hex-size-km 30
```

See `/tools/README.md` for detailed map generation guide.

### Command Line Options
- `--mode [battle|menu]`: Start in specific mode
- `--board-size WxH`: Set board dimensions (e.g., 20x15)
- `--player1 [human|ai]`: Set player 1 type
- `--player2 [human|ai]`: Set player 2 type

## Controls

### Mouse Controls
- **Left Click**: Select unit, move to location, or attack
- **Right Click**: Open context menu, view unit/terrain info
- **Scroll**: Move camera around the battlefield

### Keyboard Shortcuts
- **Space**: End turn
- **R**: Rotate selected unit
- **C**: Center camera on selected unit
- **ESC**: Cancel current action
- **Tab**: Cycle through your units

### Camera Controls
- **Arrow Keys**: Pan camera
- **W/A/S/D**: Alternative camera panning

## Game Mechanics

### Action Points (AP)
Each unit class has different AP pools:
- **Warriors**: 8 AP (high health, strong melee)
- **Archers**: 7 AP (ranged attacks, weak in melee)
- **Cavalry**: 10 AP (fast movement, devastating charges)
- **Mages**: 6 AP (powerful attacks, fragile)

### Combat Calculations
- Base damage depends on unit type and soldier count
- Terrain provides defensive bonuses
- Facing affects damage (rear: 200%, flank: 150%, front: 100%)
- Morale affects combat effectiveness

### Victory Conditions
- Eliminate all enemy units
- Capture enemy castles
- Custom objectives in scenario mode

## Project Structure

```
game/
├── main.py                     # Entry point
├── map_definitions.json        # Predefined map regions
├── game/
│   ├── game_state.py          # Core game state management
│   ├── renderer.py            # Visual rendering
│   ├── input_handler.py       # Input processing
│   ├── hex_utils.py           # Hexagonal grid utilities
│   ├── terrain.py             # Terrain system
│   ├── visibility.py          # Fog of war implementation
│   ├── pathfinding.py         # Movement algorithms
│   ├── campaign/              # Campaign mode
│   │   ├── campaign_state.py  # Campaign game state
│   │   ├── campaign_renderer.py # Campaign map rendering
│   │   └── data/              # Generated campaign maps
│   ├── entities/              # Units and buildings
│   ├── behaviors/             # Unit behaviors (movement, combat, etc.)
│   ├── components/            # Unit components (stats, facing, generals)
│   ├── ui/                    # User interface elements
│   │   ├── campaign_screen.py      # Campaign UI
│   │   ├── campaign_map_select.py  # Map selection UI
│   │   ├── country_selection.py    # Country selection UI
│   │   └── ...                     # Other UI screens
│   └── ai/                    # AI implementation
├── tools/                     # Map generation tools
│   ├── generate_campaign_maps.py   # Batch map generator
│   ├── tile_terrain_generator.py   # Core map generation
│   └── README.md                   # Tool documentation
├── medieval_cities_1200ad.json    # Historical city database
└── tests/                     # Unit tests
```

## Development

### Running Tests
```bash
python -m pytest
```

### Architecture
The game uses a component-based architecture:
- **Entities**: Units and buildings
- **Behaviors**: Pluggable actions (move, attack, special abilities)
- **Components**: Data containers (stats, facing, generals)

### Key Systems
- **Hex Grid**: Axial coordinate system for efficient hex operations
- **Pathfinding**: A* and Dijkstra algorithms for movement
- **Vision System**: Line-of-sight calculations with terrain blocking
- **Combat Resolution**: Deterministic combat with morale effects
- **Map Generation**: Real-world terrain from OpenStreetMap tile data
- **Historical Data**: Medieval cities with accurate positioning and statistics

## Contributing

Please follow these guidelines:
1. Write tests for new features
2. Follow existing code patterns
3. Document complex algorithms
4. Keep commits focused and descriptive

## Known Issues

- Some pathfinding tests are failing after recent movement system updates
- Cavalry charge mechanics need balancing
- AI decision-making could be improved

## License
 MIT
 

