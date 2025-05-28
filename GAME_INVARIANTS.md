# Game Invariants

This document captures all the invariants (rules that must always be true) in the game logic.

## 1. Board and Position Invariants

### 1.1 Board Dimensions
- Board width and height must be positive integers
- Board dimensions are immutable once set
- Default board size: 16x12 (can be configured during initialization)

### 1.2 Position Validity
- All unit positions must satisfy: `0 <= x < board_width` and `0 <= y < board_height`
- No two non-garrisoned units can occupy the same position
- Garrisoned units must have `is_garrisoned = true` and valid `garrison_location`
- Units cannot occupy impassable terrain (water, deep water, mountains)

### 1.3 Hex Grid Consistency
- The game uses flat-top hexagonal grid with odd-r offset coordinates
- All hex distance calculations use axial coordinates internally
- Hex neighbors are always exactly 6 (unless at board edge)
- All adjacent hex moves have equal base movement cost (no diagonal penalty in hex grid)

## 2. Unit and Component Invariants

### 2.1 Unit State
- Every unit must have:
  - A valid name (non-empty string)
  - A unit_class from KnightClass enum
  - A valid position (x, y)
  - A player_id (typically 1 or 2)
  - Non-negative soldier count
  - Morale between 0 and 100
  - Will between 0 and max_will

### 2.2 Action Points (AP)
- `0 <= action_points <= max_action_points`
- AP costs are always positive integers
- Units with 0 AP cannot perform any actions
- AP is restored to max at the beginning of each turn

### 2.3 Soldier Count
- `0 <= soldiers <= max_soldiers`
- Dead units (soldiers = 0) must be removed from the game
- Soldier count can only decrease (no healing/reinforcement mechanics currently)

### 2.4 Component Attachment
- Components must be attached to their parent unit
- Behaviors must be registered in unit's behaviors dict before use
- General roster cannot exceed max_generals (default: 3)

## 3. Movement Invariants

### 3.1 Movement Rules
- Units can only move during their player's turn
- Movement requires AP: base cost modified by terrain
- Units cannot move through impassable terrain
- Units cannot move through enemy units
- Units can move through friendly units

### 3.2 Movement Flags
- `has_moved` is set to true after any movement
- Units in enemy ZOC cannot move (except cavalry breakaway)
- Garrisoned units cannot move until they exit garrison
- Movement history is tracked for the current and previous turn only

### 3.3 Pathfinding
- Pathfinding must respect terrain passability
- Path cost cannot exceed available AP
- Paths cannot go through enemy units
- All paths use hex-based movement (6 directions)

## 4. Combat Invariants

### 4.1 Attack Rules
- Units can only attack enemy units
- Attack range depends on unit type (melee=1, archer=3)
- Attacks require AP and set `has_acted = true`
- Counter-attacks only occur in melee range
- Archers don't counter-attack in melee

### 4.2 Damage Calculation
- Damage is always non-negative
- Damage cannot exceed target's current soldiers
- Dead units (0 soldiers) are removed after combat animation
- Disrupted units have 50% damage and defense penalty

### 4.3 Combat Modifiers
- Height advantage: +50% damage when shooting downhill, -50% uphill
- Terrain modifiers apply based on unit type
- Facing modifiers: rear attacks deal more damage
- Morale affects damage output

## 5. Turn and State Invariants

### 5.1 Turn Order
- Players alternate turns (1, 2, 1, 2, ...)
- Turn number increments when player 1 starts their turn
- Current player can only control their own units
- AI controls player 2 units when vs_ai is true

### 5.2 Turn State Reset
- At turn end, for all units of the current player:
  - `has_moved = false`
  - `has_acted = false`
  - `has_used_special = false`
  - `action_points = max_action_points`
  - Engagement states are cleared

### 5.3 Animation State
- No game logic executes during animations
- Unit positions update after movement animations complete
- Damage is applied when attack animations complete
- Fog of war updates after movement/combat

## 6. Visibility and Fog of War Invariants

### 6.1 Visibility States
- Every hex has one of: HIDDEN, EXPLORED, PARTIAL, VISIBLE
- HIDDEN hexes show no information
- EXPLORED hexes show terrain but not current units
- PARTIAL shows unit presence but not details
- VISIBLE shows full unit information

### 6.2 Visibility Rules
- Players can only see their own units' vision
- Vision is blocked by terrain (mountains, forests reduce range)
- Units cannot attack targets they cannot see
- Visibility updates at turn start and after unit movement

### 6.3 Player Isolation
- Each player has a separate visibility map
- Player 1 cannot see Player 2's visibility state
- AI respects fog of war rules (cannot cheat)

## 7. Terrain Invariants

### 7.1 Terrain Properties
- Every hex has exactly one terrain type
- Terrain type determines:
  - Passability (binary: passable or impassable)
  - Movement cost multiplier (>= 0)
  - Defense bonus (>= 0)
  - Vision blocking (binary)
  - Combat modifiers

### 7.2 Terrain Effects
- Impassable terrain: water, deep water, mountains
- Movement penalties are multiplicative with unit type modifiers
- Cavalry becomes disrupted in difficult terrain (forest, swamp)
- Roads always provide movement bonus (0.5x cost)

## 8. Castle Invariants

### 8.1 Castle Properties
- Castles belong to a specific player
- Castles have fixed positions (cannot move)
- Castles can garrison units
- Castles can shoot at enemies within range

### 8.2 Garrison Rules
- Garrisoned units cannot be targeted
- Garrisoned units cannot perform actions
- Units must be adjacent to castle to enter garrison
- Exiting garrison requires empty adjacent hex

## 9. Special Ability Invariants

### 9.1 Cavalry Charge
- Only cavalry can charge
- Charge requires adjacent enemy target
- Charge can push target if there's space behind
- Charge causes disruption to target
- Cavalry cannot charge while disrupted

### 9.2 Breakaway
- Only cavalry can attempt breakaway from ZOC
- Breakaway requires minimum 40 will
- Breakaway costs 10 will on success
- Success chance based on will (will/100)

### 9.3 Unit Facing
- All units have a facing direction (one of 6 hex directions)
- Rotation costs 1 AP per 60-degree turn
- Units in combat cannot rotate
- Facing affects damage received (rear/flank penalties)

## 10. Victory Condition Invariants

### 10.1 Elimination Victory
- Player loses if all their units are eliminated
- Player loses if all their castles are destroyed
- Game checks victory after each combat resolution

### 10.2 Game State Consistency
- Exactly one player can win
- Game ends immediately when victory condition is met
- Dead units are removed before victory check

## 11. Data Structure Invariants

### 11.1 ID Uniqueness
- Unit IDs (using Python id()) must be unique
- Castle positions must not overlap
- Behavior names must be unique within a unit

### 11.2 Reference Integrity
- `garrison_location` must point to valid castle or be None
- `engaged_with` must point to valid enemy unit or be None
- Movement history keys must correspond to existing units

### 11.3 Type Safety
- Board positions are always integers (not floats)
- Player IDs are integers starting from 1
- All enums use proper enum values (not strings)

## 12. Scenario Loading Invariants

### 12.1 JSON Data Validation
- `board_size` must be a 2-element array of positive integers
- Unit positions must be within board bounds
- Unit types must map to valid KnightClass values
- Player IDs must be positive integers

### 12.2 Loading Consistency
- Existing units and castles are cleared before loading
- Terrain is set before placing units
- Units are created with proper initial state
- Fog of war updates after scenario load