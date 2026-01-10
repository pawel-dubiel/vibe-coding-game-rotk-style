"""Battle context adapter for existing state objects."""
from __future__ import annotations


class BattleContextAdapter:
    def __init__(self, battle_state, fog_view_player: int | None = None):
        if battle_state is None:
            raise ValueError("battle_state is required for BattleContextAdapter")
        self._battle_state = battle_state
        self.fog_view_player = fog_view_player

    @property
    def board_width(self) -> int:
        return self._battle_state.board_width

    @property
    def board_height(self) -> int:
        return self._battle_state.board_height

    @property
    def knights(self):
        return self._battle_state.knights

    @property
    def castles(self):
        return self._battle_state.castles

    @property
    def terrain_map(self):
        return self._battle_state.terrain_map

    @property
    def fog_of_war(self):
        return self._battle_state.fog_of_war

    @property
    def current_player(self) -> int:
        return self._battle_state.current_player

    def get_unit_by_id(self, unit_id: int):
        for unit in self._battle_state.knights:
            if id(unit) == unit_id:
                return unit
        return None

    def get_unit_at(self, x: int, y: int):
        return self._battle_state.get_unit_at(x, y)

    def get_knight_at(self, x: int, y: int):
        return self._battle_state.get_knight_at(x, y)
