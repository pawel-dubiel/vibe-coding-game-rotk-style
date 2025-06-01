# Routing Mechanism Documentation

## Overview

The routing system in Castle Knights simulates the psychological breaking point of units under combat stress. When units suffer heavy casualties, sustained attacks, or are hit from vulnerable angles, they may break and flee the battlefield until they can rally and return to the fight.

## Core Mechanics

### Routing State

Units have an `is_routing` boolean property (`game/entities/unit.py:54`) that tracks whether they are currently fleeing.

```python
@property
def is_routing(self) -> bool:
    """Check if unit is currently routing"""
    return getattr(self, '_is_routing', False)

@is_routing.setter
def is_routing(self, value: bool):
    """Set routing state with appropriate side effects"""
    self._is_routing = value
    if value:
        # Unit starts routing - update any dependent states
        self.is_engaged_in_combat = False
        self.engaged_with = None
```

### Routing Triggers

#### Automatic Routing (Low Morale)

Units automatically start routing when their morale drops below critical thresholds:

```python
def check_routing(self) -> bool:
    """Check if unit should start routing based on morale and conditions"""
    if self.is_routing:
        return True
        
    # Units with very low morale start routing
    routing_threshold = 20  # Start routing below 20% morale
    
    if self.morale < routing_threshold:
        self.is_routing = True
        return True
        
    # Probability-based routing for moderate morale loss
    if self.morale < 40:  # Between 20-40% morale, chance to route
        route_chance = (40 - self.morale) / 40  # 0% at 40 morale, 50% at 20 morale
        if random.random() < route_chance * 0.3:  # Max 15% chance per check
            self.is_routing = True
            return True
            
    return False
```

#### Facing-Based Routing

Units are more likely to route when attacked from vulnerable angles:

**Rear Attacks** (`game/components/facing.py:154-193`):
```python
def check_routing_chance(self, attack_angle: AttackAngle, 
                       current_morale: float, casualties_percent: float) -> bool:
    """Check if unit should route based on attack angle and damage"""
    base_chance = 0
    
    if attack_angle.is_rear:
        # Rear attacks have high routing chance (40-60% based on casualties)
        if casualties_percent > 0.3:  # Lost 30% in one attack
            base_chance = 60
        elif casualties_percent > 0.2:  # Lost 20% in one attack
            base_chance = 40
        else:
            base_chance = 25
            
    elif attack_angle.is_flank:
        # Flank attacks have moderate routing chance (15-30%)
        if casualties_percent > 0.4:
            base_chance = 30
        elif casualties_percent > 0.3:
            base_chance = 20
        else:
            base_chance = 15
    
    # Morale affects routing chance
    morale_modifier = (100 - current_morale) / 100  # 0.0 at 100 morale, 1.0 at 0 morale
    final_chance = base_chance * (0.5 + morale_modifier)  # 50-150% of base chance
    
    return random.random() < (final_chance / 100)
```

**Morale Penalties by Attack Angle**:
- **Rear attacks**: -15 morale
- **Flank attacks**: -10 morale  
- **Front attacks**: -5 morale

### Morale Loss Sources

#### Combat Casualties
When units take damage, they lose morale proportional to casualties:

```python
def take_casualties(self, casualties: int, source: str = "combat"):
    """Apply casualties and check for routing"""
    old_soldiers = self.stats.stats.current_soldiers
    self.stats.stats.current_soldiers = max(0, self.stats.stats.current_soldiers - casualties)
    
    # Calculate casualty percentage for morale loss
    casualty_percent = casualties / max(old_soldiers, 1)
    morale_loss = min(30, casualty_percent * 50)  # Up to 30 morale loss
    
    # Apply morale loss and check routing
    self.stats.stats.morale = max(0, self.stats.stats.morale - morale_loss)
    
    if not self.is_routing:
        self.check_routing()
```

#### Multiple Attacks Per Turn
Progressive morale loss system for combat fatigue (`game/behaviors/combat.py:139-144`):

```python
# Apply morale loss for multiple attacks (combat fatigue)
if unit.attacks_this_turn > 1:
    # Progressive morale loss: 5% for second attack, 10% for third, etc.
    morale_loss = unit.attacks_this_turn * 5
    unit.stats.stats.morale = max(0, unit.stats.stats.morale - morale_loss)
```

#### Cavalry Charges
Charge targets suffer significant morale impact:

```python
def apply_charge_morale_effect(self, target, charge_type: str):
    """Apply morale loss from cavalry charge"""
    if charge_type == "flank_charge":
        morale_loss = 30
    elif charge_type == "rear_charge":
        morale_loss = 25
    else:
        morale_loss = 15  # Front charge
        
    target.stats.stats.morale = max(0, target.stats.stats.morale - morale_loss)
    target.check_routing()
```

