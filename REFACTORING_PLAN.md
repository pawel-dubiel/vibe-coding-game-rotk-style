# Code Refactoring Plan

## Critical Issues Identified

Based on comprehensive code review, the following architectural issues require immediate attention:

### **CRITICAL (Fix Immediately)**

#### 1. GameState Class Violation (1,137 lines)
**File:** `game/game_state.py`

**Current Issues:**
- Handles 8+ different responsibilities
- Game logic + Camera + Animation + AI + Messages + Save/Load
- Impossible to test individual components
- Changes in one area break unrelated functionality

**Refactoring Plan:**
```
game/state/
├── core_game_state.py      # Core game state, turns, unit management (PENDING)
├── camera_manager.py       # Camera positioning and viewport (✅ COMPLETE)
├── message_system.py       # Combat messages and notifications (✅ COMPLETE)
├── victory_manager.py      # Victory condition checking (✅ COMPLETE)
├── state_serializer.py     # Save/load functionality (✅ COMPLETE)
└── animation_coordinator.py # Animation management (✅ COMPLETE)
```

**Priority:** 🔴 CRITICAL - Blocks all other improvements
**Status:** ✅ COMPLETE - All components extracted and integrated successfully

#### 2. Movement Logic Duplication
**Files:** `unit.py`, `movement.py`, `game_state.py`

**Current Issues:**
- Same movement calculations in 3 different places
- Inconsistent AP costs and validation
- High bug risk from desynchronization
- Testing requires checking multiple implementations

**Refactoring Plan:**
- Consolidate ALL movement logic in `behaviors/movement.py`
- Remove movement methods from `unit.py` (keep compatibility wrappers)
- Move execution logic from `game_state.py` to movement behaviors
- Single source of truth for movement rules

**Priority:** 🔴 CRITICAL - Active bug risk
**Status:** ✅ COMPLETE - MovementService created, all logic consolidated

#### 3. Renderer Mixing Business Logic
**File:** `game/renderer.py` (794 lines)

**Current Issues:**
- Rendering code mixed with game logic decisions
- Asset management embedded in rendering
- Fog of war calculations in renderer
- UI state management in rendering class

**Refactoring Plan:**
```
game/rendering/
├── core_renderer.py        # Main rendering coordinator
├── terrain_renderer.py     # Terrain and hex grid
├── unit_renderer.py        # Units and castles
├── ui_renderer.py          # UI elements and HUD
└── effect_renderer.py      # Animations and effects
```

**Priority:** 🔴 CRITICAL - Makes changes risky
**Status:** ✅ COMPLETE - Renderer split into 4 specialized components, integrated successfully

### **HIGH PRIORITY (Next Sprint)**

#### 4. Input Handler Tight Coupling
**File:** `game/input_handler.py`

**Issues:**
- Directly modifies game state
- Mixed input capture with business logic
- No command pattern for undo/replay
- Zoom logic embedded in input handling

**Refactoring Plan:**
```
game/input/
├── input_manager.py        # Input capture and routing
├── command_processor.py    # Command pattern implementation
├── zoom_controller.py      # Camera zoom management
└── commands/               # Individual command classes
```

#### 5. Terrain System Organization
**File:** `game/terrain.py` (933 lines)

**Issues:**
- TerrainGenerator + TerrainMap + Features in one file
- Legacy compatibility polluting new system
- Multiple property calculation methods

**Refactoring Plan:**
```
game/terrain/
├── terrain_types.py        # Enums and base properties
├── terrain_generator.py    # Map generation algorithms  
├── terrain_map.py         # Storage and access
└── terrain_features.py    # Special features and effects
```

### **MEDIUM PRIORITY (Future Sprints)**

#### 6. Component vs Behavior Confusion
**Files:** `components/` and `behaviors/` directories

**Issues:**
- Unclear distinction between Components and Behaviors
- Similar interfaces but different purposes
- Inconsistent usage patterns

**Clarification Needed:**
- **Components:** Data containers (Stats, Facing, Generals)
- **Behaviors:** Action systems (Movement, Combat, Vision)

#### 7. Animation System Side Effects
**File:** `game/animation.py`

**Issues:**
- Animation classes modify game state
- Business logic embedded in animations
- Mixed rendering and game logic

#### 8. UI/Logic Separation
**Files:** `ui/` directory

**Issues:**
- UI components contain business logic
- Direct game entity access in UI
- Validation mixed with presentation

### **LOW PRIORITY (Technical Debt)**

#### 9. Asset Management Distribution
**Files:** `asset_manager.py` and `renderer.py`

**Issues:**
- Asset logic split between files
- No lifecycle management
- Direct asset loading in renderer

#### 10. Pathfinding Coupling
**File:** `game/pathfinding.py`

**Issues:**
- Tightly coupled to game state structure
- No algorithm abstraction
- Performance mixed with algorithm logic

## Implementation Strategy

### Phase 1: Critical Fixes (Week 1)
1. **Split GameState class** into focused modules
2. **Consolidate movement logic** to eliminate duplications
3. **Separate renderer concerns** for clean architecture

### Phase 2: High Priority (Week 2)  
4. **Refactor Input Handler** with command pattern
5. **Organize Terrain system** for maintainability

### Phase 3: Medium Priority (Week 3)
6. **Clarify Component/Behavior patterns**
7. **Clean Animation system** side effects
8. **Separate UI from business logic**

### Phase 4: Technical Debt (Week 4)
9. **Centralize Asset Management**
10. **Abstract Pathfinding system**

## Success Metrics

- **Reduced file sizes** (no files > 500 lines)
- **Single responsibility** per class/module
- **Eliminated duplications** (DRY principle)
- **Improved testability** (isolated components)
- **Cleaner interfaces** between modules

## Risk Mitigation

- **Incremental changes** to avoid breaking functionality
- **Comprehensive testing** after each refactoring step
- **Backup branches** before major changes
- **Gradual migration** with compatibility wrappers