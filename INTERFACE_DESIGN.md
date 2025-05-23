# Game State Interface Design

## Overview

The game now uses an `IGameState` interface to standardize how different parts of the system interact with game state. This provides:

1. **Type Safety**: Clear contract for what methods/attributes game states must provide
2. **Testing**: Easy to create mock implementations for unit tests
3. **AI Optimization**: SimplifiedGameState can implement only what's needed
4. **Extensibility**: New game state implementations can be added easily

## Interface Definition

The `IGameState` interface (in `game/interfaces/game_state.py`) defines the minimal contract:

### Required Attributes
- `board_width: int` - Width of the game board
- `board_height: int` - Height of the game board  
- `knights: List[Unit]` - All units in the game
- `castles: List[Castle]` - All castles in the game
- `terrain_map: Optional[TerrainMap]` - Terrain information (can be None)
- `current_player: int` - ID of current player

### Required Methods
- `get_knight_at(x, y) -> Optional[Unit]` - Get unit at position

## Implementations

### 1. GameState (Main Implementation)
The full game state with all features:
- Animation management
- UI components
- Camera/viewport system
- Input handling
- Full terrain and castle management

### 2. SimplifiedGameState (AI Implementation)
Lightweight implementation for AI simulations:
- No UI components
- No animations
- Minimal memory footprint
- Fast copying for minimax search

### 3. MockGameState (Testing Implementation)
Clean implementation for unit tests:
- Predictable behavior
- Helper methods for test setup
- No pygame dependencies
- Easy state manipulation

## Usage Examples

### Creating a Mock for Tests
```python
from game.test_utils.mock_game_state import MockGameState

# Create test state
game_state = MockGameState(board_width=20, board_height=15)

# Add units
archer = UnitFactory.create_archer("Test", 10, 10)
game_state.add_knight(archer)

# Test behavior
assert game_state.get_knight_at(10, 10) == archer
```

### Type Hints with Interface
```python
from game.interfaces.game_state import IGameState

def process_turn(game_state: IGameState, unit: Unit):
    """Works with any IGameState implementation"""
    if unit.x < game_state.board_width - 1:
        # Move unit
        pass
```

### AI Using Simplified State
```python
# In AIPlayer._simulate_move()
state_copy = SimplifiedGameState()
state_copy._knights = copy.deepcopy(game_state.knights)
# ... minimal copying for performance
```

## Benefits

1. **Testability**: No more pygame initialization errors in tests
2. **Performance**: AI can use lightweight state copies  
3. **Maintainability**: Clear contract for game state
4. **Flexibility**: Easy to add new implementations
5. **Type Safety**: IDEs can provide better autocomplete

## Migration Guide

When updating existing code:

1. Import the interface:
   ```python
   from game.interfaces.game_state import IGameState
   ```

2. Use type hints:
   ```python
   def my_function(game_state: IGameState):
   ```

3. For tests, use MockGameState:
   ```python
   from game.test_utils.mock_game_state import MockGameState
   game_state = MockGameState()
   ```

4. Access attributes directly (they're guaranteed to exist):
   ```python
   width = game_state.board_width
   units = game_state.knights
   ```