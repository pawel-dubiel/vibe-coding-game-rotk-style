"""Interface for battle rule context."""
from __future__ import annotations

from typing import Protocol


class BattleContext(Protocol):
    board_width: int
    board_height: int
    knights: list
    terrain_map: object
    fog_of_war: object
    current_player: int

    def get_unit_by_id(self, unit_id: int):
        raise NotImplementedError

    def get_unit_at(self, x: int, y: int):
        raise NotImplementedError
