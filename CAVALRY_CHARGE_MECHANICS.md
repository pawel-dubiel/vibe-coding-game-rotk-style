# Cavalry Charge Mechanics

## Overview
Cavalry charges are now always possible against adjacent enemies. The outcome depends on what's behind the target, creating tactical depth and realistic combat scenarios.

## Charge Outcomes

### 1. **Normal Charge (Target can be pushed)**
- **Damage**: 80% of cavalry soldiers as casualties to target
- **Self Damage**: 5% of cavalry soldiers
- **Morale Damage**: 20 points
- **Effect**: Target is pushed back one tile
- **Message**: "Charge! Pushed [target] back!"

### 2. **Crushing Charge (Target against wall/castle)**
- **Damage**: 120% of cavalry soldiers (1.5x base)
- **Self Damage**: 10% of cavalry soldiers
- **Morale Damage**: 30 points
- **Effect**: Target is crushed with nowhere to escape
- **Message**: "Devastating charge! [target] crushed against the wall!"

### 3. **Terrain Trap Charge (Impassable terrain behind)**
- **Damage**: 104% of cavalry soldiers (1.3x base)
- **Self Damage**: 8% of cavalry soldiers
- **Morale Damage**: 25 points
- **Effect**: Target trapped by terrain
- **Message**: "Crushing charge! [target] trapped by terrain!"

### 4. **Collision Charge (Unit behind target)**
- **Damage**: 96% of cavalry soldiers (1.2x base)
- **Self Damage**: 7% of cavalry soldiers
- **Morale Damage**: 20 points to primary target
- **Collateral Damage**: 24% of cavalry soldiers (0.3x base) to unit behind
- **Collateral Morale**: 10 points to unit behind
- **Effect**: Target slams into the unit behind
- **Message**: "Charge! [target] slammed into [unit behind]!"

## Requirements
- **Unit Type**: Only cavalry can charge
- **Will Cost**: 40 will points
- **Action Points**: 2 AP (same as attack)
- **Range**: Must be adjacent (distance = 1)
- **Special**: Can only charge once per turn

## Tactical Considerations

1. **Positioning**: Try to catch enemies against walls or obstacles for maximum damage
2. **Formation**: Create "anvil" situations by positioning units behind enemies
3. **Terrain**: Use impassable terrain to trap enemies
4. **Castle Sieges**: Extremely effective when enemies are defending near castle walls
5. **Counter-play**: Keep space behind your units to allow retreat from charges

## Code Example

```python
# In the refactored system
cavalry = UnitFactory.create_cavalry("Knight", 5, 5)
result = cavalry.execute_behavior('cavalry_charge', game_state, target=enemy)

if result['success']:
    print(f"Charge damage: {result['damage']}")
    if 'collateral_unit' in result:
        print(f"Collateral damage to {result['collateral_unit'].name}: {result['collateral_damage']}")
```

## Balance Notes
- Charges are high-risk, high-reward actions
- The cavalry takes damage even on successful charges
- Will consumption limits charges to strategic moments
- Collateral damage creates interesting multi-unit interactions
- Different damage multipliers reward tactical positioning