"""
Game state management module.

This module contains the refactored game state components, splitting the monolithic
GameState class into focused, testable modules with single responsibilities.
"""

from .message_system import MessageSystem
from .camera_manager import CameraManager
from .victory_manager import VictoryManager
from .state_serializer import StateSerializer
from .animation_coordinator import AnimationCoordinator
from .battle_state import BattleState, EndTurnResult
from .presentation_state import PresentationState

__all__ = [
    'MessageSystem',
    'CameraManager',
    'VictoryManager',
    'StateSerializer',
    'AnimationCoordinator',
    'BattleState',
    'EndTurnResult',
    'PresentationState',
]
