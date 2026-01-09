# Auto-Facing and Fog of War Behavior

This document describes the intended behavior for auto-facing when units move, and how fog of war visibility is revealed and used during that decision.

## Goals

- Moving adjacent to an enemy should auto-face the enemy if the enemy is visible from the destination.
- Moving near a hidden enemy should reveal it once the unit's vision covers that tile.
- Auto-facing should not leak information about enemies still hidden by fog.

## Terminology

- "Visible" means the unit can identify enemy details (VisibilityState.VISIBLE).
- "Partial" means the unit can see that a unit exists but not its details (VisibilityState.PARTIAL).
- "Explored" means terrain is known but units are not visible (VisibilityState.EXPLORED).
- "Hidden" means never seen (VisibilityState.HIDDEN).

## Movement Flow

1. Unit performs a move to (target_x, target_y).
2. Fog of war is updated for that unit only, using its vision range and line of sight.
3. Auto-facing checks run using projected visibility from the destination, not the old fog map.
4. If a valid target is found, the unit faces the selected enemy.
5. Otherwise, facing falls back to movement direction or manual facing if provided.

## Reveal Behavior

- After a move completes, the unit's vision reveals tiles around the destination.
- Reveals upgrade visibility only (HIDDEN -> EXPLORED/PARTIAL/VISIBLE). Existing visibility never downgrades here.
- Visibility is determined by the unit's vision behavior, terrain, and line of sight.

## Auto-Facing Rules

- Auto-facing triggers only for adjacent enemies (distance 1 in hex space).
- An adjacent enemy is a valid auto-face candidate only if:
  - The enemy is currently VISIBLE or PARTIAL to the viewer, or
  - The enemy would be VISIBLE or PARTIAL when visibility is projected from the destination.
- If multiple adjacent enemies are valid, choose the nearest; if tied, use threat priority:
  - Cavalry > Warrior > Mage > Archer.
- Routing units still follow existing rules (no auto-face changes here).

## Viewer Perspective

- The visibility check uses the current viewing player (fog_view_player if set, otherwise current_player).
- If a fog system exists but the viewer player is missing, the code fails fast with a clear error.

## Fail-Fast Contract

The following are treated as explicit errors and should raise ValueError:

- Missing game_state or unit when calculating visibility.
- Missing unit.player_id for reveal logic.
- Unknown player_id in fog visibility maps.
- Origin/target out of board bounds for projected visibility.
- fog_view_player is present but None while fog is enabled.

## Example Scenarios

- Move adjacent to a hidden enemy within vision range:
  - Enemy becomes visible and can be auto-faced.
- Move adjacent to a hidden enemy outside vision range:
  - Enemy stays hidden and is not auto-faced.
- Move near a hidden enemy but end the move out of adjacency:
  - Enemy can become visible, but auto-face does not trigger (adjacency required).

## Testing Notes

- Validate that hidden enemies become visible when a unit moves adjacent within vision.
- Validate that auto-facing does not occur for hidden enemies outside vision.
- Validate threat priority when multiple adjacent enemies are visible.
