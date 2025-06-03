# Changelog

All notable changes to Castle Knights will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
  
### Added
- Zoom functionality with trackpad and keyboard support
  - Two-finger trackpad scrolling for zoom in/out on macOS
  - Mouse wheel zoom support for all platforms
  - Keyboard shortcuts: `+`/`=` to zoom in, `-` to zoom out
  - Zoom range: 0.5x to 3.0x with smooth 1.2x increments
  - Dynamic hex grid scaling that maintains accurate coordinates at all zoom levels
  - Fixed attack and charge targeting to work correctly at all zoom levels
  - Synchronized hex layout updates between input handler, renderer, and game state
  - Fixed attack and charge damage application to use correct Unit API (take_casualties instead of take_damage)
  - Fixed cavalry engagement bug: ranged attacks no longer incorrectly engage units in combat

### Refactored
- **Major Architecture Overhaul**: Comprehensive refactoring following single responsibility principle
  - Split monolithic GameState class (1,137 lines) into focused components:
    - MessageSystem: Combat messages and notifications with priority-based display
    - CameraManager: Camera positioning, zoom, and coordinate transformations  
    - VictoryManager: Victory condition checking and game completion detection
    - StateSerializer: Game state serialization for save/load functionality
    - AnimationCoordinator: Animation lifecycle and timing management
  - Consolidated duplicate movement logic from unit.py, movement.py, game_state.py:
    - Created MovementService as single source of truth for all movement operations
    - Eliminated code duplication and ensured consistent movement validation
    - Centralized movement path calculation and AP cost computation
  - Split monolithic Renderer class (794 lines) into specialized components:
    - TerrainRenderer: Hex grid, terrain types, and fog of war overlays
    - UnitRenderer: Unit sprites, health bars, and status indicators  
    - UIRenderer: HUD elements, turn counter, and context menus
    - EffectRenderer: Animations, particles, and visual effects
    - CoreRenderer: Coordinates all rendering components with clean pipeline
- Created `game/state/` and `game/rendering/` modules with focused responsibilities
- Improved testability and maintainability through better separation of concerns
- Reduced file sizes (no files > 500 lines) and eliminated architectural violations
- **Successfully integrated and tested**: All refactored components working correctly in-game
  - Fixed attack target rendering to handle both coordinate tuples and unit objects
  - Corrected context menu display to show proper text instead of raw object data
  - Updated input handler to use new animation coordinator interface
  - Ensured compatibility with existing unit property access patterns
  - **Restored missing UI elements**: Added End Turn button, victory messages, castle info display
  - Fixed context menu to display proper action text instead of raw object data
  - Engagement status now properly clears when units move away from enemies
  - Only melee and charge attacks set engagement status, not ranged attacks
  - Added comprehensive test suite for engagement mechanics (test_engagement_mechanics.py)
  - Updated MockGameState to support ZOC testing for future test development
- Improved morale system and automatic routing for more realistic combat
  - Units now lose more morale from casualties (30% base + 15% shock for heavy losses)
  - Automatic routing when morale drops below 20%
  - Probabilistic routing between 20-40% morale for panic effects
  - Units can start routing during the same turn they take heavy losses
  - Added routing messages to inform players when units break
  - Routing units now automatically flee away from enemies on the same turn
  - Immediate panic movement provides realistic battlefield psychology
- Enhanced archer line-of-sight restrictions
  - Archers cannot shoot over hills, high hills, or mountains
  - Terrain blocking uses existing fog of war line-of-sight calculations
  - Clear user feedback when shots are blocked by terrain
  - Added test scenario for archer line-of-sight mechanics
- Comprehensive game documentation system
  - Created docs/ folder with detailed mechanism guides
  - Complete routing system documentation with tactical implications
  - Quick reference cards for key game mechanics
  - Code references and strategic guides for developers and players
  - Both attackers and defenders can route from combat casualties

### Fixed
- Cavalry movement restrictions in Zone of Control scenarios
  - Fixed logic order in ZOC disengagement checks
  - High-morale cavalry (75%+) can now properly disengage from enemy ZOC
  - Resolves issue where cavalry showed no movement options when adjacent to enemies
  - Maintains tactical depth while allowing proper flanking maneuvers
- Morale recovery and rally system for routing units
  - All units recover +10 morale per turn, routing units recover +15 morale per turn
  - Routing units can rally when morale reaches 40+ (probabilistic based on condition)
  - Rally chance: 70% base, 90% with high morale, reduced if heavily damaged
  - Routing units take 30% less damage (representing scattered/fleeing formation)
  - Rally messages inform players when units stop routing and return to battle
  - Prevents permanent routing - units can recover if given time to regroup
