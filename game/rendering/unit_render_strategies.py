from __future__ import annotations

from abc import ABC, abstractmethod
import pygame
from game.components.facing import FacingDirection


class UnitRenderStrategy(ABC):
    """Interface for rendering different unit types."""

    @abstractmethod
    def render(self, screen: pygame.Surface, unit, asset_manager, center_x: int, center_y: int) -> None:
        """Render the unit sprite to the screen."""
        raise NotImplementedError
        
    def _render_icon(self, screen, unit, asset_manager, center_x, center_y, size=50):
        """Helper to render icon with rotation"""
        if not hasattr(unit, 'facing') or not unit.facing:
            facing_angle = 0
        else:
            facing_angles = {
                FacingDirection.EAST: 0,
                FacingDirection.SOUTH_EAST: 60,
                FacingDirection.SOUTH_WEST: 120,
                FacingDirection.WEST: 180,
                FacingDirection.NORTH_WEST: 240,
                FacingDirection.NORTH_EAST: 300
            }
            facing_angle = facing_angles.get(unit.facing.facing, 0)
            
        icon = asset_manager.get_unit_icon(unit.unit_class.name, unit.player_id, facing_angle, size)
        
        if icon:
            rect = icon.get_rect(center=(center_x, center_y))
            screen.blit(icon, rect)
            return True
        return False


class WarriorRenderStrategy(UnitRenderStrategy):
    """Render strategy for warriors."""

    def render(self, screen: pygame.Surface, unit, asset_manager, center_x: int, center_y: int) -> None:
        if self._render_icon(screen, unit, asset_manager, center_x, center_y):
            return
            
        # Fallback
        color = (100, 100, 255) if unit.player_id == 1 else (255, 100, 100)
        pygame.draw.rect(screen, color, (center_x - 20, center_y - 20, 40, 40))
        pygame.draw.rect(screen, (0, 0, 0), (center_x - 20, center_y - 20, 40, 40), 2)


class ArcherRenderStrategy(UnitRenderStrategy):
    """Render strategy for archers."""

    def render(self, screen: pygame.Surface, unit, asset_manager, center_x: int, center_y: int) -> None:
        if self._render_icon(screen, unit, asset_manager, center_x, center_y):
            return

        # Fallback
        color = (100, 100, 255) if unit.player_id == 1 else (255, 100, 100)
        pygame.draw.polygon(
            screen,
            color,
            [(center_x, center_y - 25), (center_x - 20, center_y + 20), (center_x + 20, center_y + 20)],
        )
        pygame.draw.polygon(
            screen,
            (0, 0, 0),
            [(center_x, center_y - 25), (center_x - 20, center_y + 20), (center_x + 20, center_y + 20)],
            2,
        )


class CavalryRenderStrategy(UnitRenderStrategy):
    """Render strategy for cavalry."""

    def render(self, screen: pygame.Surface, unit, asset_manager, center_x: int, center_y: int) -> None:
        if self._render_icon(screen, unit, asset_manager, center_x, center_y, size=60): # Slightly larger
            return

        # Fallback
        color = (100, 100, 255) if unit.player_id == 1 else (255, 100, 100)
        pygame.draw.ellipse(screen, color, (center_x - 25, center_y - 15, 50, 30))
        pygame.draw.ellipse(screen, (0, 0, 0), (center_x - 25, center_y - 15, 50, 30), 2)


class MageRenderStrategy(UnitRenderStrategy):
    """Render strategy for mages."""

    def render(self, screen: pygame.Surface, unit, asset_manager, center_x: int, center_y: int) -> None:
        if self._render_icon(screen, unit, asset_manager, center_x, center_y):
            return

        # Fallback
        color = (100, 100, 255) if unit.player_id == 1 else (255, 100, 100)
        pygame.draw.circle(screen, color, (center_x, center_y), 22)
        pygame.draw.circle(screen, (0, 0, 0), (center_x, center_y), 22, 2)