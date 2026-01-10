"""Battle command handlers."""
from __future__ import annotations

from game.battle.domain.events import UnitMoved
from game.battle.domain.services.movement_rules import MovementRules


class MoveUnitHandler:
    def __init__(self, game_state, event_sink):
        if game_state is None:
            raise ValueError("game_state is required for MoveUnitHandler")
        if event_sink is None:
            raise ValueError("event_sink is required for MoveUnitHandler")
        self._game_state = game_state
        self._event_sink = event_sink

    def handle(self, command) -> bool:
        if command is None:
            raise ValueError("command is required for MoveUnitHandler")

        unit = self._game_state.get_unit_by_id(command.unit_id)
        if unit is None:
            raise ValueError(f"unit_id not found: {command.unit_id}")

        move_result = MovementRules.resolve_move(
            unit,
            command.to_x,
            command.to_y,
            self._game_state,
        )
        if not move_result:
            return False

        unit.action_points -= move_result['ap_spent']
        unit.has_moved = True

        from_x, from_y = unit.x, unit.y
        path = move_result['path']
        event = UnitMoved(
            unit_id=id(unit),
            from_x=from_x,
            from_y=from_y,
            to_x=command.to_x,
            to_y=command.to_y,
            path=path,
            ap_spent=move_result['ap_spent'],
            final_face_target=move_result['final_face_target'],
            use_path_animation=move_result['use_path_animation'],
        )
        self._event_sink.publish(event)
        return True