## Effects of Routing

### Combat Behavior

**Reduced Damage Taken**:
Routing units are scattered and harder to target effectively:

```python
def calculate_damage_to_routing_unit(self, base_damage: int) -> int:
    """Routing units take reduced damage due to dispersal"""
    return int(base_damage * 0.7)  # 30% damage reduction
```

**No Zone of Control**:
Routing units cannot control territory or threaten enemies:

```python
def has_zone_of_control(self) -> bool:
    """Check if unit exerts zone of control"""
    if self.is_routing:
        return False
    if self.morale < 25:  # Need minimum morale for ZOC
        return False
    return True
```

### Movement Behavior

**Automatic Routing Movement** (`game/entities/unit.py:224-283`):
When units start routing, they **immediately and automatically** flee away from enemies:

```python
def _attempt_auto_routing_movement(self, game_state):
    """Attempt automatic routing movement away from enemies"""
    # Get routing movement options
    movement_behavior = self.get_behavior('MovementBehavior')
    routing_moves = movement_behavior._get_routing_moves(self, game_state)
    
    # Choose the best routing move (furthest from nearest enemy)
    enemies = [k for k in game_state.knights if k.player_id != self.player_id]
    nearest_enemy = min(enemies, key=lambda e: abs(e.x - self.x) + abs(e.y - self.y))
    
    # Find the move that gets furthest from nearest enemy
    best_move = max(routing_moves, key=lambda pos: abs(pos[0] - nearest_enemy.x) + abs(pos[1] - nearest_enemy.y))
    
    # Execute the routing movement immediately
    if best_move:
        self.x, self.y = best_move
        self.action_points = max(0, self.action_points - 1)  # Small AP cost
        game_state.add_message(f"{self.name} routs and flees!", priority=2)
        return True
```

**Routing Movement Options** (`game/behaviors/movement.py:299-327`):
The movement behavior provides valid flee directions:

```python
def _get_routing_moves(self, unit, game_state) -> List[Tuple[int, int]]:
    """Get movement options for routing units (away from enemies)"""
    moves = []
    enemies = [u for u in game_state.knights if u.player_id != unit.player_id]
    
    if not enemies:
        return self._get_basic_moves(unit, game_state)
    
    # Find nearest enemy
    nearest_enemy = min(enemies, key=lambda e: abs(e.x - unit.x) + abs(e.y - unit.y))
    
    # Check all 8 directions for routing
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
        new_x, new_y = unit.x + dx, unit.y + dy
        
        # Must be valid position
        if not game_state.is_valid_position(new_x, new_y):
            continue
            
        # Check if this moves away from nearest enemy
        current_dist = abs(unit.x - nearest_enemy.x) + abs(unit.y - nearest_enemy.y)
        new_dist = abs(new_x - nearest_enemy.x) + abs(new_y - nearest_enemy.y)
        
        if new_dist > current_dist:  # Only moves that increase distance
            moves.append((new_x, new_y))
    
    return moves
```

**ZOC Disengagement**:
Routing units can move through enemy zones of control without penalty:

```python
def can_disengage_from_zoc(self, unit) -> bool:
    """Check if unit can disengage from enemy ZOC"""
    if unit.is_routing:
        return True  # Routing units can always try to flee
    return False
```

## Rally and Recovery

### Automatic Rally

Units attempt to rally at the end of each turn:

```python
def attempt_rally(self) -> bool:
    """Try to rally and stop routing"""
    if not self.is_routing:
        return True
        
    # Need minimum morale to rally
    if self.stats.stats.morale < 40:
        return False
        
    # Base rally chance
    rally_chance = 0.7  # 70% base chance
    
    # Better chance with higher morale
    if self.stats.stats.morale >= 60:
        rally_chance = 0.9  # 90% chance with high morale
        
    # Reduced chance if heavily damaged
    soldier_ratio = self.soldiers / self.max_soldiers
    if soldier_ratio < 0.5:  # Less than 50% soldiers remaining
        rally_chance *= 0.6  # Harder to rally when heavily damaged
        
    if random.random() < rally_chance:
        self.is_routing = False
        self.has_rallied_this_turn = True
        return True
        
    return False
```

### Manual Rally (General Abilities)

**Rally Ability** (`game/components/generals.py:126-148`):
```python
class RallyAbility(GeneralAbility):
    """Active: Restore morale and remove routing status"""
    
    def __init__(self):
        super().__init__(
            name="Rally",
            description="Restore unit morale and remove routing status",
            ability_type=AbilityType.ACTIVE,
            will_cost=20,
            cooldown=3,
            range=2
        )
    
    def can_use(self, context: Dict[str, Any]) -> bool:
        """Check if rally can be used"""
        target = context.get('target')
        if not target:
            return False
            
        # Can only rally friendly units that are routing or have low morale
        return (target.player_id == context.get('caster').player_id and 
                (target.is_routing or target.morale < 60))
    
    def apply(self, unit: 'Unit', context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rally effect"""
        # Restore significant morale
        unit.stats.stats.morale = min(100, unit.stats.stats.morale + 30)
        
        # Remove routing status
        unit.is_routing = False
        
        return {
            'success': True,
            'message': f"{unit.name} rallies and stops routing!",
            'morale_restored': 30
        }
```

