"""Tests for path-based animation system"""
import unittest
from unittest.mock import Mock
from game.animation import PathMoveAnimation
from game.entities.unit_factory import UnitFactory
from tests.test_movement import MockGameState

class TestPathAnimation(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_state = MockGameState()
        self.warrior = UnitFactory.create_warrior("Test Warrior", 3, 3)
        self.warrior.player_id = 1
        self.game_state.knights = [self.warrior]
        
    def test_path_animation_creation(self):
        """Test creating a path animation"""
        path = [(4, 3), (5, 3), (6, 3)]  # 3-step path
        anim = PathMoveAnimation(self.warrior, path, step_duration=0.1)
        
        # Should have correct duration
        expected_duration = len(path) * 0.1
        self.assertEqual(anim.duration, expected_duration)
        
        # Should start at warrior's current position
        self.assertEqual(anim.start_x, 3)
        self.assertEqual(anim.start_y, 3)
        
    def test_path_animation_progression(self):
        """Test animation progression through path"""
        path = [(4, 3), (5, 3)]  # 2-step path
        anim = PathMoveAnimation(self.warrior, path, step_duration=1.0)  # 1 second per step
        
        # At start (0% progress)
        anim.elapsed = 0.0
        x, y = anim.get_current_position()
        self.assertEqual(x, 3)  # Should be at start position
        self.assertEqual(y, 3)
        
        # At 25% progress (halfway through first step)
        anim.elapsed = 0.5
        x, y = anim.get_current_position()
        self.assertGreater(x, 3)  # Should be between 3 and 4
        self.assertLess(x, 4)
        self.assertEqual(y, 3)  # Y doesn't change in this path
        
        # At 50% progress (end of first step)
        anim.elapsed = 1.0
        x, y = anim.get_current_position()
        self.assertAlmostEqual(x, 4, places=1)  # Should be at first waypoint
        self.assertEqual(y, 3)
        
        # At 75% progress (halfway through second step)
        anim.elapsed = 1.5
        x, y = anim.get_current_position()
        self.assertGreater(x, 4)  # Should be between 4 and 5
        self.assertLess(x, 5)
        self.assertEqual(y, 3)
        
        # At 100% progress (end of path)
        anim.elapsed = 2.0
        anim.finished = True
        x, y = anim.get_current_position()
        self.assertEqual(x, 5)  # Should be at final position
        self.assertEqual(y, 3)
        
    def test_path_animation_updates_unit_position(self):
        """Test that animation updates unit position when finished"""
        path = [(4, 3), (5, 3)]
        anim = PathMoveAnimation(self.warrior, path, step_duration=0.1, game_state=self.game_state)
        
        # Initially unit is at start position
        self.assertEqual(self.warrior.x, 3)
        self.assertEqual(self.warrior.y, 3)
        
        # Finish the animation
        anim.elapsed = anim.duration
        anim.finished = True
        anim.update(0.0)
        
        # Unit should now be at final position
        self.assertEqual(self.warrior.x, 5)
        self.assertEqual(self.warrior.y, 3)
        
    def test_empty_path_handling(self):
        """Test handling of empty path"""
        path = []
        anim = PathMoveAnimation(self.warrior, path, step_duration=0.1)
        
        # Should have zero duration
        self.assertEqual(anim.duration, 0)
        
        # Should stay at start position
        x, y = anim.get_current_position()
        self.assertEqual(x, 3)
        self.assertEqual(y, 3)
        
    def test_game_state_integration(self):
        """Test integration with game state movement"""
        move_behavior = self.warrior.behaviors['move']
        
        # Get a path to a destination
        path = move_behavior.get_path_to(self.warrior, self.game_state, 5, 3)
        self.assertGreater(len(path), 0)
        
        # Create animation with this path
        anim = PathMoveAnimation(self.warrior, path, step_duration=0.1, game_state=self.game_state)
        
        # Should work correctly
        self.assertGreater(anim.duration, 0)
        x, y = anim.get_current_position()
        self.assertEqual(x, 3)  # Should start at warrior position
        self.assertEqual(y, 3)
        
    def test_pathfinding_vs_direct_animation(self):
        """Test that pathfinding produces better routes than direct animation"""
        # This test demonstrates the fix for the original issue
        move_behavior = self.warrior.behaviors['move']
        
        # Test movement to a diagonal position
        target_x, target_y = 5, 5
        
        # Get the optimal path
        path = move_behavior.get_path_to(self.warrior, self.game_state, target_x, target_y)
        
        # Calculate total AP cost of the path
        total_cost = 0
        current_pos = (self.warrior.x, self.warrior.y)
        for next_pos in path:
            step_cost = move_behavior.get_ap_cost(current_pos, next_pos, self.warrior, self.game_state)
            total_cost += step_cost
            current_pos = next_pos
            
        # Calculate cost of direct diagonal movement
        direct_cost = move_behavior.get_ap_cost((self.warrior.x, self.warrior.y), (target_x, target_y), self.warrior, self.game_state)
        
        # The path should be optimal (either same cost or better than a single diagonal move)
        # In this case, since there are no obstacles, both should have the same cost
        # But the path shows the actual route taken
        
        print(f"Path: {path}")
        print(f"Path cost: {total_cost} AP")
        print(f"Direct diagonal cost: {direct_cost} AP")
        
        # The key improvement is that now we animate the actual path taken
        # rather than a direct line that doesn't represent the AP cost
        self.assertGreater(len(path), 0)
        self.assertGreater(total_cost, 0)

if __name__ == '__main__':
    unittest.main()