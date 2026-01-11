"""Centralized engagement and Zone of Control logic."""
from typing import Optional, Tuple


class EngagementSystem:
    """Utility class for ZOC and engagement state updates."""

    @staticmethod
    def _are_adjacent(unit, enemy) -> bool:
        EngagementSystem._validate_unit(unit)
        EngagementSystem._validate_unit(enemy)
        dx = abs(unit.x - enemy.x)
        dy = abs(unit.y - enemy.y)
        return dx <= 1 and dy <= 1 and (dx + dy > 0)

    @staticmethod
    def _clear_engagement(unit, enemy=None) -> None:
        unit.is_engaged_in_combat = False
        unit.engaged_with = None
        if enemy is not None and getattr(enemy, 'engaged_with', None) is unit:
            enemy.is_engaged_in_combat = False
            enemy.engaged_with = None

    @staticmethod
    def _validate_game_state(game_state) -> None:
        if game_state is None:
            raise ValueError("game_state is required for engagement checks")
        if not hasattr(game_state, 'knights'):
            raise ValueError("game_state.knights is required for engagement checks")

    @staticmethod
    def _validate_unit(unit) -> None:
        if unit is None:
            raise ValueError("unit is required for engagement checks")
        for attr in ('player_id', 'x', 'y'):
            if not hasattr(unit, attr):
                raise ValueError(f"unit.{attr} is required for engagement checks")

    @classmethod
    def is_tile_in_enemy_zoc(cls, tile_x: int, tile_y: int, unit, game_state) -> Tuple[bool, Optional[object]]:
        """Return whether a tile is inside enemy ZOC and the first enemy found."""
        cls._validate_game_state(game_state)
        cls._validate_unit(unit)
        if tile_x is None or tile_y is None:
            raise ValueError("tile coordinates are required for ZOC checks")

        for enemy in game_state.knights:
            if enemy.player_id != unit.player_id and enemy.has_zone_of_control():
                dx = abs(tile_x - enemy.x)
                dy = abs(tile_y - enemy.y)
                if dx <= 1 and dy <= 1 and (dx + dy > 0):
                    return True, enemy
        return False, None

    @classmethod
    def is_unit_in_enemy_zoc(cls, unit, game_state) -> Tuple[bool, Optional[object]]:
        """Return whether a unit is in enemy ZOC and the first enemy found."""
        cls._validate_game_state(game_state)
        cls._validate_unit(unit)
        return cls.is_tile_in_enemy_zoc(unit.x, unit.y, unit, game_state)

    @classmethod
    def update_zoc_and_engagement(cls, game_state) -> None:
        """Update ZOC and engagement flags for all units."""
        cls._validate_game_state(game_state)

        for unit in game_state.knights:
            in_zoc, enemy = cls.is_unit_in_enemy_zoc(unit, game_state)
            unit.in_enemy_zoc = in_zoc
            unit.zoc_enemy = enemy if in_zoc else None

            if unit.is_engaged_in_combat:
                if unit.engaged_with is None:
                    cls._clear_engagement(unit)
                    continue
                if unit.engaged_with not in game_state.knights:
                    cls._clear_engagement(unit, unit.engaged_with)
                    continue
                if not cls._are_adjacent(unit, unit.engaged_with):
                    cls._clear_engagement(unit, unit.engaged_with)
            elif unit.engaged_with is not None:
                unit.engaged_with = None
