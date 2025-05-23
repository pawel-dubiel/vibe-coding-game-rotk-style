# Changelog

All notable changes to Castle Knights will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Light/Heavy unit classification system
  - Heavy units: Warrior, Cavalry (cannot break away from combat)
  - Light units: Archer, Mage (can break away from heavy units)
- Breakaway mechanics for tactical disengagement
  - Light units can break away from heavy units (100% success)
  - Light vs light has 50% success chance
  - Costs 2 AP, failed attempts lose 10 morale
  - Successful breakaway triggers opportunity attack (35% damage)
- Interface abstraction pattern (IGameState)
  - GameState: Full implementation with UI/animations
  - SimplifiedGameState: Lightweight for AI simulations
  - MockGameState: Clean testing implementation
- Pathfinding abstraction layer
  - PathFinder abstract base class for different algorithms
  - AStarPathFinder implementation for optimal pathfinding
  - DijkstraPathFinder implementation with find_all_reachable support
  - Movement behaviors now use configurable pathfinding strategies
- Unit facing system with directional combat modifiers
  - Six facing directions in hexagonal grid (NE, E, SE, SW, W, NW)
  - Frontal attacks: normal damage
  - Flank attacks: +25% damage bonus
  - Rear attacks: +50% damage bonus
  - Rear attacks can trigger immediate routing checks
  - Visual indicators show unit facing direction (yellow arrows)
  - AI considers facing in tactical evaluations
- Rotation mechanics for tactical positioning
  - Manual rotation action available in context menu
  - Rotation costs AP based on terrain (Plains: 1, Forest/Hills: 2, Swamp: 3)
  - Cannot rotate when adjacent to enemies (combat locked)
  - Can rotate clockwise or counter-clockwise
- Movement facing system
  - Units automatically face the direction they move
  - Auto-facing towards enemies when ending movement within 2 hexes
  - Manual facing selection after movement (limited to 60° turn)
  - Free rotation option when not near enemies
- Multiplayer mode (Hot Seat)
  - Game mode selection screen (Single Player vs Multiplayer)
  - Both players control units on same computer
  - Clear turn indicators showing which human player is active
  - No AI delays in multiplayer mode
  - Visual mode indicators in UI and battle setup
- Comprehensive test coverage for new mechanics
  - Breakaway behavior tests
  - Archer ranged attack tests
  - Movement cost calculations
  - Path animation tests
  - Pathfinding algorithm tests
  - Unit facing tests
  - Rotation mechanics tests
  - Movement facing tests
  - Multiplayer mode tests

### Changed
- Combat system now tracks unit engagement status
- AP costs vary by unit type (Warriors: 4, Cavalry: 3, Mage/Archer: 2)
- Archers have 3-tile attack range
- Counter-attacks don't apply to archers in melee combat
- Movement system considers terrain costs and diagonal penalties
- Breaking from enemy Zone of Control costs extra AP
- AI uses lightweight game state for better performance
- Animation system supports multi-step path animations
- Knight class refactored to minimal implementation
  - Removed ~800 lines of duplicate code
  - Removed duplicate logic now handled by behaviors
  - Kept only essential properties for legacy compatibility
  - All game logic uses Unit instances with behaviors
  - Knight class marked as legacy with clear documentation
  - Fixed all test failures from refactoring (143 tests passing)
- Knight class completely removed
  - Eliminated backward compatibility class entirely
  - KnightAdapter no longer inherits from Knight
  - All tests use UnitFactory directly
  - Cleaner codebase with no legacy dependencies
- Combat damage calculations now include facing modifiers
- AI evaluation function enhanced with facing considerations
- Movement animations update unit facing during execution
- Game flow updated: Main Menu → Game Mode → Battle Setup → Game

### Fixed
- Unit engagement tracking during combat
- Movement path calculation with proper AP costs
- Animation positioning for hex grid coordinates
- Zone of Control (ZOC) movement restrictions preventing units from approaching enemies
  - Units can now properly move adjacent to enemies for melee combat
  - Movement cost calculation no longer blocks entering enemy ZOC
  - Units in ZOC can move to any adjacent hex (not just toward the enemy)
- Health bar alignment on units (properly centered)
- Hex alignment in visual tests (using HexLayout for consistency)
- AI division by zero error when evaluating facing positions
- Zone of Control mechanics for heavy units
  - Heavy units cannot disengage from other heavy units
  - Proper checking of unit engagement status
  - Breakaway rules correctly enforced based on unit types
- Multiplayer input handling
  - Removed hardcoded Player 1 restrictions from input handler
  - Both players can now select units and end turns
  - Fixed "End Turn" button to work for both players
  - Fixed spacebar and mouse controls for all players

## [0.4.0] - 2025-05-24

### Added
- Hexagonal tile system replacing square grid
- Proper hexagonal tessellation with interlocking hex tiles
- Flat-top hex orientation with correct spacing calculations
- Comprehensive hex coordinate system (offset, axial, cube coordinates)
- Hex-based movement, distance calculations, and zone of control

### Changed
- Board rendering system now uses hexagonal tiles instead of squares
- Movement and distance calculations updated for hexagonal grid
- Unit positioning and highlighting system aligned with hex coordinates
- Animation system updated to work with hex coordinate positions

### Fixed
- Field highlighting misalignment when selecting unit movement options
- Units moving to incorrect fields when clicking on hex tiles
- AI player crash due to missing HexGrid import in evaluation function
- Coordinate consistency between rendering, input handling, and game logic

## [0.3.0] - 2025-05-23

### Added
- Complete menu system with main menu and pause functionality
  - Main menu displayed on game start with options: New Game, Load Game, Options, Quit
  - In-game pause menu accessible via ESC key with Resume, Save Game options
  - Visual hover effects and button states
  - Semi-transparent overlay for pause menu
- Menu navigation flow improvements
  - Game now starts at main menu instead of directly in battle
  - ESC in battle setup returns to main menu
  - ESC during gameplay toggles pause menu
- Placeholder implementations for future features (Load/Save/Options)
- Comprehensive test suite for menu system

## [0.2.0] - 2025-05-23

### Added
- Battle setup screen for choosing battle size
  - Small battles: 15x15 board, 3 knights, 1 castle
  - Medium battles: 20x20 board, 5 knights, 2 castles
  - Large battles: 25x25 board, 8 knights, 3 castles
- Camera/viewport system for battlefield scrolling
  - Right-click drag to pan the camera
  - Keyboard scrolling with arrow keys and WASD
  - Automatic camera centering on player 1's starting units
  - Camera bounds checking to prevent scrolling beyond battlefield
- Optimized rendering system that only draws visible tiles
- Screen-to-world coordinate conversion system
- Comprehensive test suite for camera functionality

### Changed
- Game flow now includes battle setup before starting
- Board size is now configurable based on battle type
- Unit placement scales with battle size

## [0.1.0] - 2025-05-23

### Added
- Initial game implementation
- Turn-based tactical combat system
- Multiple unit types: Warriors, Archers, Cavalry, Mages
- Castle-based gameplay with garrison mechanics
- AI opponent with basic strategy
- Combat system with morale and special abilities
- Terrain system affecting movement and combat
- Animation system for unit actions
- Context menu for unit commands
- Victory conditions based on castle control and unit elimination

### Technical Features
- Pygame-based rendering engine
- Entity-component system architecture
- Modular codebase with clear separation of concerns
- Comprehensive unit test coverage

---

## Version History

- **0.3.0** - Menu System Update
- **0.2.0** - Battle Setup & Scrolling Update  
- **0.1.0** - Initial Release