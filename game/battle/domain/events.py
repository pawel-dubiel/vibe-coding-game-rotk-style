"""Battle domain events."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UnitMoved:
    unit_id: int
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    path: list[tuple[int, int]]
    ap_spent: int
    final_face_target: Optional[tuple[int, int]] = None
    use_path_animation: bool = True


@dataclass(frozen=True)
class AttackResolved:
    attacker_id: int
    target_id: int
    damage: int
    counter_damage: int
    attack_angle: Optional[object]
    extra_morale_penalty: int
    extra_cohesion_penalty: int
    should_check_routing: bool


@dataclass(frozen=True)
class ChargeResolved:
    attacker_id: int
    target_id: int
    attacker_from: tuple[int, int]
    attacker_to: Optional[tuple[int, int]]
    message: str
