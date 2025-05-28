# Test Scenarios JSON Format

This directory contains JSON-based test scenario definitions for the game. These scenarios make it easy to create, share, and modify test setups without changing code.

## File Structure

- `scenario_schema.json` - JSON Schema definition for scenario files
- `*.json` - Individual scenario definition files
- `README.md` - This documentation file

## Creating a New Scenario

1. Create a new `.json` file in this directory
2. Follow the structure defined in `scenario_schema.json`
3. Add the scenario to the game's test scenario menu (optional)

## Scenario Format

```json
{
  "name": "Scenario Name",
  "description": "What this scenario tests",
  "board_size": [width, height],
  "terrain": {
    "base": "plains|grassland|desert|snow",
    "tiles": [
      {"x": 10, "y": 5, "type": "hills|forest|water|mountains|swamp|etc"}
    ]
  },
  "units": [
    {
      "name": "Unit Name",
      "type": "warrior|archer|cavalry|pikeman",
      "x": 5,
      "y": 10,
      "player": 1,
      "facing": "NORTH_EAST|EAST|SOUTH_EAST|SOUTH_WEST|WEST|NORTH_WEST",
      "health": 100,
      "morale": 100
    }
  ],
  "castles": [
    {"x": 5, "y": 5, "player": 1}
  ],
  "victory_conditions": {
    "type": "elimination|capture|survival|custom",
    "turns": 10,
    "description": "Custom victory condition description"
  }
}
```

## Field Descriptions

### Required Fields

- **name**: Display name for the scenario
- **description**: Brief description of what the scenario tests
- **board_size**: [width, height] of the game board
- **terrain**: Terrain configuration
  - **base**: Default terrain type for all tiles
  - **tiles**: Array of specific terrain overrides
- **units**: Array of unit definitions

### Optional Fields

- **castles**: Array of castle positions
- **victory_conditions**: Victory condition configuration
- **facing**: Initial facing direction for units (defaults to EAST)
- **health**: Unit health as percentage (1-100, default 100)
- **morale**: Unit morale value (0-100, default 100)

## Terrain Types

- `plains` - Normal movement cost, no combat modifiers
- `grassland` - Same as plains (mapped to plains)
- `hills` - Elevation advantage (+50% damage from above)
- `high_hills` - Higher elevation, more pronounced effects
- `forest` - Slows movement, provides defense bonus
- `light_forest` - Light forest coverage
- `dense_forest` - Heavy forest coverage, blocks vision
- `water` - Impassable to most units
- `deep_water` - Deeper water areas
- `mountains` - Impassable, blocks line of sight
- `swamp` - Very slow movement
- `marsh` - Marshy areas, difficult terrain
- `desert` - Slightly slower movement
- `snow` - Slightly slower movement
- `bridge` - Passable over water
- `road` - Faster movement

## Unit Types

- `warrior` - Basic infantry unit
- `archer` - Ranged unit (3 hex range)
- `cavalry` - Fast unit with charge ability
- `mage` - Magic user with special abilities
- `pikeman` - Currently mapped to warrior

## Example Scenarios

### archer_mechanics.json
Tests archer ranged attacks and positioning. Includes hills for elevation testing.

### cavalry_charge.json
Tests cavalry charge mechanics against different unit types and on various terrain.

### fog_of_war.json
Tests visibility mechanics with terrain obstacles and unit positioning.

### terrain_showcase.json
Demonstrates all terrain types and their effects on movement and combat.

## Using Scenarios in Game

1. Scenarios are automatically loaded when the game starts
2. Access them through the Test Scenarios menu
3. JSON scenarios appear with "JSON:" prefix in the menu

## Tips for Creating Scenarios

1. **Start Simple**: Begin with a flat terrain and add complexity
2. **Test Incrementally**: Add units and terrain features one at a time
3. **Document Purpose**: Use clear names and descriptions
4. **Consider Visibility**: Place units within vision range for testing
5. **Balance Teams**: Unless testing specific mechanics, balance forces

## Validation

Use the `scenario_schema.json` file to validate your scenarios:

```bash
# Using a JSON schema validator (example with ajv-cli)
ajv validate -s scenario_schema.json -d your_scenario.json
```

## Sharing Scenarios

Scenarios are self-contained JSON files that can be easily shared:
- Copy the `.json` file to share a scenario
- Place in the `test_scenarios` directory to use
- No code changes required!