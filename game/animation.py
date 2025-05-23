import pygame
import math

class Animation:
    def __init__(self, duration):
        self.duration = duration
        self.elapsed = 0
        self.finished = False
    
    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.finished = True
        return not self.finished
    
    def get_progress(self):
        return min(1.0, self.elapsed / self.duration)

class MoveAnimation(Animation):
    def __init__(self, knight, start_x, start_y, end_x, end_y, duration=0.5, game_state=None):
        super().__init__(duration)
        self.knight = knight
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.position_updated = False
        self.game_state = game_state
    
    def update(self, dt):
        super().update(dt)
        # Update knight's actual position when animation completes
        if self.finished and not self.position_updated:
            self.knight.x = self.end_x
            self.knight.y = self.end_y
            self.position_updated = True
            
            # Clear pending position if game_state is available
            if self.game_state and id(self.knight) in self.game_state.pending_positions:
                del self.game_state.pending_positions[id(self.knight)]
        return not self.finished
    
    def get_current_position(self):
        progress = self.get_progress()
        # Use easing function for smooth movement
        progress = self._ease_in_out(progress)
        
        current_x = self.start_x + (self.end_x - self.start_x) * progress
        current_y = self.start_y + (self.end_y - self.start_y) * progress
        return current_x, current_y
    
    def _ease_in_out(self, t):
        return t * t * (3.0 - 2.0 * t)

class AttackAnimation(Animation):
    def __init__(self, attacker, target, damage, counter_damage=0, duration=0.8):
        super().__init__(duration)
        self.attacker = attacker
        self.target = target
        self.damage = damage
        self.counter_damage = counter_damage
        self.shake_intensity = 10
        self.damage_applied = False
    
    def update(self, dt):
        super().update(dt)
        # Apply casualties when projectile hits (at 50% progress)
        progress = self.get_progress()
        if progress >= 0.5 and not self.damage_applied:
            self.target.take_casualties(self.damage)
            # Apply counter damage to attacker if melee
            if self.counter_damage > 0:
                self.attacker.take_casualties(self.counter_damage)
            self.damage_applied = True
        return not self.finished
    
    def get_effect_position(self):
        progress = self.get_progress()
        
        # Attack effect moves from attacker to target
        if progress < 0.5:
            # Move towards target
            effect_progress = progress * 2
            x = self.attacker.x + (self.target.x - self.attacker.x) * effect_progress
            y = self.attacker.y + (self.target.y - self.attacker.y) * effect_progress
            return x, y, False
        else:
            # Shake target
            shake_progress = (progress - 0.5) * 2
            shake_x = math.sin(shake_progress * math.pi * 4) * self.shake_intensity * (1 - shake_progress)
            shake_y = math.cos(shake_progress * math.pi * 4) * self.shake_intensity * (1 - shake_progress)
            return self.target.x, self.target.y, True, shake_x, shake_y

class ArrowAnimation(Animation):
    def __init__(self, castle, targets, damages, duration=1.0):
        super().__init__(duration)
        self.castle = castle
        self.targets = targets
        self.damages = damages
        self.arrow_speed = 0.4
        self.damage_applied = False
    
    def update(self, dt):
        super().update(dt)
        # Apply casualties when arrows hit
        progress = self.get_progress()
        if progress >= self.arrow_speed and not self.damage_applied:
            for target, casualties in zip(self.targets, self.damages):
                target.take_casualties(casualties)
            self.damage_applied = True
        return not self.finished
    
    def get_arrow_positions(self):
        progress = self.get_progress()
        arrows = []
        
        if progress < self.arrow_speed:
            # Arrows flying
            arrow_progress = progress / self.arrow_speed
            for target in self.targets:
                x = self.castle.center_x + (target.x - self.castle.center_x) * arrow_progress
                y = self.castle.center_y + (target.y - self.castle.center_y) * arrow_progress
                arrows.append((x, y))
        
        return arrows, progress >= self.arrow_speed

class AnimationManager:
    def __init__(self):
        self.animations = []
        self.pending_animations = []
        self.death_callbacks = []
    
    def add_animation(self, animation):
        self.pending_animations.append(animation)
    
    def update(self, dt):
        # Add pending animations
        if not self.animations and self.pending_animations:
            self.animations.append(self.pending_animations.pop(0))
        
        # Update current animations
        self.animations = [anim for anim in self.animations if anim.update(dt)]
        
        # Add next pending animation if current finished
        if not self.animations and self.pending_animations:
            self.animations.append(self.pending_animations.pop(0))
    
    def is_animating(self):
        return len(self.animations) > 0 or len(self.pending_animations) > 0
    
    def get_current_animations(self):
        return self.animations
    
    def clear(self):
        self.animations.clear()
        self.pending_animations.clear()