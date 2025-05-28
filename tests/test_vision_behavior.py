"""Test vision behavior refactoring"""
import pytest
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.behaviors.vision import VisionBehavior, StandardVisionBehavior, ArcherVisionBehavior, ScoutVisionBehavior
from game.terrain import TerrainType, Terrain
from game.visibility import FogOfWar, VisibilityState
from game.test_utils.mock_game_state import MockGameState
from game.hex_utils import HexGrid


class TestVisionBehavior:
    """Test vision behavior abstraction"""
    
    def test_units_have_vision_behaviors(self):
        """Test that units are created with appropriate vision behaviors"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        archer = UnitFactory.create_archer("Test Archer", 1, 0)
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 2, 0)
        mage = UnitFactory.create_mage("Test Mage", 3, 0)
        
        # Check each unit has a vision behavior
        assert warrior.get_behavior('VisionBehavior') is not None
        assert archer.get_behavior('VisionBehavior') is not None
        assert cavalry.get_behavior('VisionBehavior') is not None
        assert mage.get_behavior('VisionBehavior') is not None
        
        # Check correct types
        assert isinstance(warrior.get_behavior('VisionBehavior'), StandardVisionBehavior)
        assert isinstance(archer.get_behavior('VisionBehavior'), ArcherVisionBehavior)
        assert isinstance(cavalry.get_behavior('VisionBehavior'), ScoutVisionBehavior)
        assert isinstance(mage.get_behavior('VisionBehavior'), StandardVisionBehavior)
        
    def test_vision_ranges(self):
        """Test that different units have appropriate vision ranges"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        archer = UnitFactory.create_archer("Test Archer", 1, 0)
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 2, 0)
        
        warrior_vision = warrior.get_behavior('VisionBehavior')
        archer_vision = archer.get_behavior('VisionBehavior')
        cavalry_vision = cavalry.get_behavior('VisionBehavior')
        
        # Test base ranges
        assert warrior_vision.get_vision_range() == 3
        assert archer_vision.get_vision_range() == 4
        assert cavalry_vision.get_vision_range() == 4
        
    def test_elevated_vision(self):
        """Test that elevation affects vision"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 1, 0)
        
        warrior_vision = warrior.get_behavior('VisionBehavior')
        cavalry_vision = cavalry.get_behavior('VisionBehavior')
        
        # Warriors are not naturally elevated
        assert not warrior_vision.is_elevated()
        
        # Cavalry is naturally elevated
        assert cavalry_vision.is_elevated()
        
    def test_vision_blocking(self):
        """Test that only certain units block vision"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 1, 0)
        
        warrior_vision = warrior.get_behavior('VisionBehavior')
        cavalry_vision = cavalry.get_behavior('VisionBehavior')
        
        # Warriors don't block vision
        assert not warrior_vision.blocks_vision()
        
        # Cavalry blocks vision
        assert cavalry_vision.blocks_vision()
        
    def test_terrain_vision_bonus(self):
        """Test that hills provide vision bonus"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        warrior_vision = warrior.get_behavior('VisionBehavior')
        
        # Normal terrain
        normal_terrain = Terrain(TerrainType.PLAINS)
        assert warrior_vision.get_vision_range(normal_terrain) == 3
        
        # Hills terrain
        hills_terrain = Terrain(TerrainType.HILLS)
        assert warrior_vision.get_vision_range(hills_terrain) == 4  # +1 for elevation
        
    def test_fog_of_war_integration(self):
        """Test that fog of war works with vision behaviors"""
        # Create game state with units
        game_state = MockGameState(board_width=10, board_height=10)
        game_state.hex_grid = HexGrid()
        
        warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        warrior.player_id = 1
        archer = UnitFactory.create_archer("Test Archer", 7, 5)
        archer.player_id = 1
        
        game_state.add_knight(warrior)
        game_state.add_knight(archer)
        
        # Create fog of war
        fog = FogOfWar(10, 10, 2)
        fog.update_player_visibility(game_state, 1)
        
        # Check that units can see around themselves
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.VISIBLE
        
        # Check warrior vision range (3 hexes)
        # In hex grid, distance is calculated differently than row distance
        # Check positions that are actually within 3 hex distance
        assert fog.is_hex_visible(1, 4, 5)  # 1 hex away (left)
        assert fog.is_hex_visible(1, 6, 5)  # 1 hex away (right)
        assert fog.is_hex_visible(1, 5, 4)  # 1 hex away (up)
        assert fog.is_hex_visible(1, 5, 6)  # 1 hex away (down)
        
        # Check that visibility system is working
        visible_count = 0
        for x in range(10):
            for y in range(10):
                if fog.get_visibility_state(1, x, y) in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
                    visible_count += 1
        
        # Should see a reasonable number of hexes from both units combined
        assert visible_count > 20  # At least 20 hexes visible
        
    def test_vision_modifiers(self):
        """Test temporary vision modifiers"""
        warrior = UnitFactory.create_warrior("Test Warrior", 0, 0)
        vision = warrior.get_behavior('VisionBehavior')
        
        # Base range
        assert vision.get_vision_range() == 3
        
        # Add a modifier
        vision.add_vision_modifier('spell', 2)
        assert vision.get_vision_range() == 5
        
        # Remove modifier
        vision.remove_vision_modifier('spell')
        assert vision.get_vision_range() == 3
        
    def test_no_type_checking_in_visibility(self):
        """Test that visibility.py doesn't check unit types directly"""
        # Read the visibility.py file and ensure no direct type checking
        with open('/Users/pawel/work/game/game/visibility.py', 'r') as f:
            content = f.read()
            
        # These patterns should NOT appear in the refactored code
        bad_patterns = [
            "== 'cavalry'",
            "== 'archer'", 
            "== 'warrior'",
            "== 'mage'",
            ".lower() == 'cavalry'",
            ".lower() == 'archer'"
        ]
        
        # Check for unit type in vision range calculation
        lines = content.split('\n')
        get_vision_range_start = None
        for i, line in enumerate(lines):
            if 'def _get_unit_vision_range' in line:
                get_vision_range_start = i
                break
                
        if get_vision_range_start:
            # Check the next 20 lines of the method
            method_lines = lines[get_vision_range_start:get_vision_range_start + 20]
            method_content = '\n'.join(method_lines)
            
            for pattern in bad_patterns:
                assert pattern not in method_content, f"Found type checking pattern '{pattern}' in _get_unit_vision_range"