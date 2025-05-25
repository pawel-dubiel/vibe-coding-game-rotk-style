"""Test terrain behavior refactoring"""
import pytest
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import Terrain, TerrainType, TerrainMap
from game.behaviors.terrain_movement import (
    TerrainMovementBehavior, CavalryTerrainBehavior,
    ArcherTerrainBehavior, WarriorTerrainBehavior, MageTerrainBehavior
)


class TestTerrainBehavior:
    """Test terrain movement behavior abstraction"""
    
    def test_units_have_terrain_behaviors(self):
        """Test that units are created with appropriate terrain behaviors"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        archer = UnitFactory.create_archer("Test Archer", 1, 0)
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 2, 0)
        mage = UnitFactory.create_mage("Test Mage", 3, 0)
        
        # Check each unit has a terrain behavior
        assert warrior.get_behavior('TerrainMovementBehavior') is not None
        assert archer.get_behavior('TerrainMovementBehavior') is not None
        assert cavalry.get_behavior('TerrainMovementBehavior') is not None
        assert mage.get_behavior('TerrainMovementBehavior') is not None
        
        # Check correct types
        assert isinstance(warrior.get_behavior('TerrainMovementBehavior'), WarriorTerrainBehavior)
        assert isinstance(archer.get_behavior('TerrainMovementBehavior'), ArcherTerrainBehavior)
        assert isinstance(cavalry.get_behavior('TerrainMovementBehavior'), CavalryTerrainBehavior)
        assert isinstance(mage.get_behavior('TerrainMovementBehavior'), MageTerrainBehavior)
        
    def test_cavalry_terrain_penalties(self):
        """Test that cavalry has appropriate terrain penalties"""
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 0, 0)
        terrain_behavior = cavalry.get_behavior('TerrainMovementBehavior')
        
        # Check movement modifiers
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.PLAINS) == 1.0
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.FOREST) == 2.0
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.SWAMP) == 2.0
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.HILLS) == 1.5
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.ROAD) == 0.8
        
        # Check combat modifiers
        assert terrain_behavior.get_combat_modifier(TerrainType.PLAINS) == 1.1
        assert terrain_behavior.get_combat_modifier(TerrainType.FOREST) == 0.8
        assert terrain_behavior.get_combat_modifier(TerrainType.HILLS) == 0.8
        
    def test_archer_terrain_bonuses(self):
        """Test that archers have forest bonuses"""
        archer = UnitFactory.create_archer("Test Archer", 0, 0)
        terrain_behavior = archer.get_behavior('TerrainMovementBehavior')
        
        # Check movement modifiers
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.FOREST) == 0.75
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.PLAINS) == 1.0
        
        # Check combat modifiers
        assert terrain_behavior.get_combat_modifier(TerrainType.FOREST) == 1.2
        assert terrain_behavior.get_combat_modifier(TerrainType.HILLS) == 1.2
        
    def test_warrior_terrain_resilience(self):
        """Test that warriors are less affected by difficult terrain"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        terrain_behavior = warrior.get_behavior('TerrainMovementBehavior')
        
        # Warriors have reduced penalties in difficult terrain
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.HILLS) == 0.8
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.SWAMP) == 0.8
        
    def test_mage_swamp_penalty(self):
        """Test that mages struggle in swamps"""
        mage = UnitFactory.create_mage("Test Mage", 0, 0)
        terrain_behavior = mage.get_behavior('TerrainMovementBehavior')
        
        # Mages have extra penalty in swamps
        assert terrain_behavior.get_movement_cost_modifier(TerrainType.SWAMP) == 1.2
        assert terrain_behavior.get_combat_modifier(TerrainType.SWAMP) == 0.7
        
    def test_terrain_integration(self):
        """Test that terrain objects use unit behaviors correctly"""
        # Create units
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 0, 0)
        archer = UnitFactory.create_archer("Test Archer", 0, 0)
        
        # Create terrain
        forest = Terrain(TerrainType.FOREST)
        plains = Terrain(TerrainType.PLAINS)
        
        # Test movement costs
        # Forest base cost is 2
        assert forest.get_movement_cost_for_unit(cavalry) == 4.0  # 2 * 2.0 modifier
        assert forest.get_movement_cost_for_unit(archer) == 1.5   # 2 * 0.75 modifier
        
        # Plains base cost is 1
        assert plains.get_movement_cost_for_unit(cavalry) == 1.0
        assert plains.get_movement_cost_for_unit(archer) == 1.0
        
        # Test combat modifiers
        assert forest.get_combat_modifier_for_unit(cavalry) == 0.8
        assert forest.get_combat_modifier_for_unit(archer) == 1.2
        
    def test_no_type_checking_in_terrain(self):
        """Test that terrain.py doesn't check unit types directly"""
        # Read the terrain.py file and ensure no direct type checking
        with open('/Users/pawel/work/game/game/terrain.py', 'r') as f:
            content = f.read()
            
        # These patterns should NOT appear in the refactored code
        bad_patterns = [
            "== KnightClass.CAVALRY",
            "== KnightClass.ARCHER", 
            "== KnightClass.WARRIOR",
            "== KnightClass.MAGE",
            "knight_class ==",
            "elif knight_class"
        ]
        
        # Check that none of these patterns exist
        for pattern in bad_patterns:
            assert pattern not in content, f"Found type checking pattern '{pattern}' in terrain.py"
            
    def test_terrain_map_uses_units(self):
        """Test that TerrainMap methods use units instead of knight_class"""
        terrain_map = TerrainMap(10, 10)
        
        # Create a unit
        warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        
        # These should work with units
        cost = terrain_map.get_movement_cost(5, 5, warrior)
        assert isinstance(cost, (int, float))
        
        # Should also work without unit (passable check)
        assert terrain_map.is_passable(5, 5) in [True, False]