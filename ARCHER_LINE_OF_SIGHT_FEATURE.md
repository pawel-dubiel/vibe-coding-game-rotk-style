# Archer Line-of-Sight Feature

## Overview

This feature implements realistic line-of-sight restrictions for archer ranged attacks, preventing archers from shooting arrows over hills, high hills, and mountains. When players attempt blocked shots, they receive clear feedback messages explaining why the attack cannot be made.

## Implementation Details

### Core Changes

#### 1. Enhanced Visibility System (`game/visibility.py`)

The `_has_line_of_sight()` method was enhanced to properly handle all terrain types:

- **Mountains**: Always block line of sight (impassable high terrain)
- **High Hills**: Block unless viewer is on high ground (hills, high hills, or mountains)  
- **Hills**: Block unless viewer is elevated or on hills/higher ground

#### 2. Archer Attack Behavior (`game/behaviors/combat.py`)

**New Methods Added:**
- `_has_line_of_sight()`: Checks if archer has clear line of sight to target
- `_is_valid_target()`: Override that includes line-of-sight checking for ranged attacks
- `get_attack_blocked_reason()`: Provides specific feedback for why attacks are blocked

**Code Refactoring:**
- Eliminated code duplication between `AttackBehavior` and `ArcherAttackBehavior`
- Added base `_is_valid_target()` helper method for common validation
- Added `get_attack_blocked_reason()` for user feedback

#### 3. Input Handler Integration (`game/input_handler.py`)

Added feedback system for failed attacks:
```python
# Show attack failure feedback
target = game_state.get_knight_at(attack_tile_x, attack_tile_y)
if target and game_state.selected_knight:
    attack_behavior = game_state.selected_knight.behaviors.get('attack')
    if attack_behavior and hasattr(attack_behavior, 'get_attack_blocked_reason'):
        reason = attack_behavior.get_attack_blocked_reason(game_state.selected_knight, target, game_state)
        game_state.add_message(f"Cannot attack: {reason}", priority=1)
```

#### 4. Game State Validation (`game/game_state.py`)

Enhanced `attack_with_selected_knight_hex()` to check valid targets before execution:
```python
# Check if target is valid (includes line of sight for archers)
valid_targets = attack_behavior.get_valid_targets(self.selected_knight, self)
if target not in valid_targets:
    return False  # Attack blocked - feedback will be provided by input handler
```

## User Experience

### Feedback Messages

When players attempt blocked shots, they see specific messages:

- **Line of sight blocked**: "Cannot attack: No line of sight - arrows blocked by terrain"
- **Out of range**: "Cannot attack: Target out of range (distance: X, max range: Y)"
- **Insufficient AP**: "Cannot attack: Not enough action points"
- **Low morale**: "Cannot attack: Morale too low for additional attacks"
- **Invalid target**: "Cannot attack: Target not visible"

### Visual Indicators

- Attack targets list automatically excludes blocked targets
- Players cannot select blocked targets for attack
- Clear messaging prevents confusion about why attacks fail

## Test Scenario

### Archer Line of Sight Test (`test_scenarios/archer_line_of_sight.json`)

A comprehensive test scenario that includes:

**Terrain Setup:**
- Hill barrier (6,4) to (8,7) - blocks shots across the middle
- Mountain cluster (10,3) to (12,5) - always blocks shots
- Forest area (2,2) to (3,3) - provides cover but doesn't block ranged

**Unit Placement:**
- **Archer Alpha** (3,5): Blocked from shooting Target A by hills
- **Archer Beta** (4,8): Can shoot Target B with clear line of sight  
- **Target A** (9,6): Behind hill barrier
- **Target B** (5,9): Clear line of sight available
- **Mountain Target** (13,4): Protected by mountains

**Test Objectives:**
1. Verify hills block archer shots appropriately
2. Confirm mountains always block shots
3. Test clear line-of-sight scenarios work correctly
4. Validate user feedback messages are displayed

## Testing

### Unit Tests

**File**: `tests/test_archer_line_of_sight.py`

Tests include:
- `test_archer_hills_blocking()`: Hills block line of sight
- `test_archer_mountains_blocking()`: Mountains always block
- `test_archer_clear_line_of_sight()`: Clear shots work correctly
- `test_archer_out_of_range()`: Range limitations with feedback

All tests verify both the blocking behavior and appropriate feedback messages.

### Integration Testing

The feature integrates with existing systems:
- ✅ Fog of war visibility checking
- ✅ Action point consumption
- ✅ Morale requirements for multiple attacks  
- ✅ Attack animations and damage calculations
- ✅ Turn-based game flow

## Game Balance Impact

### Tactical Considerations

- **Hills as Cover**: Infantry can use hills for protection from archer fire
- **Elevation Advantage**: Cavalry (elevated units) can see over some terrain
- **Positioning Strategy**: Archers must consider terrain when positioning
- **Mountain Barriers**: Mountains create absolute safe zones from ranged fire

### Backward Compatibility

- All existing scenarios continue to work
- Melee combat remains unchanged
- Non-archer ranged units (mages) inherit the same restrictions
- Fog of war mechanics remain intact

## Future Enhancements

Potential improvements could include:

1. **Partial Cover**: Reduced damage instead of complete blocking
2. **Trajectory Visualization**: Show arrow arc over terrain
3. **Elevation Levels**: More granular height-based visibility
4. **Unit Blocking**: Large units blocking shots to units behind them
5. **Weather Effects**: Rain/fog affecting visibility ranges

## Technical Notes

### Performance

- Line-of-sight calculations use efficient ray-casting algorithm
- Results cached within fog-of-war system
- No performance impact on existing features

### Architecture

- Clean separation between visibility logic and combat logic
- Extensible design allows easy addition of new terrain types
- Consistent with existing behavior pattern architecture

### Error Handling

- Graceful degradation when fog-of-war unavailable
- Clear error messages for invalid scenarios
- Robust input validation throughout