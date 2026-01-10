"""Movement rules for battle actions."""
from __future__ import annotations

from typing import Optional


class MovementRules:
    @staticmethod
    def resolve_move(unit, target_x: int, target_y: int, game_state) -> Optional[dict]:
        if unit is None:
            raise ValueError("unit is required for movement resolution")
        if game_state is None:
            raise ValueError("game_state is required for movement resolution")

        move_behavior = unit.behaviors.get('move') if hasattr(unit, 'behaviors') else None
        if move_behavior:
            possible_moves = move_behavior.get_possible_moves(unit, game_state)
            if (target_x, target_y) not in possible_moves:
                return None

            path = move_behavior.get_path_to(unit, game_state, target_x, target_y)
            if not path:
                return None

            total_ap_cost = 0
            current_pos = (unit.x, unit.y)
            for next_pos in path:
                step_cost = move_behavior.get_ap_cost(current_pos, next_pos, unit, game_state)
                total_ap_cost += step_cost
                current_pos = next_pos

            if unit.action_points < total_ap_cost:
                return None

            final_face_target = move_behavior.get_auto_face_target(
                unit,
                game_state,
                target_x,
                target_y,
            )

            return {
                'path': path,
                'ap_spent': total_ap_cost,
                'final_face_target': final_face_target,
                'use_path_animation': True,
            }

        if unit.action_points < 1 or getattr(unit, 'has_moved', False):
            return None

        return {
            'path': [],
            'ap_spent': 1,
            'final_face_target': None,
            'use_path_animation': False,
        }
