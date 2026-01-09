import pygame
import math
from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
from game.entities.knight import KnightClass

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
        self.progress = self.get_progress()
        # Update knight's actual position when animation completes
        if self.finished and not self.position_updated:
            self.knight.x = self.end_x
            self.knight.y = self.end_y
            
            # Update facing based on movement direction
            if hasattr(self.knight, 'facing'):
                self.knight.facing.update_facing_from_movement(self.start_x, self.start_y, self.end_x, self.end_y)
                
            self.position_updated = True
            
            # Check cavalry disruption after movement
            if self.game_state:
                check_cavalry_disruption_for_terrain(self.knight, self.game_state)
            
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

class PathMoveAnimation(Animation):
    def __init__(self, knight, path, step_duration=0.3, game_state=None, final_face_target=None):
        """Animation that follows a multi-step path"""
        total_duration = len(path) * step_duration if path else 0
        super().__init__(total_duration)
        self.knight = knight
        self.path = path  # List of (x, y) positions to move through
        self.step_duration = step_duration
        self.current_step = 0
        self.position_updated = False
        self.game_state = game_state
        self.last_completed_step = -1
        self.final_face_target = final_face_target
        
        # Store the initial position
        self.start_x = knight.x
        self.start_y = knight.y
    
    def update(self, dt):
        super().update(dt)
        
        # Update facing as we reach each step
        if self.path and hasattr(self.knight, 'facing'):
            progress = self.get_progress()
            total_steps = len(self.path)
            
            # Handle instant completion or large jumps
            if self.finished:
                # If we have an explicit target to face, use it
                if self.final_face_target:
                    target_x, target_y = self.final_face_target
                    # Current pos is end of path
                    curr_x, curr_y = self.path[-1]
                    self.knight.facing.face_towards(target_x, target_y, curr_x, curr_y)
                else:
                    # Force update to final facing based on last segment
                    if total_steps > 0:
                        if total_steps == 1:
                            from_x, from_y = self.start_x, self.start_y
                        else:
                            from_x, from_y = self.path[-2]
                        
                        to_x, to_y = self.path[-1]
                        self.knight.facing.update_facing_from_movement(from_x, from_y, to_x, to_y)
            else:
                # Normal incremental update
                current_step_float = progress * total_steps
                current_step = int(current_step_float)
                
                # Update facing when we complete a step
                if current_step > self.last_completed_step and current_step < total_steps:
                    # Get positions for facing update
                    if self.last_completed_step < 0:
                        from_x, from_y = self.start_x, self.start_y
                    else:
                        from_x, from_y = self.path[self.last_completed_step]
                        
                    to_x, to_y = self.path[current_step]
                    
                    # Update facing
                    self.knight.facing.update_facing_from_movement(from_x, from_y, to_x, to_y)
                    self.last_completed_step = current_step
        
        # Update knight's actual position when animation completes
        if self.finished and not self.position_updated:
            if self.path:
                final_x, final_y = self.path[-1]
                self.knight.x = final_x
                self.knight.y = final_y
            self.position_updated = True
            
            # Check cavalry disruption after movement
            if self.game_state:
                check_cavalry_disruption_for_terrain(self.knight, self.game_state)
            
            # Clear pending position if game_state is available
            if self.game_state and id(self.knight) in self.game_state.pending_positions:
                del self.game_state.pending_positions[id(self.knight)]
        
        return not self.finished
    
    def get_current_position(self):
        if not self.path:
            return self.start_x, self.start_y
            
        progress = self.get_progress()
        total_steps = len(self.path)
        
        # Calculate which step we're currently on
        current_step_float = progress * total_steps
        current_step = int(current_step_float)
        step_progress = current_step_float - current_step
        
        # Apply easing to step progress
        step_progress = self._ease_in_out(step_progress)
        
        # Determine start and end positions for current step
        if current_step == 0:
            start_x, start_y = self.start_x, self.start_y
        else:
            start_x, start_y = self.path[current_step - 1]
            
        if current_step >= len(self.path):
            # Animation finished, stay at final position
            return self.path[-1]
        else:
            end_x, end_y = self.path[current_step]
        
        # Interpolate between start and end of current step
        current_x = start_x + (end_x - start_x) * step_progress
        current_y = start_y + (end_y - start_y) * step_progress
        
        return current_x, current_y
    
    def _ease_in_out(self, t):
        return t * t * (3.0 - 2.0 * t)

