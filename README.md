# Hex Strategy Game

A turn-based tactical strategy game featuring medieval combat on a hexagonal grid, with terrain effects, fog of war, and unit management.

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
- **Dynamic Generation**: Realistic terrain using Perlin noise algorithms

### Special Abilities
- **Cavalry Charges**: Devastating charges that can push enemies back
- **Breakaway Mechanics**: Attempt to disengage from combat
- **General System**: Leaders provide passive bonuses and active abilities
- **Morale System**: Units can rout when taking heavy casualties

### Game Modes
- **Battle Mode**: Custom battles with configurable settings
- **Multiplayer**: Hot-seat multiplayer support
- **AI Opponents**: Computer-controlled enemies
- **Campaign Mode**: Basic Poland map with army movement

## Installation

### Requirements
- Python 3.10+
- Pygame 2.6+

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
pip install pygame
```

## Running the Game

```bash
python main.py
```

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
├── main.py              # Entry point
├── game/
│   ├── game_state.py    # Core game state management
│   ├── renderer.py      # Visual rendering
│   ├── input_handler.py # Input processing
│   ├── hex_utils.py     # Hexagonal grid utilities
│   ├── terrain.py       # Terrain system
│   ├── visibility.py    # Fog of war implementation
│   ├── pathfinding.py   # Movement algorithms
│   ├── entities/        # Units and buildings
│   ├── behaviors/       # Unit behaviors (movement, combat, etc.)
│   ├── components/      # Unit components (stats, facing, generals)
│   ├── ui/             # User interface elements
│   └── ai/             # AI implementation
└── tests/              # Unit tests
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

## Future Features

- Campaign mode with persistent armies
- More unit types and abilities
- Multiplayer networking support
- Map editor
- Mod support

## License

[Your License Here]

## Credits

Created by [Your Name]

Special thanks to:
- Pygame community for the graphics framework
- Hex grid algorithms from Red Blob Games