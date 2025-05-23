# Action Point System Implementation

## Overview
Redesigned the game's Action Point (AP) system to be more tactical and realistic, where different actions cost different amounts of AP based on terrain, unit type, and combat situations.

## Key Changes

### 1. Increased Starting AP
- **Warriors**: 8 AP (was 3)
- **Archers**: 7 AP (was 3) 
- **Cavalry**: 10 AP (was 4)
- **Mages**: 6 AP (was 2)

### 2. Movement AP Costs
Movement now costs AP based on:
- **Terrain type**: Plains (1), Forest/Hills (2), Swamp (3), Roads (0.5)
- **Diagonal movement**: +40% cost
- **Enemy ZOC**: +1 AP penalty
- **Formation breaking**: +1 AP penalty
- **Unit-specific modifiers**: e.g., cavalry penalty in forest

### 3. Combat AP Costs
- **Warriors**: 4 AP (methodical fighters)
- **Cavalry**: 3 AP (quick attackers)
- **Archers**: 2 AP (ranged is faster)
- **Mages**: 2 AP (magic is efficient)

### 4. Special Abilities
- **Cavalry Charge**: 5 AP + 40 Will (high cost for powerful ability)

## Tactical Impact

### Multiple Actions Per Turn
Units can now perform multiple actions if they manage AP well:
- A cavalry unit (10 AP) could: Move (1-3 AP) + Attack (3 AP) + Move again (1-3 AP)
- An archer (7 AP) could: Move (1-2 AP) + Attack (2 AP) + Move (1-2 AP) + Attack (2 AP)

### Terrain Considerations
- **Roads**: Enable faster movement and repositioning
- **Difficult terrain**: Limits movement options, making positioning crucial
- **Formation fighting**: Staying together is cheaper than breaking formation

### Resource Management
- Players must balance offensive and defensive actions
- Moving through enemy ZOC is expensive
- Special abilities require significant AP investment

## Code Implementation

### Movement Behavior
```python
def get_ap_cost(self, from_pos, to_pos, unit, game_state) -> int:
    terrain_cost = game_state.terrain_map.get_movement_cost(to_pos[0], to_pos[1], unit.unit_class)
    
    # Diagonal penalty
    if is_diagonal:
        terrain_cost = int(terrain_cost * 1.4)
        
    # ZOC penalty
    if unit.in_enemy_zoc:
        terrain_cost += 1
        
    # Formation breaking penalty
    if self._would_break_formation(from_pos, to_pos, unit, game_state):
        terrain_cost += 1
        
    return max(1, terrain_cost)
```

### Combat Behavior
```python
def get_ap_cost(self, unit=None, target=None) -> int:
    if unit.unit_class == KnightClass.WARRIOR:
        return 4
    elif unit.unit_class == KnightClass.CAVALRY:
        return 3
    elif unit.unit_class in [KnightClass.ARCHER, KnightClass.MAGE]:
        return 2
    return 3
```

## Testing
Comprehensive test suite covers:
- ✅ Starting AP values for all unit types
- ✅ Terrain-based movement costs
- ✅ Attack AP costs by unit type
- ✅ Special ability AP costs
- ✅ Multiple actions per turn
- ✅ ZOC movement penalties
- ✅ AP regeneration

## Balance Notes
- System encourages tactical thinking about action economy
- Different unit types have distinct tactical roles
- Terrain becomes much more important
- Positioning and formation fighting rewarded
- Special abilities are powerful but expensive

This creates a much more strategic and realistic combat system where every action matters!