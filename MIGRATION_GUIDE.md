# Migration Guide: From Knight to Component-Based Units

## Overview

The game has been refactored from a monolithic `Knight` class to a component-based architecture with behaviors. This makes the code more modular, testable, and extensible.

## Key Changes

### 1. Component-Based Architecture

**Before:**
```python
class Knight:
    # Everything in one class
    def calculate_damage(self, target, ...):
        # Combat logic mixed with unit data
    
    def get_possible_moves(self, ...):
        # Movement logic mixed with unit data
```

**After:**
```python
# Separate concerns
unit = Unit(name, unit_class, x, y)
unit.add_behavior(MovementBehavior())
unit.add_behavior(AttackBehavior())
unit.add_behavior(CavalryChargeBehavior())  # Only for cavalry

# Stats are managed by a component
unit.stats = StatsComponent(UnitStats(...))
```

### 2. Behaviors as First-Class Objects

Behaviors can be:
- Added/removed dynamically
- Tested in isolation
- Extended without modifying core classes
- Queried for availability

```python
# Check what a unit can do
available_actions = unit.get_available_behaviors(game_state)

# Execute a behavior
if unit.can_execute_behavior('attack', game_state):
    result = unit.execute_behavior('attack', game_state, target=enemy)
```

### 3. Using the Factory

```python
# Create units with appropriate behaviors
warrior = UnitFactory.create_warrior("Sir Lancelot", 4, 5)
archer = UnitFactory.create_archer("Robin Hood", 4, 7)
cavalry = UnitFactory.create_cavalry("Sir Galahad", 3, 6)
```

### 4. Compatibility with Existing Code

Use `KnightAdapter` to make new units work with existing code:

```python
# In game_state._init_game()
from game.entities.unit_factory import UnitFactory
from game.entities.knight_adapter import KnightAdapter

# Create units with new system
unit = UnitFactory.create_warrior("Sir Lancelot", 4, 5)
knight = KnightAdapter(unit)  # Wrap for compatibility
self.knights.append(knight)
```

## Benefits

1. **Testability**: Each behavior can be tested independently
2. **Extensibility**: Add new behaviors without modifying existing code
3. **Modularity**: Clear separation of concerns
4. **Flexibility**: Units can have different combinations of behaviors
5. **Maintainability**: Easier to understand and modify

## Example: Adding a New Behavior

```python
from game.components.base import Behavior

class HealingBehavior(Behavior):
    def __init__(self):
        super().__init__("heal")
        
    def can_execute(self, unit, game_state):
        return unit.action_points >= 1 and unit.soldiers < unit.max_soldiers
        
    def get_ap_cost(self):
        return 1
        
    def execute(self, unit, game_state, **kwargs):
        if not self.can_execute(unit, game_state):
            return {'success': False}
            
        # Heal 10% of max soldiers
        heal_amount = int(unit.max_soldiers * 0.1)
        unit.stats.stats.current_soldiers = min(
            unit.max_soldiers,
            unit.soldiers + heal_amount
        )
        
        unit.action_points -= self.get_ap_cost()
        
        return {
            'success': True,
            'healed': heal_amount,
            'message': f"{unit.name} healed {heal_amount} soldiers"
        }

# Add to a unit
medic = UnitFactory.create_mage("Field Medic", 5, 5)
medic.add_behavior(HealingBehavior())
```

## Testing Example

```python
def test_custom_behavior():
    unit = UnitFactory.create_warrior("Test", 0, 0)
    unit.stats.take_casualties(30)  # Reduce to 70 soldiers
    
    # Add healing behavior
    unit.add_behavior(HealingBehavior())
    
    # Test execution
    result = unit.execute_behavior('heal', game_state)
    assert result['success']
    assert unit.soldiers == 80  # Healed 10
```

## Full Integration Example

To fully migrate the game:

1. Update `game_state._init_game()`:
```python
def _init_game(self):
    # ... castles ...
    
    # Create units with new system
    units = [
        UnitFactory.create_warrior("Sir Lancelot", 4, 5),
        UnitFactory.create_archer("Robin Hood", 4, 7),
        UnitFactory.create_cavalry("Sir Galahad", 3, 6),
        UnitFactory.create_warrior("Black Knight", 11, 5),
        UnitFactory.create_archer("Dark Archer", 11, 7),
        UnitFactory.create_mage("Merlin", 12, 6)
    ]
    
    # Wrap in adapters for compatibility
    for i, unit in enumerate(units):
        unit.player_id = 1 if i < 3 else 2
        self.knights.append(KnightAdapter(unit))
```

2. Update action handling to use behaviors:
```python
def attack_with_selected_knight(self, x, y):
    if not self.selected_knight:
        return False
        
    target = self.get_knight_at(x, y)
    if not target:
        return False
        
    # Use the underlying unit's behavior
    unit = self.selected_knight.unit if hasattr(self.selected_knight, 'unit') else self.selected_knight
    result = unit.execute_behavior('attack', self, target=target)
    
    if result['success']:
        # Handle animation, messages, etc.
        self.add_message(result.get('message', "Attack successful!"))
        return True
        
    return False
```

This architecture makes the game much more maintainable and extensible!