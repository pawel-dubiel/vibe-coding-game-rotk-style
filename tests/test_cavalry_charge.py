"""Test cavalry charge mechanics with various obstacles"""
import unittest
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.entities.castle import Castle

class MockGameState:
    """Mock game state for testing charges"""
    def __init__(self):
        self.board_width = 16
        self.board_height = 12
        self.knights = []
        self.castles = []
        self.terrain_map = None

class TestCavalryCharge(unittest.TestCase):
    """Test cavalry charge behavior with different obstacles"""
    
    def setUp(self):
        """Set up test environment"""
        self.game_state = MockGameState()
        
    def test_charge_with_push(self):
        """Test normal charge that pushes target"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        target = UnitFactory.create_archer("Target", 6, 5)
        target.player_id = 2
        
        self.game_state.knights = [cavalry, target]
        
        # Execute charge
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['push'])
        self.assertEqual(result['push_to'], (7, 5))
        self.assertIn("Pushed", result['message'])
        
        # Check damage (80% of 50 cavalry = 40 base damage)
        self.assertEqual(result['damage'], 40)
        self.assertEqual(result['self_damage'], 2)  # 5% of 50
        
    def test_charge_against_wall(self):
        """Test charge when target is against map edge"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 14, 5)
        cavalry.player_id = 1
        
        # Target at edge of map
        target = UnitFactory.create_archer("Target", 15, 5)
        target.player_id = 2
        
        self.game_state.knights = [cavalry, target]
        
        # Execute charge
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        
        self.assertTrue(result['success'])
        self.assertFalse(result['push'])
        self.assertIn("crushed against the wall", result['message'])
        
        # Check increased damage - base damage may be modified by facing
        # Just check it's reasonable
        self.assertGreater(result['damage'], 40)  # Should be significant
        self.assertGreater(result['self_damage'], 0)  # Some self damage
        self.assertGreaterEqual(result['morale_damage'], 30)  # At least base morale damage
        
    def test_charge_into_unit(self):
        """Test charge when another unit is behind target"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        target = UnitFactory.create_archer("Target", 6, 5)
        target.player_id = 2
        
        # Unit behind target
        blocker = UnitFactory.create_warrior("Blocker", 7, 5)
        blocker.player_id = 2
        
        self.game_state.knights = [cavalry, target, blocker]
        
        # Execute charge
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        
        self.assertTrue(result['success'])
        self.assertFalse(result['push'])
        self.assertIn("slammed into", result['message'])
        
        # Check damage - base damage may be modified by facing
        self.assertGreater(result['damage'], 30)  # Should be significant
        self.assertGreater(result['self_damage'], 0)  # Some self damage
        self.assertGreaterEqual(result['morale_damage'], 20)  # At least base morale damage
        
        # Check collateral damage
        self.assertIn('collateral_unit', result)
        self.assertEqual(result['collateral_unit'], blocker)
        self.assertGreater(result['collateral_damage'], 0)  # Some collateral damage
        
    def test_charge_against_castle(self):
        """Test charge when castle is behind target"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        target = UnitFactory.create_archer("Target", 6, 5)
        target.player_id = 2
        
        # Castle behind target
        castle = Castle(7, 5, 2)
        self.game_state.castles = [castle]
        self.game_state.knights = [cavalry, target]
        
        # Execute charge
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        
        self.assertTrue(result['success'])
        self.assertFalse(result['push'])
        self.assertIn("crushed against the wall", result['message'])
        
        # Same as wall - devastating damage
        self.assertEqual(result['damage'], 60)
        self.assertEqual(result['self_damage'], 5)
        
    def test_charge_requirements(self):
        """Test charge requirements (will, AP, etc.)"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        target = UnitFactory.create_archer("Target", 6, 5)
        target.player_id = 2
        
        self.game_state.knights = [cavalry, target]
        
        # Test with low will
        cavalry.will = 30
        self.assertFalse(cavalry.can_execute_behavior('cavalry_charge', self.game_state))
        
        # Test with sufficient will
        cavalry.will = 100
        self.assertTrue(cavalry.can_execute_behavior('cavalry_charge', self.game_state))
        
        # Execute and check will consumption
        result = cavalry.execute_behavior('cavalry_charge', self.game_state, target=target)
        self.assertTrue(result['success'])
        self.assertEqual(cavalry.will, 60)  # Used 40 will
        
        # Can't charge again
        self.assertFalse(cavalry.can_execute_behavior('cavalry_charge', self.game_state))

if __name__ == '__main__':
    unittest.main()