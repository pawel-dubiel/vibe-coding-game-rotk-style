# General System Documentation

## Overview

Each unit can have up to 3 generals who provide various bonuses and special abilities. Generals add strategic depth by offering passive bonuses, active abilities, and triggered effects that can turn the tide of battle.

## General Types and Abilities

### Passive Abilities (Always Active)

1. **Inspire** 
   - +10 morale bonus
   - +5 morale regeneration per turn
   - Great for keeping troops fighting

2. **Tactician**
   - +1 movement range
   - Excellent for cavalry and mobile units

3. **Veteran**
   - 10% damage reduction
   - Keeps units alive longer

4. **Aggressive**
   - 15% damage bonus
   - Perfect for assault units

### Active Abilities (Cost Will)

1. **Rally** (20 Will)
   - Restore 30 morale instantly
   - Remove routing status
   - 3 turn cooldown
   - Essential for recovering broken units

2. **Berserk** (30 Will)
   - Double damage on next attack
   - Take 50% more damage
   - 2 turn cooldown
   - High risk, high reward

### Triggered Abilities (Automatic)

1. **Last Stand**
   - When below 25% soldiers
   - 30% damage reduction
   - Helps units fight to the end

2. **Countercharge**
   - When charged by cavalry
   - 50% bonus counter damage
   - Punishes enemy charges

## General Archetypes

### Pre-built Templates

1. **Inspiring Leader**: Inspire + Rally + Veteran
2. **Tactical Genius**: Tactician + Veteran + Last Stand
3. **Aggressive Commander**: Aggressive + Berserk + Countercharge
4. **Defensive Master**: Veteran + Last Stand + Countercharge
5. **Veteran Officer**: Veteran + Inspire + Last Stand
6. **Cavalry Expert**: Tactician + Aggressive + Countercharge
7. **Berserker Lord**: Berserk + Aggressive + Last Stand

## General Progression

### Experience System
- Generals gain XP after battles
- Victory: 10 XP base
- Defeat: 5 XP base
- +1 XP per 10 casualties inflicted
- Level up at: 100, 200, 300... XP

### Level Bonuses
- +2 morale per level
- +2% attack bonus per level
- +2% defense bonus per level

## Implementation Examples

### Creating Units with Generals
```python
# Units automatically get 2 starting generals
warrior = UnitFactory.create_warrior("Elite Guard", 5, 5)

# Or create without generals
scout = UnitFactory.create_unit("Scout", KnightClass.ARCHER, 3, 3, add_generals=False)

# Add custom general
general = GeneralFactory.create_general("Defensive Master")
scout.generals.add_general(general)
```

### Using Active Abilities
```python
# Get available active abilities
active_abilities = unit.generals.get_active_abilities(unit)

for general, ability in active_abilities:
    if ability.name == "Rally" and unit.morale < 50:
        result = unit.execute_general_ability(general, ability)
        if result['success']:
            print(result['message'])
```

### Combat with General Bonuses
```python
# Damage calculation automatically includes:
# - Passive damage bonuses (Aggressive)
# - Level-based attack bonuses
# - Temporary effects (Berserk)

# Defense calculation includes:
# - Passive damage reduction (Veteran)
# - Triggered abilities (Last Stand)
# - Level-based defense bonuses
```

## Strategic Considerations

### Army Composition
- **Frontline Units**: Defensive Master + Veteran Officer
- **Cavalry**: Cavalry Expert + Aggressive Commander
- **Archers**: Tactical Genius + Veteran Officer
- **Elite Units**: 3 high-level generals for maximum bonuses

### Ability Timing
- Save **Rally** for critical moments or routing units
- Use **Berserk** for decisive strikes or desperate situations
- Position units to maximize **Countercharge** opportunities

### General Development
- Focus on leveling key generals through combat
- Preserve experienced generals by rotating damaged units
- Consider general synergies when assigning to units

## UI Integration

The game includes:
- General display panel showing all generals and abilities
- Visual indicators for ability cooldowns
- Context menu options for active abilities
- Experience bars for general progression

## Balance Notes

- Maximum 3 generals per unit prevents stacking too many bonuses
- Will cost limits ability spam
- Cooldowns prevent ability cycling
- Level bonuses are small but meaningful over time
- Triggered abilities provide comeback mechanics