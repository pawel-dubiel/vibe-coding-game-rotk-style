"""Tests for unit rotation mechanics"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.facing import FacingDirection
from game.test_utils.mock_game_state import MockGameState
from game.terrain import TerrainType, Terrain


class TestRotationMechanics:
    """Test unit rotation behavior"""
    
    def setup_method(self):
        """Set up test environment"""
        self.game_state = MockGameState(board_width=20, board_height=20)
        
    def test_rotation_behavior_exists(self):
        """Test that units have rotation behavior"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        assert 'rotate' in unit.behaviors
        
    def test_basic_rotation(self):
        """Test basic clockwise and counter-clockwise rotation"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.player_id = 1
        unit.action_points = 5
        self.game_state.add_knight(unit)
        
        # Start facing north-east
        unit.facing.facing = FacingDirection.NORTH_EAST
        
        # Rotate clockwise
        result = unit.behaviors['rotate'].execute(unit, self.game_state, 'clockwise')
        assert result['success']
        assert unit.facing.facing == FacingDirection.EAST
        assert unit.action_points == 4  # Cost 1 AP
        
        # Rotate counter-clockwise
        unit.action_points = 5
        result = unit.behaviors['rotate'].execute(unit, self.game_state, 'counter_clockwise')
        assert result['success']
        assert unit.facing.facing == FacingDirection.NORTH_EAST
        
    def test_rotation_ap_cost(self):
        """Test AP costs for rotation"""
        # Test basic unit
        unit = UnitFactory.create_warrior("Test", 10, 10)
        behavior = unit.behaviors['rotate']
        assert behavior.get_ap_cost(unit, self.game_state) == 1
        
        # Test cavalry (should cost more)
        cavalry = UnitFactory.create_cavalry("Cavalry", 10, 10)
        behavior = cavalry.behaviors['rotate']
        assert behavior.get_ap_cost(cavalry, self.game_state) == 2
        
    def test_terrain_rotation_costs(self):
        """Test that terrain affects rotation cost"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.player_id = 1
        behavior = unit.behaviors['rotate']
        
        # Plains - normal cost
        self.game_state.terrain_map.terrain_grid[10][10] = Terrain(TerrainType.PLAINS)
        assert behavior.get_ap_cost(unit, self.game_state) == 1
        
        # Forest - harder to rotate
        self.game_state.terrain_map.terrain_grid[10][10] = Terrain(TerrainType.FOREST)
        assert behavior.get_ap_cost(unit, self.game_state) == 2
        
        # Swamp - very hard to rotate
        self.game_state.terrain_map.terrain_grid[10][10] = Terrain(TerrainType.SWAMP)
        assert behavior.get_ap_cost(unit, self.game_state) == 3
        
    def test_cannot_rotate_in_combat(self):
        """Test that units cannot rotate when adjacent to enemies"""
        unit = UnitFactory.create_warrior("Unit", 10, 10)
        unit.player_id = 1
        unit.action_points = 5
        
        enemy = UnitFactory.create_warrior("Enemy", 11, 10)
        enemy.player_id = 2
        
        self.game_state.add_knight(unit)
        self.game_state.add_knight(enemy)
        
        # Should not be able to rotate
        behavior = unit.behaviors['rotate']
        assert not behavior.can_execute(unit, self.game_state)
        
        # Try to execute should fail
        result = behavior.execute(unit, self.game_state, 'clockwise')
        assert not result['success']
        assert result['reason'] == 'Cannot rotate'
        
    def test_cannot_rotate_without_ap(self):
        """Test that rotation requires AP"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.player_id = 1
        unit.action_points = 0
        self.game_state.add_knight(unit)
        
        behavior = unit.behaviors['rotate']
        assert not behavior.can_execute(unit, self.game_state)
        
    def test_routing_units_cannot_rotate(self):
        """Test that routing units cannot rotate"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.player_id = 1
        unit.action_points = 5
        unit.is_routing = True
        self.game_state.add_knight(unit)
        
        behavior = unit.behaviors['rotate']
        assert not behavior.can_execute(unit, self.game_state)
        
    def test_rotation_options(self):
        """Test getting rotation options"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.facing.facing = FacingDirection.NORTH_EAST
        
        behavior = unit.behaviors['rotate']
        options = behavior.get_rotation_options(unit)
        
        assert len(options) == 2
        assert options[0][0] == 'rotate_cw'
        assert options[0][2] == 'clockwise'
        assert 'East' in options[0][1]  # Should mention rotating to East
        
        assert options[1][0] == 'rotate_ccw' 
        assert options[1][2] == 'counter_clockwise'
        assert 'North West' in options[1][1]  # Should mention rotating to North West
        
    def test_cavalry_rotation_in_forest(self):
        """Test cavalry rotating in difficult terrain"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 10, 10)
        cavalry.player_id = 1
        cavalry.action_points = 5
        self.game_state.add_knight(cavalry)
        
        # Set forest terrain
        self.game_state.terrain_map.terrain_grid[10][10] = Terrain(TerrainType.FOREST)
        
        behavior = cavalry.behaviors['rotate']
        # Cavalry (+1) in forest (+1 from base 1) = 3 AP
        assert behavior.get_ap_cost(cavalry, self.game_state) == 3
        
        # Should be able to rotate with 5 AP
        assert behavior.can_execute(cavalry, self.game_state)
        
        # But not with only 2 AP
        cavalry.action_points = 2
        assert not behavior.can_execute(cavalry, self.game_state)


def run_tests():
    """Run all rotation tests"""
    test = TestRotationMechanics()
    
    print("Testing Rotation Mechanics...")
    
    test.setup_method()
    test.test_rotation_behavior_exists()
    print("✓ Units have rotation behavior")
    
    test.setup_method()
    test.test_basic_rotation()
    print("✓ Basic rotation works")
    
    test.setup_method()
    test.test_rotation_ap_cost()
    print("✓ AP costs calculated correctly")
    
    test.setup_method()
    test.test_terrain_rotation_costs()
    print("✓ Terrain affects rotation cost")
    
    test.setup_method()
    test.test_cannot_rotate_in_combat()
    print("✓ Cannot rotate in combat")
    
    test.setup_method()
    test.test_cannot_rotate_without_ap()
    print("✓ Rotation requires AP")
    
    test.setup_method()
    test.test_routing_units_cannot_rotate()
    print("✓ Routing units cannot rotate")
    
    test.setup_method()
    test.test_rotation_options()
    print("✓ Rotation options generated correctly")
    
    test.setup_method()
    test.test_cavalry_rotation_in_forest()
    print("✓ Cavalry rotation in difficult terrain")
    
    print("\nAll rotation tests passed!")


if __name__ == "__main__":
    run_tests()