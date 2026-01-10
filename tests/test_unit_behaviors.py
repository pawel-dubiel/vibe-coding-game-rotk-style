"""Unit tests for the refactored unit and behavior system"""
import unittest
from game.entities.unit import Unit
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.behaviors.movement import MovementBehavior
from game.behaviors.combat import AttackBehavior
from game.behaviors.special_abilities import CavalryChargeBehavior

class MockTerrainType:
    """Mock terrain type"""
    def __init__(self, value="Plains"):
        self.value = value

class MockTerrain:
    """Mock terrain for testing"""
    def __init__(self):
        self.defense_bonus = 0
        self.type = MockTerrainType()
        self.movement_cost = 1
        
    def get_combat_modifier_for_unit(self, unit_class):
        return 1.0

class MockTerrainMap:
    """Mock terrain map for testing"""
    def is_passable(self, x, y, unit_class):
        return True
        
    def get_terrain(self, x, y):
        return MockTerrain()
        
    def get_movement_cost(self, x, y, unit_class):
        return 1

class MockGameState:
    """Mock game state for testing"""
    def __init__(self):
        self.board_width = 16
        self.board_height = 12
        self.knights = []
        self.castles = []
        self.terrain_map = MockTerrainMap()

    def get_knight_at(self, x, y):
        for knight in self.knights:
            if knight.x == x and knight.y == y:
                return knight
        return None

class TestUnitBehaviors(unittest.TestCase):
    """Test unit behavior system"""
    
    def setUp(self):
        """Set up test units and game state"""
        self.game_state = MockGameState()
        
    def test_unit_creation(self):
        """Test creating units with factory"""
        warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        self.assertEqual(warrior.name, "Test Warrior")
        self.assertEqual(warrior.unit_class, KnightClass.WARRIOR)
        self.assertEqual(warrior.x, 5)
        self.assertEqual(warrior.y, 5)
        self.assertEqual(warrior.soldiers, 100)
        
        # Check behaviors were added
        self.assertIn('move', warrior.behaviors)
        self.assertIn('attack', warrior.behaviors)
        self.assertNotIn('cavalry_charge', warrior.behaviors)
        
    def test_cavalry_has_charge(self):
        """Test cavalry units have charge behavior"""
        cavalry = UnitFactory.create_cavalry("Test Cavalry", 3, 3)
        self.assertIn('cavalry_charge', cavalry.behaviors)
        self.assertEqual(cavalry.soldiers, 50)
        self.assertEqual(cavalry.will, 100)
        
    def test_movement_behavior(self):
        """Test movement behavior"""
        warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        warrior.player_id = 1
        self.game_state.knights = [warrior]
        
        # Check can move
        self.assertTrue(warrior.can_execute_behavior('move', self.game_state))
        
        # Execute move
        result = warrior.execute_behavior('move', self.game_state, target_x=6, target_y=5)
        self.assertEqual(result['from'], (5, 5))
        self.assertEqual(result['to'], (6, 5))
        self.assertTrue(warrior.has_moved)
        # Warriors start with 8 AP, movement cost depends on terrain
        self.assertLess(warrior.action_points, 8)  # Should have used some AP
        self.assertGreater(warrior.action_points, 0)  # But not all of it
        
    def test_attack_behavior(self):
        """Test attack behavior"""
        attacker = UnitFactory.create_warrior("Attacker", 5, 5)
        attacker.player_id = 1
        
        defender = UnitFactory.create_warrior("Defender", 6, 5)
        defender.player_id = 2
        
        self.game_state.knights = [attacker, defender]
        
        # Check can attack
        self.assertTrue(attacker.can_execute_behavior('attack', self.game_state))
        
        # Execute attack
        result = attacker.execute_behavior('attack', self.game_state, target=defender)
        self.assertTrue(result['success'])
        self.assertGreater(result['damage'], 0)
        self.assertGreater(result['counter_damage'], 0)  # Melee has counter damage

    def test_routing_units_cannot_attack(self):
        """Test routing units cannot attack"""
        attacker = UnitFactory.create_warrior("Attacker", 5, 5)
        attacker.player_id = 1
        attacker.is_routing = True

        defender = UnitFactory.create_warrior("Defender", 6, 5)
        defender.player_id = 2

        self.game_state.knights = [attacker, defender]

        self.assertFalse(attacker.can_execute_behavior('attack', self.game_state))

    def test_routing_units_cannot_move(self):
        """Test routing units cannot move"""
        mover = UnitFactory.create_warrior("Mover", 5, 5)
        mover.player_id = 1
        mover.is_routing = True
        next_tile = (6, 5)

        self.game_state.knights = [mover]

        possible_moves = mover.get_possible_moves(
            self.game_state.board_width,
            self.game_state.board_height,
            self.game_state.terrain_map,
            self.game_state,
        )
        self.assertNotIn(next_tile, possible_moves)
        self.assertFalse(mover.can_move())
        
    def test_cavalry_charge(self):
        """Test cavalry charge behavior"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        target = UnitFactory.create_archer("Archer", 6, 5)
        target.player_id = 2
        
        self.game_state.knights = [cavalry, target]
        
        # Check can charge
        self.assertTrue(cavalry.can_execute_behavior('cavalry_charge', self.game_state))
        
        # Execute charge
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        self.assertTrue(result['success'])
        self.assertGreater(result['damage'], 0)
        self.assertEqual(cavalry.will, 60)  # Used 40 will
        
    def test_behavior_removal(self):
        """Test removing behaviors"""
        warrior = UnitFactory.create_warrior("Test", 0, 0)
        
        # Remove attack behavior
        warrior.remove_behavior('attack')
        self.assertNotIn('attack', warrior.behaviors)
        self.assertFalse(warrior.can_execute_behavior('attack', self.game_state))
        
    def test_custom_behavior(self):
        """Test adding custom behaviors"""
        
        class TestBehavior(AttackBehavior):
            def __init__(self):
                super().__init__(attack_range=5)
                self.name = "long_range_attack"
                
        warrior = UnitFactory.create_warrior("Test", 0, 0)
        warrior.add_behavior(TestBehavior())
        
        self.assertIn('long_range_attack', warrior.behaviors)
        self.assertEqual(warrior.behaviors['long_range_attack'].attack_range, 5)
        
    def test_stats_component(self):
        """Test stats component"""
        warrior = UnitFactory.create_warrior("Test", 0, 0)
        
        # Take casualties
        initial_cohesion = warrior.cohesion
        warrior.stats.take_casualties(25)
        self.assertEqual(warrior.soldiers, 75)
        # Morale might be boosted by generals, check raw morale instead
        self.assertLess(warrior.stats.stats.morale, 100)
        self.assertLess(warrior.cohesion, initial_cohesion)
        
        # Consume will
        self.assertTrue(warrior.stats.consume_will(50))
        self.assertEqual(warrior.will, 50)
        self.assertFalse(warrior.stats.consume_will(60))  # Not enough
        
        # Regenerate will
        warrior.stats.regenerate_will(30)
        self.assertEqual(warrior.will, 80)

if __name__ == '__main__':
    unittest.main()
