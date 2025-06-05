from __future__ import annotations

from abc import ABC, abstractmethod
import pygame


class UnitRenderStrategy(ABC):
    """Interface for rendering different unit types."""

    @abstractmethod
    def render(self, screen: pygame.Surface, player_color: tuple[int, int, int], center_x: int, center_y: int) -> None:
        """Render the unit sprite to the screen."""
        raise NotImplementedError


class WarriorRenderStrategy(UnitRenderStrategy):
    """Render strategy for warriors."""

    def render(self, screen: pygame.Surface, player_color: tuple[int, int, int], center_x: int, center_y: int) -> None:
        pygame.draw.rect(screen, player_color, (center_x - 20, center_y - 20, 40, 40))
        pygame.draw.rect(screen, (0, 0, 0), (center_x - 20, center_y - 20, 40, 40), 2)


class ArcherRenderStrategy(UnitRenderStrategy):
    """Render strategy for archers."""

    def render(self, screen: pygame.Surface, player_color: tuple[int, int, int], center_x: int, center_y: int) -> None:
        pygame.draw.polygon(
            screen,
            player_color,
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

    def render(self, screen: pygame.Surface, player_color: tuple[int, int, int], center_x: int, center_y: int) -> None:
        pygame.draw.ellipse(screen, player_color, (center_x - 25, center_y - 15, 50, 30))
        pygame.draw.ellipse(screen, (0, 0, 0), (center_x - 25, center_y - 15, 50, 30), 2)


class MageRenderStrategy(UnitRenderStrategy):
    """Render strategy for mages."""

    def render(self, screen: pygame.Surface, player_color: tuple[int, int, int], center_x: int, center_y: int) -> None:
        pygame.draw.circle(screen, player_color, (center_x, center_y), 22)
        pygame.draw.circle(screen, (0, 0, 0), (center_x, center_y), 22, 2)
