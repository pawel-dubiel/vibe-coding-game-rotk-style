"""Test terrain-based attack costs system"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.test_utils.mock_game_state import MockGameState
from game.terrain import TerrainType

class TestTerrainAttackCosts:
    """Test that attacking into difficult terrain costs additional AP"""
    
    def setup_method(self):
        """Set up test environment"""
        self.game_state = MockGameState(board_width=10, board_height=10)
        
    def test_plains_no_penalty(self):
        """Test that plains terrain has no attack penalty"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
        
        # Create units
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        
        # Test attack cost
        attack_behavior = warrior.behaviors['attack']
        cost = attack_behavior.get_ap_cost(warrior, target, self.game_state)
        
        assert cost == 4, f"Plains attack should cost 4 AP (base), got {cost}"
        
    def test_hills_penalty(self):
        """Test that hills terrain adds +2 AP penalty for melee"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        
        # Create units
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        
        # Test attack cost
        attack_behavior = warrior.behaviors['attack']
        cost = attack_behavior.get_ap_cost(warrior, target, self.game_state)
        
        assert cost == 6, f"Hills attack should cost 6 AP (4 base + 2 terrain), got {cost}"
        
    def test_forest_penalty(self):
        """Test that forest terrain adds +2 AP penalty for melee"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.FOREST)
        
        # Create units
        cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(cavalry)
        self.game_state.add_knight(target)
        
        # Test attack cost
        attack_behavior = cavalry.behaviors['attack']
        cost = attack_behavior.get_ap_cost(cavalry, target, self.game_state)
        
        assert cost == 5, f"Forest attack should cost 5 AP (3 base + 2 terrain), got {cost}"
        
    def test_dense_forest_penalty(self):
        """Test that dense forest terrain adds +4 AP penalty"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.DENSE_FOREST)
        
        # Create units
        mage = UnitFactory.create_unit("Mage", KnightClass.MAGE, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(mage)
        self.game_state.add_knight(target)
        
        # Test attack cost
        attack_behavior = mage.behaviors['attack']
        cost = attack_behavior.get_ap_cost(mage, target, self.game_state)
        
        assert cost == 6, f"Dense forest attack should cost 6 AP (2 base + 4 terrain), got {cost}"
        
    def test_ranged_reduced_penalty(self):
        """Test that ranged attacks have reduced terrain penalties"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        
        # Create units
        archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(archer)
        self.game_state.add_knight(target)
        
        # Test attack cost
        attack_behavior = archer.behaviors['attack']
        cost = attack_behavior.get_ap_cost(archer, target, self.game_state)
        
        assert cost == 3, f"Ranged hills attack should cost 3 AP (2 base + 1 terrain), got {cost}"
        
    def test_swamp_high_penalty(self):
        """Test that swamp terrain adds high penalty"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.SWAMP)
        
        # Create units
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        
        # Test attack cost
        attack_behavior = warrior.behaviors['attack']
        cost = attack_behavior.get_ap_cost(warrior, target, self.game_state)
        
        assert cost == 8, f"Swamp attack should cost 8 AP (4 base + 4 terrain), got {cost}"
        
    def test_base_cost_without_terrain(self):
        """Test that base costs work correctly without terrain data"""
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 3, 3)
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        
        attack_behavior = warrior.behaviors['attack']
        
        # Test without game_state
        cost = attack_behavior.get_ap_cost(warrior, target)
        assert cost == 4, f"Base warrior attack should cost 4 AP, got {cost}"
        
        # Test without target
        cost = attack_behavior.get_ap_cost(warrior)
        assert cost == 4, f"Base warrior attack should cost 4 AP, got {cost}"
        
    def test_combat_execution_with_terrain_costs(self):
        """Test that actual combat execution uses terrain costs"""
        # Set terrain
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        
        # Create units
        warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)  # Adjacent
        warrior.player_id = 1
        target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
        target.player_id = 2
        
        self.game_state.add_knight(warrior)
        self.game_state.add_knight(target)
        self.game_state.current_player = 1
        
        initial_ap = warrior.action_points
        
        # Execute attack
        attack_behavior = warrior.behaviors['attack']
        result = attack_behavior.execute(warrior, self.game_state, target)
        
        assert result['success'], "Attack should succeed"
        
        ap_consumed = initial_ap - warrior.action_points
        assert ap_consumed == 6, f"Should consume 6 AP (4 base + 2 hills), consumed {ap_consumed}"

if __name__ == "__main__":
    # Run the tests
    test_class = TestTerrainAttackCosts()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    print("Running terrain attack cost tests...")
    for method_name in test_methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✅ {method_name} - PASSED")
        except Exception as e:
            print(f"❌ {method_name} - FAILED: {e}")
    
    print("Tests completed!")