- PNG asset support for terrain rendering
  - AssetManager class for loading and caching image assets
  - Automatic scaling of terrain images to match zoom level
  - Support for water.png, deep-water.png, plain.png, hills.png, high-hills.png, light-forrest.png, forrest.png, dense-forrest.png, swamp.png, mountains.png, snow.png, and desert.png terrain textures
  - Graceful fallback to procedural rendering when assets unavailable
  - Assets stored in `/assets/` directory with organized structure
- Zoom-aware coordinate system
  - Fixed mouse coordinate conversion to work correctly at all zoom levels
  - Hex-based movement actions bypass pixel-to-hex conversion issues
  - Improved camera bounds for better navigation when zoomed in
  - Movement accuracy maintained regardless of zoom level or starting position
- Scrollbar support for Test Scenarios menu
  - Mouse wheel scrolling
  - Draggable scrollbar handle
  - Keyboard navigation with automatic scrolling
  - Supports unlimited number of test scenarios
- Save and Load game system with multiple slots
  - 10 save slots available for different game progress
  - Save metadata includes turn number, player count, unit count, and timestamp
  - Custom save names with optional text input
  - Visual save/load menu accessible from main menu and pause menu
  - Scrollbar support for save slot navigation
    - Mouse wheel scrolling through save slots
    - Draggable scrollbar handle
    - Shows 6 slots at a time with smooth scrolling
  - Overwrite confirmation dialog for existing saves
  - Delete functionality for managing save files
  - Dedicated saves directory for organization
  - Comprehensive state persistence including:
    - All unit positions, stats, and action states
    - Castle health and garrison status
    - Terrain configuration
    - Fog of war visibility states
    - Camera position
    - Turn and player information
    - Movement history
  - Error handling with informative messages
  - Save files use Python pickle format for serialization
  - Metadata stored in JSON for quick access
- Game invariants documentation (GAME_INVARIANTS.md)
  - Comprehensive list of rules that must always be true
  - Covers board positions, units, movement, combat, turns, visibility, terrain, castles, abilities, victory conditions, data structures, and scenario loading
  - Serves as reference for maintaining game consistency
- Test scenario loader improvements
  - Fixed property access for unit soldiers count
  - Added explicit tuple conversion for board_size
  - Improved error handling in scenario loading
- Performance optimizations for turn transitions
  - Fixed fog of war updating for all players instead of just active player
  - Reduced AI turn delay from 0.5s to 0.1s for snappier gameplay
  - Eliminated unnecessary visibility recalculations during turn changes
- Completely redesigned terrain generation for consistent, balanced battlefields
  - All maps now start with plains base, then add strategic terrain features in controlled amounts
  - Guaranteed terrain distribution: 1-2 hill clusters, 2-4 forest clusters, 1-2 streams, 0-1 swamp areas
  - Hills placed strategically with 40% chance for high hills at cluster centers
  - Forest clusters use natural progression: dense forest center → regular forest → light forest edges
  - Streams drawn as lines across battlefield with occasional width variation
  - Swamps only appear near streams (40% chance) for realistic placement
  - Prevents problematic terrain generation (no more all-hills or all-forest maps)
  - Area-clearing algorithm ensures features don't overlap inappropriately
  - Maintains 60-70% plains for tactical maneuvering while adding meaningful terrain variety
- Improved line-of-sight algorithm using shadow casting
  - Implemented SimpleShadowcaster for efficient field of view calculations
  - Sector-based approach adapted for hexagonal grids
  - Significant performance improvement over checking every hex individually
  - Accurate terrain and unit blocking mechanics
  - Proper handling of elevation (cavalry, hills) for vision calculations
  - Tests updated to validate new shadow casting behavior
  - Turn transitions are now significantly faster
- Reduced general morale bonuses for more visible combat feedback
  - InspireAbility morale bonus reduced from +10 to +5
  - General level morale bonus reduced from +2 per level to +1 per level
  - Total typical morale bonus reduced from +14 to +7
  - Morale drops now visible after smaller amounts of damage
  - Maintains morale recovery benefits while improving combat feedback
- Enhanced cavalry charge feedback system for better user experience
  - Added `get_charge_info_at()` method to provide detailed charge failure reasons
  - Input handler now displays helpful messages when charges fail
  - Categorized failure types: terrain restrictions, insufficient will, not adjacent, etc.
  - Players now see immediate feedback like "Cannot charge: Cannot charge from hills"
  - Improved MockGameState with charge feedback support for testing
