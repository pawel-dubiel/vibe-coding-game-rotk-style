"""
Animation coordination and management system.

Handles animation lifecycle, timing, and integration with game state updates.
Extracted from GameState for better separation of animation logic from game logic.
"""
from game.animation import AnimationManager, MoveAnimation, AttackAnimation, ArrowAnimation, PathMoveAnimation


class AnimationCoordinator:
    """Coordinates animations with game state updates and user input."""
    
    def __init__(self):
        self.animation_manager = AnimationManager()
        self._block_input_during_animations = True
    
    def update(self, dt: float) -> None:
        """Update all active animations."""
        self.animation_manager.update(dt)
    
    def is_animating(self) -> bool:
        """Check if any animations are currently playing."""
        return self.animation_manager.is_animating()
    
    def should_block_input(self) -> bool:
        """Check if input should be blocked due to animations."""
        return self._block_input_during_animations and self.is_animating()
    
    def clear_animations(self) -> None:
        """Clear all active animations."""
        self.animation_manager.animations.clear()
    
    def create_move_animation(self, unit, start_pos: tuple, end_pos: tuple, duration: float = 0.5) -> MoveAnimation:
        """Create and add a movement animation."""
        anim = MoveAnimation(unit, start_pos, end_pos, duration)
        self.animation_manager.add_animation(anim)
        return anim
    
    def create_path_animation(self, unit, path: list, move_duration: float = 0.5) -> PathMoveAnimation:
        """Create and add a path movement animation showing the optimal route."""
        anim = PathMoveAnimation(unit, path, move_duration)
        self.animation_manager.add_animation(anim)
        return anim
    
    def create_attack_animation(self, attacker, target, duration: float = 0.3) -> AttackAnimation:
        """Create and add an attack animation."""
        anim = AttackAnimation(attacker, target, duration)
        self.animation_manager.add_animation(anim)
        return anim
    
    def create_arrow_animation(self, archer, target, damage: int, duration: float = 0.8) -> ArrowAnimation:
        """Create and add an arrow attack animation."""
        anim = ArrowAnimation(archer, target, damage, duration)
        self.animation_manager.add_animation(anim)
        return anim
    
    def create_charge_animation(self, cavalry_unit, start_pos: tuple, end_pos: tuple, duration: float = 0.7) -> MoveAnimation:
        """Create and add a cavalry charge animation (faster movement)."""
        anim = MoveAnimation(cavalry_unit, start_pos, end_pos, duration)
        self.animation_manager.add_animation(anim)
        return anim
    
    def set_input_blocking(self, should_block: bool) -> None:
        """Configure whether animations should block user input."""
        self._block_input_during_animations = should_block
    
    def get_active_animation_count(self) -> int:
        """Get the number of currently active animations."""
        return len(self.animation_manager.animations)
    
    def has_animation_type(self, animation_type: type) -> bool:
        """Check if there are any animations of a specific type active."""
        return any(isinstance(anim, animation_type) for anim in self.animation_manager.animations)