class AttackAnimation(Animation):
    def __init__(self, attacker, target, damage, counter_damage=0, duration=0.8,
                 attack_angle=None, extra_morale_penalty=0, extra_cohesion_penalty=0,
                 should_check_routing=False, game_state=None, is_ranged=False):
        super().__init__(duration)
        if game_state is None:
            raise ValueError("game_state is required for attack animations")
        self.attacker = attacker
        self.target = target
        self.damage = damage
        self.counter_damage = counter_damage
        self.shake_intensity = 10
        self.damage_applied = False
        self.attack_angle = attack_angle
        self.extra_morale_penalty = extra_morale_penalty
        self.extra_cohesion_penalty = extra_cohesion_penalty
        self.should_check_routing = should_check_routing
        self.game_state = game_state
        # Determine if this should be rendered as a ranged attack
        self.is_ranged = is_ranged or getattr(attacker, "knight_class", None) == KnightClass.ARCHER
        self.progress = 0.0
    
    def update(self, dt):
        super().update(dt)
        self.progress = self.get_progress()
        # Apply casualties when projectile hits (at 50% progress)
        progress = self.progress
        if progress >= 0.5 and not self.damage_applied:
            # Calculate casualties before applying
            initial_soldiers = self.target.soldiers
            initial_morale = self.target.morale
            was_routing_before = self.target.is_routing
            
            # Apply damage (this will trigger automatic routing checks)
            self.target.take_casualties(self.damage, self.game_state)
            casualties_taken = initial_soldiers - self.target.soldiers
            
            # Apply extra morale/cohesion penalties for shock attacks
            if self.extra_morale_penalty > 0:
                self.target.morale = max(0, self.target.morale - self.extra_morale_penalty)
            if self.extra_cohesion_penalty > 0 and hasattr(self.target, 'cohesion'):
                self.target.cohesion = max(0, self.target.cohesion - self.extra_cohesion_penalty)

            if self.should_check_routing and not self.target.is_routing:
                shock_bonus = self.extra_morale_penalty + self.extra_cohesion_penalty
                self.target.check_routing(self.game_state, shock_bonus=shock_bonus)
            
            # Add routing message if unit just started routing
            if not was_routing_before and self.target.is_routing:
                if self.game_state:
                    self.game_state.add_message(f"{self.target.name} breaks and starts routing!", priority=2)
            
            # Apply counter damage to attacker if melee (this can also cause routing)
            if self.counter_damage > 0:
                attacker_initial_morale = self.attacker.morale
                was_attacker_routing = self.attacker.is_routing
                self.attacker.take_casualties(self.counter_damage, self.game_state)
                
                # Message if attacker starts routing from counter-attack
                if not was_attacker_routing and self.attacker.is_routing:
                    if self.game_state:
                        self.game_state.add_message(f"{self.attacker.name} breaks from counter-attack!", priority=2)
                        
            self.damage_applied = True
        return not self.finished

    def get_current_arrow_position(self):
        """Return arrow position for ranged attacks before impact."""
        if not self.is_ranged:
            return None
        if self.progress >= 0.5:
            return None
        arrow_progress = self.progress * 2
        x = self.attacker.x + (self.target.x - self.attacker.x) * arrow_progress
        y = self.attacker.y + (self.target.y - self.attacker.y) * arrow_progress
        return x, y
    
    def get_effect_position(self):
        progress = self.progress
        
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
    def __init__(self, castle, targets, damages, duration=1.0, game_state=None):
        super().__init__(duration)
        if game_state is None:
            raise ValueError("game_state is required for arrow animations")
        self.castle = castle
        self.targets = targets
        self.damages = damages
        self.game_state = game_state
        self.arrow_speed = 0.4
        self.damage_applied = False
    
    def update(self, dt):
        super().update(dt)
        # Apply casualties when arrows hit
        progress = self.get_progress()
        if progress >= self.arrow_speed and not self.damage_applied:
            for target, casualties in zip(self.targets, self.damages):
                target.take_casualties(casualties, self.game_state)
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
