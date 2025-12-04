# Architecture & Development Guide

This document outlines the high-level architecture of the **Medieval Hex Strategy Game**. It serves as a map to the codebase, explaining how different modules interact.

## 1. Design Philosophy
The game is built on a **Component-Entity-Behavior** hybrid pattern:
- **Entities** (Units, Castles) are containers of state.
- **Components** (Stats, Facing) hold specific data types.
- **Behaviors** (Movement, Combat) contain the logic for actions.

This decouples logic from data, allowing for flexible composition (e.g., adding "MagicUser" behavior to a "Knight" entity).

## 2. Core Modules

### Game Loop (`main.py`)
The entry point. It initializes Pygame, the GameState, and the Renderer. It runs the standard game loop:
1.  **Input Handling**: Processes mouse/keyboard via `InputHandler`.
2.  **Update**: Advances game state (animations, AI, physics) via `GameState.update()`.
3.  **Render**: Draws the frame via `Renderer`.

### State Management (`game/game_state.py`)
The `GameState` class is the "God Object" of the session. It holds:
-   `knights`: List of all active units.
-   `castles`: List of static structures.
-   `terrain_map`: The grid data.
-   `message_system`: The UI log.

### Hexagonal Grid (`game/hex_utils.py`, `game/hex_layout.py`)
We use an **Axial Coordinate System** (q, r) for logic, converted to Pixel coordinates (x, y) for rendering.
-   **Logic**: `HexGrid` handles neighbors, distance, and line-of-sight math.
-   **Visuals**: `HexLayout` handles screen positioning, scaling, and zoom.

## 3. Detailed Systems

### Combat (`game/behaviors/combat.py`)
Combat is deterministic but complex.
-   **Flow**: `can_attack()` -> `calculate_damage()` -> `apply_damage()`.
-   **Key Factors**: Terrain height, Flanking angle, Morale status.

### Pathfinding (`game/pathfinding.py`)
Uses A* (A-Star) algorithm adapted for hexagonal grids.
-   **Costs**: Defined in `MovementBehavior`. Includes terrain cost + Zone of Control penalties.

### Rendering (`game/renderer.py`)
Layered rendering approach:
1.  **Terrain Layer**: Cached surface for performance.
2.  **Grid Layer**: Hex outlines (if enabled).
3.  **Unit Layer**: Sorted by Y-position for correct overlap (2.5D effect).
4.  **Effect Layer**: Arrows, damage numbers, explosions.
5.  **UI Layer**: Menus, tooltips.

## 4. Automatic Documentation
We use **docstrings** in the code to maintain detailed API documentation.
To generate the full API reference HTML:

```bash
# Run the generation script
python tools/generate_docs.py
```

Open `docs/html/index.html` to browse the API.