- Completely overhauled attack system for tactical depth and realism
  - **Terrain-based attack costs**: AP cost = unit base cost + (terrain movement cost - 1.0) × 2
    - Plains: No penalty (1.0x movement cost)
    - Hills/Forest: +2 AP penalty (2.0x movement cost)
    - Dense Forest/Swamp: +4 AP penalty (3.0x movement cost)
    - Light Forest: +1 AP penalty (1.5x movement cost)
    - Ranged attacks have reduced terrain penalties (1x instead of 2x multiplier)
  - **Multiple attacks per turn**: Removed `has_acted` limitation, units can attack multiple times per turn
  - **Morale requirements**: Second and subsequent attacks require 50%+ morale to execute
  - **Progressive morale loss**: Combat fatigue increases with multiple attacks
    - 1st attack: No morale loss
    - 2nd attack: -10 morale
    - 3rd attack: -15 morale
    - 4th attack: -20 morale, etc. (attacks_this_turn × 5)
  - **Attack counter system**: Tracks attacks per turn, resets at end of turn
  - **AP-based attack limits**: Natural limit through action point consumption
  - Comprehensive test suite added (test_enhanced_attack_system.py)
  - Examples:
    - Warrior vs enemy on plains: 4 AP per attack, no morale loss (1st attack)
    - Warrior vs enemy on hills: 6 AP per attack, -10 morale (2nd attack)
    - Archer vs enemy in dense forest: 4 AP per attack (reduced terrain penalty)

### Fixed
- **Critical Post-Refactoring Issues**: Fixed zoom and attack functionality that stopped working after architecture overhaul
  - **Zoom System**: Fixed zoom functionality by restoring the original working implementation
    - **Reverted to Hex Layout Scaling**: Restored the original approach of scaling hex layout size for proper zoom
    - Fixed zoom to scale hexes and all game elements proportionally (making everything appear larger/smaller)
    - Input handler manages zoom level and creates scaled hex layouts (36px base × zoom factor)
    - CoreRenderer uses input handler's scaled hex layouts for proper visual zoom effect
    - **Asset Scaling**: Fixed terrain assets (PNG textures) to scale with zoom level
    - Terrain images now get larger/smaller with zoom changes for proper visual zoom effect
    - AssetManager scales terrain textures based on hex_size for consistent zoom behavior
    - Updated input handler to call `update_zoom()` only when zoom actually changes
    - Fixed coordinate conversion pipeline to use consistent camera and hex layout systems
    - Synchronized legacy camera properties with new camera manager for compatibility
  - **Attack System**: Fixed attack functionality by resolving coordinate conversion issues
    - Updated input handler to use game state's hex layout instead of its own for coordinate conversion
    - Fixed screen-to-world coordinate conversion to use camera manager consistently
    - Added automatic hex layout synchronization with camera zoom in game state update loop
    - Ensured all coordinate transformations maintain accuracy at all zoom levels
  - **Camera Synchronization**: Implemented proper sync between legacy camera system and new camera manager
    - Legacy `camera_x/camera_y` properties now stay synchronized with `camera_manager` position
    - All coordinate conversion methods (`screen_to_world`, `world_to_screen`) now use camera manager
    - Fixed initialization to ensure both camera systems start with identical positions
  - **Animation System Integration**: Updated AI player to use new animation coordinator interface
    - Fixed AI player references from `animation_manager` to `animation_coordinator.animation_manager`
    - Updated state serializer to use animation coordinator's `clear_animations()` method
    - Maintained backward compatibility while using new modular architecture
- **Post-Refactoring UI Issues**: Fixed terrain info display and unit selection rendering
  - **Terrain Info Display**: Fixed terrain details not showing when clicking on empty terrain
    - Updated UI renderer to properly extract terrain object from terrain_info structure
    - Fixed terrain_info parsing to show terrain type, movement cost, elevation, and defense bonus
    - Terrain info now displays: "Terrain: Plains (2, 3) | Movement Cost: 1.0 | Elevation: 1, Defense: +0"
  - **Unit Selection Rendering**: Fixed overlapping lines when selecting units
    - Removed duplicate selection highlight from terrain renderer (hex polygon outline)
    - Added proper selection circle rendering to unit renderer (yellow circle around unit)
    - Eliminated visual conflicts between multiple selection indicator systems
  - **Legacy Renderer Conflicts**: Renamed old renderer.py to prevent conflicts with new modular system
- Fixed UnboundLocalError in attack_with_selected_knight_hex method
  - Removed redundant local KnightClass import that was causing scoping issues
  - Attack system now works correctly in the main game

