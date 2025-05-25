# Test Organization

This document describes the organization of test files in the test suite.

## Test Files by Feature

### test_general_display.py
Tests for general (commander) display functionality:
- Units have generals property
- Generals can be attached to units
- Multiple generals can be attached
- General roster has maximum limit

### test_frontage_combat.py
Tests for frontage (formation width) in combat calculations:
- Effective soldiers limited by formation width
- Terrain affects frontage (forest, hills, bridge)
- Combat damage uses effective soldiers, not total
- Different unit types have appropriate frontage values
- Special terrain like bridges severely limit frontage

### test_enemy_unit_info.py
Tests for enemy unit information display:
- Game state has enemy_info_unit property
- Clicking enemy units sets info
- Clicking friendly units clears enemy info
- Enemy info persists until cleared
- All unit stats are accessible for display

### test_disrupted_status.py
Tests for the disrupted status effect:
- Units have is_disrupted flag
- Disrupted units deal 50% less damage
- Disrupted units have 50% reduced defense
- Status can be toggled on/off
- Disruption affects all attack types
- Multiple status effects can stack

### test_cavalry_disruption.py
Tests for automatic cavalry disruption in terrain:
- Cavalry starts not disrupted
- Cavalry disrupted when moving to forest/hills/castle
- Disruption cleared when moving to plains
- Non-cavalry units not affected by terrain
- Disruption affects combat effectiveness

## Running Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_general_display.py -v
```

Run with coverage:
```bash
python -m pytest tests/ --cov=game --cov-report=html
```