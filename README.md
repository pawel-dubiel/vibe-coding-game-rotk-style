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
- **Facing & Flanking**: Unit orientation matters - rear and flank attacks deal bonus damage. Units automatically face threats when engaging.
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

## Installation & Setup

### Prerequisites
- Python 3.10+
- C Compiler (GCC/Clang) & Python Dev Headers (for performance extensions)
- Internet connection (for map generation)

### Quick Start

```bash
# 1. Clone the repository
git clone [repository-url]
cd game

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies (uses pygame-ce for better performance)
pip install -r requirements.txt

# 4. Compile C Extensions (Critical for AI/Pathfinding performance)
python c_modules/setup.py build_ext --inplace

# 5. Run the game
python main.py
```

## Performance & Optimizations

This project uses **C extensions** for pathfinding and hex math, providing a **~22x speedup** over pure Python. 

- **Optimized Algorithms**: A* Pathfinding, Line of Sight.
- **AI Performance**: Fast state cloning and move pruning for responsive AI turns.
- **Configuration**: Toggle optimizations in `game/config.py` (`USE_C_EXTENSIONS`).

*See `c_modules/README.md` for detailed build troubleshooting.*

## Game Modes

### Campaign Mode
Experience medieval Europe with historically accurate maps and cities:
1. **Select Campaign** from the main menu
2. **Choose a Map** (Europe, British Isles, HRE, etc.)
3. **Select a Country** to play
4. **Conquer** territories across authentic medieval landscapes

### Battle Mode
Custom tactical battles with configurable settings against AI or local multiplayer.

## Controls

- **Left Click**: Select unit / Move / Attack
- **Right Click**: Deselect / Unit Info
- **Scroll**: Zoom In/Out
- **Arrow Keys / WASD**: Pan Camera
- **R**: Rotate selected unit manually
- **Space**: End Turn
- **ESC**: Pause / Menu

## Development

### Running Tests
The project maintains high test coverage (~500 tests).
```bash
python -m pytest
```

### Project Structure
- **`game/`**: Core source code
  - **`ai/`**: AI logic (Minimax with pruning)
  - **`behaviors/`**: Unit actions (Movement, Combat)
  - **`entities/`**: Unit and Building definitions
  - **`rendering/`**: Visuals (Pygame-ce based)
- **`c_modules/`**: C extension source code
- **`tools/`**: Map and Asset generation scripts

### Contributing
1. Write tests for new features (`tests/`).
2. Follow existing code patterns (Entity-Component-Behavior).
3. Ensure C extensions compile and pass tests.

## Known Issues
- Cavalry charge mechanics may need balance adjustments in complex terrain.
- Very large campaign maps (Europe 20km hex) require significant RAM.

## License
MIT