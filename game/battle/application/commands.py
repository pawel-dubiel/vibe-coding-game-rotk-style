"""Battle commands."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MoveUnitCommand:
    unit_id: int
    to_x: int
    to_y: int


@dataclass(frozen=True)
class AttackUnitCommand:
    attacker_id: int
    target_x: int
    target_y: int
    enforce_visibility: bool = False


@dataclass(frozen=True)
class ChargeUnitCommand:
    attacker_id: int
    target_x: int
    target_y: int
