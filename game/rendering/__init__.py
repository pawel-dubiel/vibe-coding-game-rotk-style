"""
Rendering module with focused, specialized renderers.

This module splits the monolithic Renderer class into specialized components
with single responsibilities, improving maintainability and testability.
"""

from .core_renderer import CoreRenderer
from .terrain_renderer import TerrainRenderer
from .unit_renderer import UnitRenderer
from .ui_renderer import UIRenderer
from .effect_renderer import EffectRenderer

__all__ = ['CoreRenderer', 'TerrainRenderer', 'UnitRenderer', 'UIRenderer', 'EffectRenderer']