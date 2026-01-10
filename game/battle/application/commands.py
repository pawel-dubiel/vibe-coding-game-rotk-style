"""Battle commands."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MoveUnitCommand:
    unit_id: int
    to_x: int
    to_y: int
