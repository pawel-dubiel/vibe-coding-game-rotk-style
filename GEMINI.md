# Gemini Project Context

## Project Overview
Medieval Hex Strategy Game is a comprehensive turn-based strategy game featuring medieval combat on hexagonal grids. It supports both tactical battles and grand campaign modes, emphasizing historical accuracy, realistic terrain, and strategic depth.

## Tech Stack
- **Language:** Python 3.10+
- **Game Engine:** Pygame 2.6.1
- **Image Processing:** Pillow (PIL)
- **Testing:** Pytest 8.3.5

## Architecture
The project follows a component-based architecture to manage complexity and ensure flexibility.

### Key Directories & Modules
- **`game/`**: Contains the core source code.
    - **`main.py`**: The entry point of the application.
    - **`game_state.py`**: Manages the central game state, including units, map, and turn logic.
    - **`entities/`**: Defines game objects like Units (`Knight`, `Archer`, etc.) and Buildings (`Castle`).
    - **`behaviors/`**: Implements pluggable logic for entities (e.g., `Movement`, `Combat`, `SpecialAbilities`).
    - **`components/`**: Data containers for entity properties (e.g., `Stats`, `Facing`, `Generals`).
    - **`ui/`**: Handles user interface elements, menus, and rendering (e.g., `CampaignScreen`, `MainMenu`).
    - **`ai/`**: AI player logic and decision-making.
    - **`campaign/`**: Manages campaign-specific logic, state, and map data.
    - **`rendering/`**: Handles visual output (e.g., `UnitRenderer`, `TerrainRenderer`).
    - **`interfaces/`**: Defines abstract base classes and interfaces.

- **`tools/`**: Utility scripts for development and content generation.
    - **`generate_campaign_maps.py`**: Generates campaign maps using OpenStreetMap data.
    - **`tile_terrain_generator.py`**: Core logic for processing map tiles.

- **`tests/`**: Comprehensive test suite using `pytest`.

### Core Systems & Concepts
- **Hexagonal Grid**: Uses an axial coordinate system for efficient grid traversal and calculation.
    - **`hex_utils.py`**: Utilities for hex math (distance, neighbors, etc.).
    - **`hex_layout.py`**: Handles conversion between hex coordinates and screen pixels.
- **Action Points (AP)**: A resource management system where units spend AP for movement and actions.
- **Combat Mechanics**:
    - **Facing**: Directional damage bonuses (Rear > Flank > Front).
    - **Terrain**: Modifiers for defense and movement costs.
    - **Morale**: Affects unit performance; units can rout.
- **Visibility**:
    - **Line of Sight (LoS)**: Raycasting on the hex grid to determine visible tiles.
    - **Fog of War**: Hides unexplored or currently unobserved areas.
- **Map Generation**: procedural generation based on real-world OpenStreetMap data.

## Development Workflow

### Running the Application
Execute the main script from the root directory:
```bash
python main.py
```

### Testing
Run the full test suite to ensure system integrity:
```bash
python -m pytest
```
*Note: Tests cover various aspects from unit behaviors to complex campaign integration.*

### Map Generation
To generate or update campaign maps:
```bash
python tools/generate_campaign_maps.py
```

## Contributing Guidelines
- **Code Style**: Adhere to Python conventions (PEP 8).
- **Type Hinting**: Use Python type hints for function arguments and return values.
- **Testing**: New features must include accompanying unit tests.
- **Architecture**: Respect the Entity-Component-Behavior pattern. Avoid tight coupling between unrelated systems.
