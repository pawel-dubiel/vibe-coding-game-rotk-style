import unittest
from unittest.mock import MagicMock
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.components.stats import UnitStats

class TestAIStateCloning(unittest.TestCase):
    def setUp(self):
        # Create a source unit with modified state
        self.unit = Unit("Test Knight", KnightClass.WARRIOR, 5, 5)
        self.unit.player_id = 1
        
        # Modify stats
        self.unit.action_points = 3
        self.unit.has_moved = True
        self.unit.has_acted = False
        self.unit.is_routing = True
        self.unit.in_enemy_zoc = True
        
        # Modify combat stats via component
        self.unit.stats.stats.current_soldiers = 50
        self.unit.stats.stats.morale = 20
        
        # Set temporary modifiers
        self.unit.temp_damage_multiplier = 1.5
        
        # Create a mock general (simple object)
        self.unit.generals = MagicMock()
        self.unit.generals.get_all_passive_bonuses.return_value = {'damage_bonus': 0.1}
        
        # Add behaviors manually since raw Unit() doesn't have them
        self.unit.behaviors = {'move': MagicMock(), 'attack': MagicMock()}

    def test_clone_has_same_attributes(self):
        """Test that the clone has all the modified attributes of the original"""
        clone = self.unit.clone_for_simulation()
        
        # Check basic primitive types
        self.assertEqual(clone.name, self.unit.name)
        self.assertEqual(clone.x, self.unit.x)
        self.assertEqual(clone.y, self.unit.y)
        self.assertEqual(clone.player_id, self.unit.player_id)
        
        # Check modified state
        self.assertEqual(clone.action_points, 3)
        self.assertTrue(clone.has_moved)
        self.assertFalse(clone.has_acted)
        self.assertTrue(clone.is_routing)
        self.assertTrue(clone.in_enemy_zoc)
        self.assertEqual(clone.temp_damage_multiplier, 1.5)
        
    def test_clone_stats_independence(self):
        """Test that modifying the clone's stats does not affect the original"""
        clone = self.unit.clone_for_simulation()
        
        # Verify initial sync
        self.assertEqual(clone.soldiers, 50)
        self.assertEqual(clone.morale, 20)
        
        # Modify clone
        clone.stats.stats.current_soldiers = 10
        clone.stats.stats.morale = 0
        clone.action_points = 0
        
        # Verify clone changed
        self.assertEqual(clone.soldiers, 10)
        self.assertEqual(clone.morale, 0)
        self.assertEqual(clone.action_points, 0)
        
        # Verify original stayed same
        self.assertEqual(self.unit.soldiers, 50)
        self.assertEqual(self.unit.morale, 20)
        self.assertEqual(self.unit.action_points, 3)
        
    def test_clone_behavior_access(self):
        """Test that behaviors are accessible on the clone"""
        clone = self.unit.clone_for_simulation()
        
        # Check if behaviors dict exists and has keys
        self.assertIn('move', clone.behaviors)
        self.assertIn('attack', clone.behaviors)
        
        # Check if we can access the shared behavior instances
        self.assertEqual(clone.behaviors['move'], self.unit.behaviors['move'])

    def test_clone_generals_shared(self):
        """Test that generals component is shared (read-only assumption for AI)"""
        clone = self.unit.clone_for_simulation()
        self.assertEqual(clone.generals, self.unit.generals)
        
        # Verify method calls work
        bonuses = clone.generals.get_all_passive_bonuses(clone)
        self.assertEqual(bonuses['damage_bonus'], 0.1)

if __name__ == '__main__':
    unittest.main()