## Visual Indicators

### Routing Display

**Unit Status Icons** (`game/renderer.py:528-536`):
```python
def render_unit_status_icons(self, screen, unit, x, y):
    """Render status icons for units"""
    icon_y = y - 25
    
    if unit.is_routing:
        # White flag icon for routing
        routing_icon = self._get_routing_icon()
        screen.blit(routing_icon, (x - 10, icon_y))
        icon_y -= 15
```

**Status Text**:
```python
def get_unit_status_text(self, unit) -> str:
    """Get status text for unit display"""
    if unit.is_routing:
        return "ROUTING!"
    elif unit.morale < 25:
        return "SHAKEN"
    elif unit.morale < 50:
        return "WAVERING"
    return ""
```

### Animation Effects

**Routing Notifications** (`game/animation.py:184-219`):
```python
class RoutingAnimation(Animation):
    """Animation for unit starting to route"""
    
    def __init__(self, unit, message: str):
        super().__init__(duration=2000)  # 2 second animation
        self.unit = unit
        self.message = message
        
    def update(self, dt: float, game_state) -> bool:
        """Update routing animation"""
        if self.time_elapsed == 0:  # First frame
            game_state.add_message(f"{self.unit.name} breaks and starts routing!", priority=2)
            
        return super().update(dt, game_state)
```

## AI Integration

### AI Attack Evaluation

AI prioritizes attacking units likely to route:

```python
def _evaluate_attack_target(self, attacker, target):
    """Evaluate the value of attacking a target"""
    base_value = 50
    
    # Bonus for attacking low morale units (routing potential)
    if target.morale < 50:
        morale_bonus = (50 - target.morale) * 1.5  # Up to 75 bonus
        base_value += morale_bonus
        
    # Bonus for rear/flank attacks (higher routing chance)
    attack_angle = target.facing.get_attack_angle(attacker.x, attacker.y, target.x, target.y)
    if attack_angle.is_rear:
        base_value += 50  # High bonus for rear attacks
    elif attack_angle.is_flank:
        base_value += 25  # Moderate bonus for flank attacks
        
    return base_value
```

### AI Routing Response

AI adjusts strategy when units are routing:

```python
def _evaluate_unit_threat(self, unit):
    """Evaluate how threatening a unit is"""
    base_threat = unit.soldiers * unit.attack_strength
    
    if unit.is_routing:
        base_threat *= 0.3  # Routing units are much less threatening
    elif unit.morale < 25:
        base_threat *= 0.6  # Low morale units are less effective
        
    return base_threat
```

## Configuration and Balance

### Routing Thresholds
- **Automatic routing**: Below 20% morale
- **Rally threshold**: 40% morale minimum
- **ZOC threshold**: 25% morale minimum

### Morale Loss Values
- **Casualties**: Up to 30 morale (based on casualty percentage)
- **Multiple attacks**: 5% per additional attack
- **Rear attacks**: -15 morale penalty
- **Flank attacks**: -10 morale penalty
- **Cavalry charges**: 15-30 morale loss

### Rally Mechanics
- **Base rally chance**: 70%
- **High morale rally**: 90% (60+ morale)
- **Damaged unit penalty**: 60% of base chance (<50% soldiers)
- **Rally ability**: +30 morale, removes routing, 3-turn cooldown

## Strategic Implications

### Tactical Considerations

1. **Morale Management**: Keep units above 40% morale to prevent routing
2. **Positioning**: Protect unit flanks and rear from enemy attacks
3. **Rally Support**: Position generals to rally routing units
4. **Exploitation**: Target low-morale enemies for routing chains

### Counter-Routing Strategies

1. **Terrain Use**: Hills and forests provide defensive bonuses
2. **General Abilities**: Rally and Inspire abilities counter routing
3. **Unit Spacing**: Prevent routing from spreading to nearby units
4. **Reserve Forces**: Keep fresh units to plug gaps from routing

### Routing Chains

When one unit routes, it can trigger cascading morale effects:
- Nearby friendly units may suffer morale penalties
- Exposed flanks become vulnerable to exploitation
- Battle lines can collapse rapidly if not managed

The routing system creates dynamic, realistic battlefield psychology that rewards tactical positioning, morale management, and decisive action while punishing poor coordination and overextension.