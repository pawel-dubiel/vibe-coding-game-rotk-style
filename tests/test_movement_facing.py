"""Test movement facing behavior including auto-facing"""
import unittest
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.components.facing import FacingDirection

class TestMovementFacing(unittest.TestCase):
    """Test automatic facing after movement"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_state = MockGameState(20, 20)
        
        # Create a warrior with movement behavior
        self.warrior = UnitFactory.create_warrior("Warrior", 5, 5)
        self.warrior.player_id = 1
        self.game_state.add_knight(self.warrior)
        
        # Create an enemy warrior
        self.enemy = UnitFactory.create_warrior("Enemy", 10, 5)
        self.enemy.player_id = 2
        self.game_state.add_knight(self.enemy)
        
    def test_auto_face_adjacent_enemy(self):
        """Test unit automatically faces enemy when ending movement adjacent"""
        move_behavior = self.warrior.behaviors['move']
        
        # Move enemy closer to warrior's movement range
        self.enemy.x = 7
        self.enemy.y = 5
        
        # Move warrior next to enemy
        result = move_behavior.execute(self.warrior, self.game_state, 6, 5)
        self.assertTrue(result['success'])
        self.assertTrue(result['auto_faced'])
        
        
        # Warrior should now face east towards the enemy
        self.assertEqual(self.warrior.facing.facing, FacingDirection.EAST)
        
    def test_auto_face_two_hexes_away(self):
        """Test unit automatically faces enemy when ending movement 2 hexes away"""
        move_behavior = self.warrior.behaviors['move']
        
        # Move enemy closer
        self.enemy.x = 8
        self.enemy.y = 5
        
        # Move warrior 2 hexes from enemy
        result = move_behavior.execute(self.warrior, self.game_state, 6, 5)
        self.assertTrue(result['success'])
        self.assertTrue(result['auto_faced'])
        
        # Manually update position
        self.warrior.x = 6
        self.warrior.y = 5
        
        # Warrior should face east towards the enemy
        self.assertEqual(self.warrior.facing.facing, FacingDirection.EAST)
        
    def test_no_auto_face_far_enemy(self):
        """Test unit doesn't auto-face when enemy is far away"""
        move_behavior = self.warrior.behaviors['move']
        
        # Set initial facing
        self.warrior.facing.facing = FacingDirection.NORTH_EAST
        
        # Move warrior but stay far from enemy
        result = move_behavior.execute(self.warrior, self.game_state, 4, 5)
        self.assertTrue(result['success'])
        self.assertFalse(result['auto_faced'])
        
        # Warrior should maintain facing based on movement direction
        # Since moving west, should face west
        self.assertEqual(self.warrior.facing.facing, FacingDirection.WEST)
        
    def test_manual_facing_selection(self):
        """Test manual facing selection when no enemies nearby"""
        move_behavior = self.warrior.behaviors['move']
        
        # Set initial facing
        self.warrior.facing.facing = FacingDirection.EAST
        
        # Move warrior east with specific final facing (one turn clockwise from EAST)
        result = move_behavior.execute(self.warrior, self.game_state, 6, 5, 
                                     final_facing=FacingDirection.SOUTH_EAST.value)
        self.assertTrue(result['success'])
        self.assertFalse(result['auto_faced'])
        
        # Warrior moved east, so faces EAST, then rotates to SOUTH_EAST (valid 60 degree turn)
        self.assertEqual(self.warrior.facing.facing, FacingDirection.SOUTH_EAST)
        
    def test_invalid_manual_facing(self):
        """Test that invalid manual facing (>60 degrees) is rejected"""
        move_behavior = self.warrior.behaviors['move']
        
        # Set initial facing
        self.warrior.facing.facing = FacingDirection.EAST
        
        # Move east and try to rotate more than 60 degrees (from EAST to WEST = 180 degrees)
        result = move_behavior.execute(self.warrior, self.game_state, 6, 5,
                                     final_facing=FacingDirection.WEST.value)
        self.assertTrue(result['success'])
        
        # Warrior moved east so faces EAST, cannot rotate 180 degrees to WEST
        self.assertEqual(self.warrior.facing.facing, FacingDirection.EAST)
        
    def test_auto_face_nearest_of_multiple_enemies(self):
        """Test unit faces nearest enemy when multiple are nearby"""
        # Move first enemy farther
        self.enemy.x = 8
        self.enemy.y = 5
        
        # Add another enemy closer than the first
        closer_enemy = UnitFactory.create_archer("Closer Enemy", 7, 5)
        closer_enemy.player_id = 2
        self.game_state.add_knight(closer_enemy)
        
        move_behavior = self.warrior.behaviors['move']
        
        # Move warrior between enemies, but closer to the archer
        result = move_behavior.execute(self.warrior, self.game_state, 6, 5)
        self.assertTrue(result['success'])
        self.assertTrue(result['auto_faced'])
        
        # Manually update position
        self.warrior.x = 6
        self.warrior.y = 5
        
        # Warrior should face east towards the closer enemy
        self.assertEqual(self.warrior.facing.facing, FacingDirection.EAST)
        
    def test_valid_rotation_calculation(self):
        """Test the rotation validation logic"""
        move_behavior = self.warrior.behaviors['move']
        
        # Test adjacent rotations (valid)
        self.assertTrue(move_behavior._is_valid_rotation(0, 1))  # NE to E
        self.assertTrue(move_behavior._is_valid_rotation(1, 0))  # E to NE
        self.assertTrue(move_behavior._is_valid_rotation(5, 0))  # NW to NE (wrap)
        self.assertTrue(move_behavior._is_valid_rotation(0, 5))  # NE to NW (wrap)
        
        # Test same facing (valid)
        self.assertTrue(move_behavior._is_valid_rotation(3, 3))  # SW to SW
        
        # Test too large rotations (invalid)
        self.assertFalse(move_behavior._is_valid_rotation(0, 2))  # NE to SE (120°)
        self.assertFalse(move_behavior._is_valid_rotation(0, 3))  # NE to SW (180°)
        self.assertFalse(move_behavior._is_valid_rotation(1, 4))  # E to W (180°)
        
    def test_movement_updates_facing_before_auto_face(self):
        """Test that movement animation updates facing, then auto-face overrides if needed"""
        # Place enemy to the north
        self.enemy.x = 5
        self.enemy.y = 3
        
        move_behavior = self.warrior.behaviors['move']
        
        # Move warrior north (should face north initially, then auto-face stays north)
        result = move_behavior.execute(self.warrior, self.game_state, 5, 4)
        self.assertTrue(result['success'])
        self.assertTrue(result['auto_faced'])
        
        
        # Should face towards enemy (which is directly north, no diagonal)
        # Since warrior moved from (5,5) to (5,4) and enemy is at (5,3), they are in same column
        # This should make warrior face north-west (due to odd column hex geometry)
        self.assertEqual(self.warrior.facing.facing, FacingDirection.NORTH_WEST)
        
    def test_simple_move_updates_facing(self):
        """Test that simple movement updates facing direction"""
        # Remove enemy to avoid auto-facing
        self.game_state.knights.remove(self.enemy)
        
        # Test basic movements
        # Note: In hex grid with odd-r offset, vertical movement depends on column parity
        test_cases = [
            ((6, 5), FacingDirection.EAST),       # Move east
            ((5, 4), FacingDirection.NORTH_WEST),  # Move north from odd column
            ((4, 5), FacingDirection.WEST),       # Move west
            ((5, 6), FacingDirection.SOUTH_WEST),  # Move south from odd column
        ]
        
        for (target_x, target_y), expected_facing in test_cases:
            # Reset warrior position
            self.warrior.x = 5
            self.warrior.y = 5
            self.warrior.has_moved = False
            self.warrior.action_points = 10
            
            # Execute movement
            result = self.warrior.behaviors['move'].execute(self.warrior, self.game_state, target_x, target_y)
            self.assertTrue(result['success'])
            
            # Check facing after move
            self.assertEqual(self.warrior.facing.facing, expected_facing,
                           f"Failed for move to ({target_x}, {target_y})")

if __name__ == '__main__':
    unittest.main()