"""Interface for handling domain events."""
from __future__ import annotations

from typing import Protocol


class EventSink(Protocol):
    def publish(self, event) -> None:
        raise NotImplementedError
