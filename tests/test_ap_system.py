"""Test the new Action Point system"""
import unittest
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainMap, TerrainType, Terrain

class MockGameState:
    def __init__(self):
        self.board_width = 10
        self.board_height = 10
        self.knights = []
        self.castles = []
        self.terrain_map = TerrainMap(10, 10)

class TestAPSystem(unittest.TestCase):
    """Test Action Point system for movement, combat, and abilities"""
    
    def setUp(self):
        self.game_state = MockGameState()
        
    def test_unit_starting_ap(self):
        """Test units start with appropriate AP"""
        warrior = UnitFactory.create_warrior("Warrior", 5, 5)
        archer = UnitFactory.create_archer("Archer", 5, 5)
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        mage = UnitFactory.create_mage("Mage", 5, 5)
        
        self.assertEqual(warrior.action_points, 8)
        self.assertEqual(archer.action_points, 7)
        self.assertEqual(cavalry.action_points, 10)
        self.assertEqual(mage.action_points, 6)
        
    def test_movement_ap_costs(self):
        """Test movement costs AP based on terrain"""
        unit = UnitFactory.create_warrior("Test", 5, 5)
        unit.player_id = 1
        self.game_state.knights = [unit]
        
        move_behavior = unit.behaviors['move']
        
        # First ensure we have plains terrain for comparison
        plains_terrain = Terrain(TerrainType.PLAINS)
        self.game_state.terrain_map.terrain_grid[5][6] = plains_terrain
        plains_cost = move_behavior.get_ap_cost((5, 5), (6, 5), unit, self.game_state)
        self.assertGreaterEqual(plains_cost, 1)
        
        # Now change to forest terrain
        forest_terrain = Terrain(TerrainType.FOREST)
        self.game_state.terrain_map.terrain_grid[5][6] = forest_terrain
        forest_cost = move_behavior.get_ap_cost((5, 5), (6, 5), unit, self.game_state)
        
        # Forest should cost more than plains
        self.assertGreater(forest_cost, plains_cost)
        
        # Diagonal movement should cost more than orthogonal
        diagonal_cost = move_behavior.get_ap_cost((5, 5), (6, 6), unit, self.game_state)
        self.assertGreaterEqual(diagonal_cost, plains_cost)
        
    def test_movement_execution_costs_ap(self):
        """Test that executing movement actually costs AP"""
        unit = UnitFactory.create_warrior("Test", 5, 5)
        unit.player_id = 1
        self.game_state.knights = [unit]
        
        initial_ap = unit.action_points
        
        # Move to adjacent position
        result = unit.execute_behavior('move', self.game_state, target_x=6, target_y=5)
        
        self.assertTrue(result['success'])
        self.assertLess(unit.action_points, initial_ap)  # Should have consumed some AP
        
    def test_attack_ap_costs(self):
        """Test different units have different attack AP costs"""
        warrior = UnitFactory.create_warrior("Warrior", 5, 5)
        archer = UnitFactory.create_archer("Archer", 5, 5)
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        mage = UnitFactory.create_mage("Mage", 5, 5)
        
        # Test attack behavior AP costs
        self.assertEqual(warrior.behaviors['attack'].get_ap_cost(warrior), 4)
        self.assertEqual(archer.behaviors['attack'].get_ap_cost(archer), 2)
        self.assertEqual(cavalry.behaviors['attack'].get_ap_cost(cavalry), 3)
        self.assertEqual(mage.behaviors['attack'].get_ap_cost(mage), 2)
        
    def test_attack_execution_costs_ap(self):
        """Test that attacks consume the correct AP"""
        attacker = UnitFactory.create_warrior("Attacker", 5, 5)
        attacker.player_id = 1
        
        target = UnitFactory.create_warrior("Target", 6, 5)
        target.player_id = 2
        
        self.game_state.knights = [attacker, target]
        
        initial_ap = attacker.action_points
        
        # Execute attack
        result = attacker.execute_behavior('attack', self.game_state, target=target)
        
        self.assertTrue(result['success'])
        self.assertEqual(attacker.action_points, initial_ap - 4)  # Warriors cost 4 AP
        
    def test_charge_ap_cost(self):
        """Test cavalry charge costs significant AP"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        target = UnitFactory.create_archer("Target", 6, 5)
        target.player_id = 2
        
        self.game_state.knights = [cavalry, target]
        
        # Check charge AP cost
        charge_behavior = cavalry.behaviors['cavalry_charge']
        self.assertEqual(charge_behavior.get_ap_cost(), 5)
        
        initial_ap = cavalry.action_points
        
        # Execute charge
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        
        self.assertTrue(result['success'])
        self.assertEqual(cavalry.action_points, initial_ap - 5)  # Charges cost 5 AP
        
    def test_can_attack_with_insufficient_ap(self):
        """Test units cannot attack without enough AP"""
        warrior = UnitFactory.create_warrior("Warrior", 5, 5)
        warrior.action_points = 3  # Not enough for warrior attack (needs 4)
        
        self.assertFalse(warrior.can_execute_behavior('attack', self.game_state))
        
        # But archer should be able to attack with 3 AP (needs 2)
        archer = UnitFactory.create_archer("Archer", 5, 5)
        archer.action_points = 3
        
        self.assertTrue(archer.can_execute_behavior('attack', self.game_state))
        
    def test_multiple_actions_per_turn(self):
        """Test units can perform multiple actions if they have AP"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)  # Starts with 10 AP
        cavalry.player_id = 1
        
        enemy = UnitFactory.create_archer("Enemy", 7, 5)
        enemy.player_id = 2
        
        self.game_state.knights = [cavalry, enemy]
        
        initial_ap = cavalry.action_points
        
        # Move once
        result1 = cavalry.execute_behavior('move', self.game_state, target_x=6, target_y=5)
        self.assertTrue(result1['success'])
        self.assertLess(cavalry.action_points, initial_ap)
        
        ap_after_move = cavalry.action_points
        
        # Simulate animation completion - position would be updated by animation
        cavalry.x = 6
        cavalry.y = 5
        
        # Reset has_moved flag to allow another move
        cavalry.has_moved = False
        
        # Move again (to a different position since enemy is at 7,5)
        result2 = cavalry.execute_behavior('move', self.game_state, target_x=7, target_y=6)
        self.assertTrue(result2['success'])
        self.assertLess(cavalry.action_points, ap_after_move)
        
        ap_after_second_move = cavalry.action_points
        
        # Attack if we have enough AP
        if cavalry.can_execute_behavior('attack', self.game_state):
            result3 = cavalry.execute_behavior('attack', self.game_state, target=enemy)
            self.assertTrue(result3['success'])
            self.assertLess(cavalry.action_points, ap_after_second_move)
        
    def test_zoc_movement_penalty(self):
        """Test movement in enemy ZOC costs extra AP"""
        unit = UnitFactory.create_warrior("Unit", 5, 5)
        unit.player_id = 1
        
        enemy = UnitFactory.create_warrior("Enemy", 6, 6)
        enemy.player_id = 2
        
        self.game_state.knights = [unit, enemy]
        
        move_behavior = unit.behaviors['move']
        
        # Normal movement cost
        normal_cost = move_behavior.get_ap_cost((5, 5), (5, 6), unit, self.game_state)
        
        # Set unit in ZOC
        unit.in_enemy_zoc = True
        
        # Movement in ZOC should cost extra
        zoc_cost = move_behavior.get_ap_cost((5, 5), (5, 6), unit, self.game_state)
        self.assertGreater(zoc_cost, normal_cost)
        
    def test_road_movement_bonus(self):
        """Test roads reduce movement AP cost"""
        unit = UnitFactory.create_warrior("Unit", 5, 5)
        unit.player_id = 1
        self.game_state.knights = [unit]
        
        # Set road terrain
        road_terrain = Terrain(TerrainType.ROAD)
        self.game_state.terrain_map.terrain_grid[5][6] = road_terrain
        
        move_behavior = unit.behaviors['move']
        ap_cost = move_behavior.get_ap_cost((5, 5), (6, 5), unit, self.game_state)
        
        # Roads have 0.5 cost, but minimum is 1
        self.assertEqual(ap_cost, 1)
        
    def test_ap_regeneration(self):
        """Test AP is restored at end of turn"""
        unit = UnitFactory.create_warrior("Unit", 5, 5)
        unit.action_points = 3  # Partially spent
        
        unit.end_turn()
        
        self.assertEqual(unit.action_points, 8)  # Back to full

if __name__ == '__main__':
    unittest.main()