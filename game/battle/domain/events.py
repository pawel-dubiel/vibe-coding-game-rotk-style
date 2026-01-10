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
