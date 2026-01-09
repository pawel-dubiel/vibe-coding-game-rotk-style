"""Tests for combat breakaway mechanics"""
import unittest
import random
from unittest.mock import patch
from game.entities.knight import KnightClass
from game.entities.unit_factory import UnitFactory
from game.combat_config import CombatConfig

class MockTerrainType:
    """Mock terrain type for testing"""
    @property
    def value(self):
        return "Plains"

class MockTerrain:
    """Mock terrain for testing"""
    def __init__(self):
        self.type = MockTerrainType()
        self.movement_cost = 1
        
    def get_combat_modifier_for_unit(self, unit_class):
        return 1.0
    
    @property
    def defense_bonus(self):
        return 0

class MockTerrainMap:
    """Mock terrain map for testing"""
    def get_terrain(self, x, y):
        return MockTerrain()

class MockGameState:
    """Simple mock game state for testing"""
    def __init__(self):
        self.board_width = 10
        self.board_height = 10
        self.knights = []
        self.terrain_map = MockTerrainMap()

    def get_knight_at(self, x, y):
        for knight in self.knights:
            if knight.x == x and knight.y == y:
                return knight
        return None

class TestCombatBreakaway(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a simple mock game state
        self.game_state = MockGameState()
        
        # Create test units
        self.warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        self.archer = UnitFactory.create_archer("Test Archer", 6, 5)
        self.cavalry = UnitFactory.create_cavalry("Test Cavalry", 7, 5)
        self.mage = UnitFactory.create_mage("Test Mage", 8, 5)
        
        # Set different players
        self.warrior.player_id = 1
        self.archer.player_id = 2
        self.cavalry.player_id = 1
        self.mage.player_id = 2
        
        # Add to game state
        self.game_state.knights = [self.warrior, self.archer, self.cavalry, self.mage]
        
    def test_unit_weight_classification(self):
        """Test that units are correctly classified as heavy or light"""
        # Heavy units
        self.assertTrue(self.warrior.is_heavy_unit())
        self.assertFalse(self.warrior.is_light_unit())
        
        self.assertTrue(self.cavalry.is_heavy_unit())
        self.assertFalse(self.cavalry.is_light_unit())
        
        # Light units
        self.assertTrue(self.archer.is_light_unit())
        self.assertFalse(self.archer.is_heavy_unit())
        
        self.assertTrue(self.mage.is_light_unit())
        self.assertFalse(self.mage.is_heavy_unit())
        
    def test_breakaway_chances(self):
        """Test breakaway chance calculations"""
        # Light vs Heavy - should be 100%
        chance = CombatConfig.get_breakaway_chance("Warrior", "Archer")
        self.assertEqual(chance, 100)
        
        chance = CombatConfig.get_breakaway_chance("Cavalry", "Mage")
        self.assertEqual(chance, 100)
        
        # Light vs Light - should be 50%
        chance = CombatConfig.get_breakaway_chance("Archer", "Mage")
        self.assertEqual(chance, 50)
        
        chance = CombatConfig.get_breakaway_chance("Mage", "Archer")
        self.assertEqual(chance, 50)
        
        # Heavy vs Heavy - should be 0%
        chance = CombatConfig.get_breakaway_chance("Warrior", "Cavalry")
        self.assertEqual(chance, 0)
        
        chance = CombatConfig.get_breakaway_chance("Cavalry", "Warrior")
        self.assertEqual(chance, 0)
        
        # Heavy vs Light - should be 0%
        chance = CombatConfig.get_breakaway_chance("Archer", "Warrior")
        self.assertEqual(chance, 0)
        
        chance = CombatConfig.get_breakaway_chance("Mage", "Cavalry")
        self.assertEqual(chance, 0)
        
    def test_breakaway_requirements(self):
        """Test breakaway requirements"""
        # Engage units in combat
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.warrior
        self.warrior.is_engaged_in_combat = True
        self.warrior.engaged_with = self.archer
        
        # Archer (light) should be able to break away from warrior (heavy)
        self.assertTrue(self.archer.can_break_away_from(self.warrior))
        
        # Warrior (heavy) should not be able to break away from archer (light)
        self.assertFalse(self.warrior.can_break_away_from(self.archer))
        
        # Test insufficient AP
        self.archer.action_points = 1  # Less than required 2 AP
        self.assertFalse(self.archer.can_break_away_from(self.warrior))
        
        # Restore AP
        self.archer.action_points = 5
        self.assertTrue(self.archer.can_break_away_from(self.warrior))
        
    @patch('random.randint')
    def test_successful_breakaway(self, mock_randint):
        """Test successful breakaway attempt"""
        # Mock random to return 50 (should succeed with 100% chance)
        mock_randint.return_value = 50
        
        # Engage archer (light) with warrior (heavy)
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.warrior
        self.warrior.is_engaged_in_combat = True
        self.warrior.engaged_with = self.archer
        
        initial_ap = self.archer.action_points
        
        # Attempt breakaway
        result = self.archer.attempt_breakaway(self.warrior, self.game_state)
        
        # Should succeed (light vs heavy = 100% chance)
        self.assertTrue(result['success'])
        self.assertIn('successfully broke away', result['message'])
        self.assertTrue(result.get('opportunity_attack', False))
        
        # Check engagement status cleared
        self.assertFalse(self.archer.is_engaged_in_combat)
        self.assertIsNone(self.archer.engaged_with)
        self.assertFalse(self.warrior.is_engaged_in_combat)
        self.assertIsNone(self.warrior.engaged_with)
        
        # Check AP consumed
        self.assertEqual(self.archer.action_points, initial_ap - CombatConfig.BREAKAWAY_AP_COST)
        
    @patch('random.randint')
    def test_failed_breakaway(self, mock_randint):
        """Test failed breakaway attempt"""
        # Mock random to return 75 (should fail with 50% chance)
        mock_randint.return_value = 75
        
        # Engage two light units (50% chance)
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.mage
        self.mage.is_engaged_in_combat = True
        self.mage.engaged_with = self.archer
        
        initial_ap = self.archer.action_points
        initial_morale = self.archer.stats.stats.morale
        
        # Attempt breakaway
        result = self.archer.attempt_breakaway(self.mage, self.game_state)
        
        # Should fail 
        self.assertFalse(result['success'])
        self.assertIn('failed to break away', result['message'])
        
        # Check still engaged
        self.assertTrue(self.archer.is_engaged_in_combat)
        self.assertEqual(self.archer.engaged_with, self.mage)
        
        # Check AP consumed and morale lost
        self.assertEqual(self.archer.action_points, initial_ap - CombatConfig.BREAKAWAY_AP_COST)
        self.assertEqual(self.archer.stats.stats.morale, initial_morale - CombatConfig.FAILED_BREAKAWAY_MORALE_LOSS)
        
    @patch('random.randint')
    def test_breakaway_behavior(self, mock_randint):
        """Test the BreakawayBehavior class"""
        # Mock random to return 25 (should succeed with 100% chance)
        mock_randint.return_value = 25
        
        # Engage archer with warrior
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.warrior
        self.warrior.is_engaged_in_combat = True
        self.warrior.engaged_with = self.archer
        
        breakaway_behavior = self.archer.behaviors.get('breakaway')
        self.assertIsNotNone(breakaway_behavior)
        
        # Should be able to execute
        self.assertTrue(breakaway_behavior.can_execute(self.archer, self.game_state))
        
        # Test execution
        result = breakaway_behavior.execute(self.archer, self.game_state)
        self.assertTrue(result['success'])
        
        # Should include opportunity attack damage
        self.assertIn('opportunity_damage', result)
        
    def test_combat_engagement(self):
        """Test that combat properly engages units"""
        attack_behavior = self.warrior.behaviors.get('attack')
        self.assertIsNotNone(attack_behavior)
        
        # Position units adjacent
        self.archer.x = 5
        self.archer.y = 6
        
        # Execute attack
        result = attack_behavior.execute(self.warrior, self.game_state, target=self.archer)
        
        # Check units are engaged
        self.assertTrue(self.warrior.is_engaged_in_combat)
        self.assertEqual(self.warrior.engaged_with, self.archer)
        self.assertTrue(self.archer.is_engaged_in_combat)
        self.assertEqual(self.archer.engaged_with, self.warrior)
    
    def test_heavy_units_cannot_break_away(self):
        """Test that heavy units cannot break away from combat"""
        # Engage warrior (heavy) with archer (light)
        self.warrior.is_engaged_in_combat = True
        self.warrior.engaged_with = self.archer
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.warrior
        
        # Warrior should not be able to break away
        self.assertFalse(self.warrior.can_break_away_from(self.archer))
        
        # Attempt should fail
        result = self.warrior.attempt_breakaway(self.archer, self.game_state)
        self.assertFalse(result['success'])
        
    def test_heavy_vs_heavy_no_breakaway(self):
        """Test that heavy units cannot break away from each other"""
        # Engage warrior (heavy) with cavalry (heavy)
        self.warrior.is_engaged_in_combat = True
        self.warrior.engaged_with = self.cavalry
        self.cavalry.is_engaged_in_combat = True
        self.cavalry.engaged_with = self.warrior
        
        # Neither should be able to break away
        self.assertFalse(self.warrior.can_break_away_from(self.cavalry))
        self.assertFalse(self.cavalry.can_break_away_from(self.warrior))
        
    @patch('random.randint')
    def test_light_vs_light_50_percent_chance(self, mock_randint):
        """Test 50% breakaway chance for light vs light"""
        # Test successful breakaway (roll 25, chance is 50)
        mock_randint.return_value = 25
        
        # Engage two light units
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.mage
        self.mage.is_engaged_in_combat = True
        self.mage.engaged_with = self.archer
        
        result = self.archer.attempt_breakaway(self.mage, self.game_state)
        self.assertTrue(result['success'])
        
        # Reset engagement for next test
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.mage
        self.mage.is_engaged_in_combat = True
        self.mage.engaged_with = self.archer
        
        # Test failed breakaway (roll 75, chance is 50)
        mock_randint.return_value = 75
        result = self.archer.attempt_breakaway(self.mage, self.game_state)
        self.assertFalse(result['success'])
        
    def test_not_engaged_cannot_break_away(self):
        """Test that units not in combat cannot break away"""
        # Units not engaged
        self.archer.is_engaged_in_combat = False
        self.archer.engaged_with = None
        
        # Should not be able to break away
        self.assertFalse(self.archer.can_break_away_from(self.warrior))
        
        result = self.archer.attempt_breakaway(self.warrior, self.game_state)
        self.assertFalse(result['success'])
        
    def test_insufficient_ap_cannot_break_away(self):
        """Test that units with insufficient AP cannot break away"""
        # Engage units
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.warrior
        
        # Set AP below required amount
        self.archer.action_points = 1  # Less than required 2
        
        # Should not be able to break away
        self.assertFalse(self.archer.can_break_away_from(self.warrior))
        
        # Breakaway behavior should not be executable
        breakaway_behavior = self.archer.behaviors.get('breakaway')
        self.assertFalse(breakaway_behavior.can_execute(self.archer, self.game_state))
        
    def test_ap_cost_configuration(self):
        """Test that AP cost is configurable"""
        breakaway_behavior = self.archer.behaviors.get('breakaway')
        
        # Check AP cost matches configuration
        self.assertEqual(breakaway_behavior.get_ap_cost(), CombatConfig.BREAKAWAY_AP_COST)
        self.assertEqual(CombatConfig.BREAKAWAY_AP_COST, 2)  # Verify default value
        
    def test_morale_loss_configuration(self):
        """Test that morale loss is configurable"""
        # Verify default value
        self.assertEqual(CombatConfig.FAILED_BREAKAWAY_MORALE_LOSS, 10)
        
    @patch('random.randint')
    def test_opportunity_attack_damage(self, mock_randint):
        """Test opportunity attack damage calculation"""
        mock_randint.return_value = 50  # Successful breakaway
        
        # Engage archer with warrior
        self.archer.is_engaged_in_combat = True
        self.archer.engaged_with = self.warrior
        self.warrior.is_engaged_in_combat = True
        self.warrior.engaged_with = self.archer
        
        initial_soldiers = self.archer.soldiers
        
        # Execute breakaway through behavior (includes opportunity attack)
        breakaway_behavior = self.archer.behaviors.get('breakaway')
        result = breakaway_behavior.execute(self.archer, self.game_state)
        
        # Should succeed and take opportunity damage
        self.assertTrue(result['success'])
        self.assertIn('opportunity_damage', result)
        self.assertGreater(result['opportunity_damage'], 0)
        
        # Archer should have taken casualties
        self.assertLess(self.archer.soldiers, initial_soldiers)

if __name__ == '__main__':
    unittest.main()
