# Zone of Control (ZOC)

This document describes how the current game code implements Zone of Control mechanics.

## Determining if a Unit Has ZOC

A unit exerts ZOC when it is not routing, has at least 25 morale and still has soldiers. The `Unit` method is shown below:

```python
class Unit:
    def has_zone_of_control(self) -> bool:
        """Check if unit exerts Zone of Control"""
        # Only non-routing units with good morale have ZOC
        return not self.is_routing and self.morale >= 25 and self.soldiers > 0
```

(See `game/entities/unit.py` lines 341-344.)

## Detecting When a Unit Is in Enemy ZOC

During each update the game checks if a unit is adjacent (including diagonals) to an enemy that has ZOC. The method returns the enemy exerting the ZOC if found:

```python
class Unit:
    def is_in_enemy_zoc(self, game_state) -> Tuple[bool, Optional['Unit']]:
        """Check if unit is in enemy Zone of Control"""
        for enemy in game_state.knights:
            if (enemy.player_id != self.player_id and
                enemy.has_zone_of_control()):
                # Check if adjacent (including diagonals)
                dx = abs(self.x - enemy.x)
                dy = abs(self.y - enemy.y)
                if dx <= 1 and dy <= 1 and (dx + dy > 0):
                    return True, enemy
        return False, None
```

(See `game/entities/unit.py` lines 346-356.)

The `GameState` method `_update_zoc_status` calls `is_in_enemy_zoc` for every unit each frame, storing the result and clearing engagement if none is found:

```python
for knight in self.knights:
    in_zoc, enemy = knight.is_in_enemy_zoc(self)
    knight.in_enemy_zoc = in_zoc
    knight.engaged_with = enemy if in_zoc else None

    # Clear engagement status if no longer in enemy ZOC
    if not in_zoc:
        knight.is_engaged_in_combat = False
```

(See `game/game_state.py` lines 356-362.)

## Movement Restrictions

Movement costs and available destinations change when a unit is already inside enemy ZOC.

### AP Cost Penalty

The movement cost calculation adds +1 action point when the moving unit is currently in enemy ZOC:

```python
if unit.in_enemy_zoc:
    terrain_cost += 1  # Extra AP to disengage
```

(See `game/behaviors/movement.py` lines 46-48.)

### Limiting Possible Moves

When a unit is inside enemy ZOC and cannot disengage, its only legal move is into the hex occupied by the engaged enemy (to attack). If no enemy is set, no movement is allowed:

```python
# Special handling for units in ZOC
if unit.in_enemy_zoc and not self._can_disengage_from_zoc(unit):
    # Can only move to attack the engaging enemy
    if unit.engaged_with:
        return [(unit.engaged_with.x, unit.engaged_with.y)]
    return []
```

(See `game/behaviors/movement.py` lines 151-156.)

### Approaching Enemy ZOC

Units that start **outside** enemy ZOC may enter an adjacent threatened tile but must end their movement there. The pathfinding logic prevents leaving that tile in the same action unless the unit moves directly onto the enemy's position. This is handled by `_zoc_transition_blocked`:

```python
def _zoc_transition_blocked(self, from_pos, to_pos, unit, game_state):
    if unit.in_enemy_zoc:
        return False
    from_in_zoc = self._is_enemy_zoc_tile(from_pos[0], from_pos[1], unit, game_state)
    to_in_zoc = self._is_enemy_zoc_tile(to_pos[0], to_pos[1], unit, game_state)
    if from_in_zoc and not to_in_zoc and not self._is_enemy_at(to_pos[0], to_pos[1], unit, game_state):
        return True
    return False
```

(See `game/behaviors/movement.py` lines 301-314.)

### Disengagement Checks

The `_can_disengage_from_zoc` helper determines whether the unit may leave enemy ZOC. Routing units and high-morale cavalry can always attempt to disengage. Heavy units engaged with other heavy units generally cannot. Custom `can_break_away_from` logic is used if available:

```python
def _can_disengage_from_zoc(self, unit) -> bool:
    # Routing units always try to move
    if unit.is_routing:
        return True

    # Cavalry with high morale can attempt to disengage
    if unit.unit_class == KnightClass.CAVALRY and unit.morale >= 75:
        return True

    # Heavy units cannot disengage from heavy enemies
    if unit.is_heavy_unit() and unit.engaged_with and unit.engaged_with.is_heavy_unit():
        return False

    # Otherwise defer to unit-specific breakaway rules
    if unit.engaged_with and hasattr(unit, 'can_break_away_from'):
        return unit.can_break_away_from(unit.engaged_with)

    return True
```

(See `game/behaviors/movement.py` lines 236-265.)

## Tactical Implications

- A unit moving from outside enemy ZOC must stop on the first threatened tile it enters unless it attacks the occupying enemy.
- Once in ZOC, movement costs increase and available destinations become severely limited unless the unit can disengage.
- The ZOC check considers all eight adjacent hexes, so diagonal positioning also exerts control.
- Routing units ignore ZOC when fleeing, and units with morale below 25 never project ZOC themselves.

## Visual Indicators

During rendering, units with ZOC have the neighboring hexes highlighted so players can see which tiles are threatened.

## Summary

Zone of Control is applied automatically each update. A unit with at least 25 morale that is not routing controls all adjacent tiles. Entering these tiles is allowed, but leaving them without a valid disengagement option costs extra AP and may only allow attacking the enemy exerting the control.
Approaching an enemy will therefore halt the unit on the first tile within that enemy's ZOC unless the path ends on the enemy's position.