## [0.5.0] - 2025-01-27

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
    - Uses proper A* search with hex distance heuristic
    - Includes path caching for performance
    - Pre-computed neighbor cache (CachedHexGrid)
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
- Combat Mode System
  - RANGED: Attacks from distance (>1 hex) receive no counter-attack
  - MELEE: Close combat (1 hex) with full counter-attacks
  - CHARGE: Cavalry charges get +30% damage bonus but 75% counter-damage
  - SKIRMISH: Future mode for hit-and-run tactics (50% counter-damage)
  - Archers no longer counter-attack in melee combat
- Test Scenarios System
  - New "Test Scenarios" option in main menu
  - Pre-configured battlefield setups for testing specific mechanics
  - Scenarios include: Archer Attack, Cavalry Charge, Combat Modes, Terrain Effects, Flanking Attack, Movement & Terrain
  - Deterministic terrain (always starts as flat plains with specific modifications)
  - Both players are human-controlled for testing mechanics
  - Clear instructions displayed when each scenario starts
  - Visual mode indicators in UI and battle setup
- Fog of War system with Line of Sight mechanics
  - Each player has limited visibility based on their units' positions
  - Visibility states: Hidden, Explored, Partial, Visible
  - Line of Sight calculations with terrain blocking
    - Uses hexagonal grid-adapted line drawing algorithm
    - Linear interpolation in cube coordinates for accurate hex traversal
    - Not Bresenham's algorithm but similar "supercover" approach for hexes
  - Hills block vision unless viewer is on elevated terrain
  - Cavalry units block vision behind them (unit blocking)
  - Terrain always visible but greyed out when not in direct sight
  - Units at distance visible but unidentified (appear as generic markers)
  - Unified visibility from all player's units
  - AI operates with limited information (respects fog of war)
  - Generals with Keen Sight ability have extended vision range
- Height advantage system for ranged combat
  - Archers shooting uphill receive 30% damage penalty
  - Archers shooting downhill receive 20% damage bonus
  - No height modifier when both units at same elevation
- Cavalry charge restrictions on hills
  - Cavalry cannot initiate charges when standing on hills
  - Cavalry cannot charge at enemies positioned on hills
  - Prevents unrealistic cavalry charges up steep terrain
- Terrain movement behaviors for proper abstraction
  - TerrainMovementBehavior base class for unit terrain interactions
  - CavalryTerrainBehavior: Struggles in forests/swamps, excels on plains
  - ArcherTerrainBehavior: Forest movement bonus and combat advantages
  - WarriorTerrainBehavior: Reduced penalties in difficult terrain
  - MageTerrainBehavior: Extra penalties in swamps
  - Eliminates type checking in terrain system (Liskov Substitution Principle)
- Enhanced terrain system with layers and realistic generation
  - New terrain types: Light Forest, Dense Forest, High Hills, Mountains, Deep Water, Marsh, Desert, Snow
  - Terrain features layer: Streams, rivers, roads, bridges, ruins, villages, fortifications
  - Realistic terrain generation using Perlin noise for height and moisture maps
  - Rivers flow naturally from high elevation to low, following terrain
  - Roads pathfind between important locations avoiding difficult terrain
  - Elevation system affects vision and combat
  - Legacy terrain generation mode for backward compatibility
  - Terrain information display: Click empty terrain to see details
    - Shows terrain type, features, movement cost, defense bonus, elevation
    - Displays passability and vision blocking information
    - Helps players understand tactical terrain advantages
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
  - Fog of war visibility tests
  - Attack targeting visibility tests
  - Cavalry charge hill restriction tests
  - Height advantage combat tests
  - Terrain behavior abstraction tests

### Fixed
- Fog of war player ID mismatch
  - Fixed initialization using 0-based indexing while game uses 1-based player IDs
  - Fog of war now properly updates when switching between players
  - Each player correctly sees only their units and what's in vision range
- Castle status display in renderer
  - Fixed crash when no castles exist in test scenarios
  - Castle UI only displays when castles are present

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
- Attack targeting now respects fog of war visibility
  - Units can only target visible enemies
  - Invisible units not highlighted during attack selection
  - AI targeting limited to visible units
- Renderer updated to show all terrain with fog overlays
  - Previously hidden terrain now visible but greyed out
  - Better player understanding of battlefield layout
- Terrain system refactored to use behavior pattern
  - Removed hardcoded unit type checks in terrain.py
  - Terrain modifiers now determined by unit behaviors
  - Follows Liskov Substitution Principle
- Vision system refactored to use behavior pattern
  - Removed hardcoded vision ranges per unit type
  - Vision capabilities now encapsulated in VisionBehavior subclasses
  - Cleaner separation of concerns

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