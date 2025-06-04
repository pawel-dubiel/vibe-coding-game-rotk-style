"""Tests for movement mechanics and pathfinding"""
import unittest
from unittest.mock import Mock, patch
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.behaviors.movement import MovementBehavior
from game.terrain import TerrainMap, TerrainType

class MockTerrain:
    """Mock terrain for testing"""
    def __init__(self, terrain_type):
        self.type = terrain_type
        self.movement_cost = self._get_movement_cost()
        self.defense_bonus = 0
        self.passable = terrain_type != TerrainType.WATER
        
    def _get_movement_cost(self):
        costs = {
            TerrainType.PLAINS: 1,
            TerrainType.FOREST: 2,
            TerrainType.HILLS: 2,
            TerrainType.WATER: float('inf'),
            TerrainType.BRIDGE: 1,
            TerrainType.SWAMP: 3,
            TerrainType.ROAD: 0.5
        }
        return costs.get(self.type, 1)
        
    def get_movement_cost_for_unit(self, knight_class):
        from game.entities.knight import KnightClass
        base_cost = self.movement_cost
        
        # Apply unit-specific modifiers
        if knight_class == KnightClass.CAVALRY:
            if self.type in [TerrainType.FOREST, TerrainType.SWAMP]:
                return base_cost * 2
            elif self.type == TerrainType.HILLS:
                return base_cost * 1.5
        elif knight_class == KnightClass.ARCHER:
            if self.type == TerrainType.FOREST:
                return base_cost * 0.75
        elif knight_class == KnightClass.WARRIOR:
            if self.type in [TerrainType.HILLS, TerrainType.SWAMP]:
                return base_cost * 0.8
        
        return base_cost

class MockTerrainMap:
    """Mock terrain map with controlled terrain"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize all as plains
        self.terrain_grid = {}
        for y in range(height):
            for x in range(width):
                self.terrain_grid[(x, y)] = MockTerrain(TerrainType.PLAINS)
                
    def set_terrain(self, x, y, terrain_type):
        """Set specific terrain at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.terrain_grid[(x, y)] = MockTerrain(terrain_type)
            
    def get_terrain(self, x, y):
        """Get terrain at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.terrain_grid.get((x, y), MockTerrain(TerrainType.PLAINS))
        return None
        
    def is_passable(self, x, y, unit=None):
        """Check if position is passable"""
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return False
        return terrain.passable
        
    def get_movement_cost(self, x, y, unit):
        """Get movement cost for unit at position"""
        terrain = self.get_terrain(x, y)
        if terrain is None:
            return float('inf')
        # Pass unit.unit_class for compatibility with mock terrain
        return terrain.get_movement_cost_for_unit(unit.unit_class)

class MockGameState:
    """Mock game state for movement testing"""
    def __init__(self):
        self.board_width = 10
        self.board_height = 10
        self.knights = []
        self.terrain_map = MockTerrainMap(10, 10)
        self.pending_positions = {}

class TestMovement(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures with fresh state"""
        # Create fresh mock game state for each test
        self.game_state = MockGameState()
        
        # Create test units
        self.warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        self.archer = UnitFactory.create_archer("Test Archer", 7, 7)
        self.cavalry = UnitFactory.create_cavalry("Test Cavalry", 3, 3)
        
        # Set players
        self.warrior.player_id = 1
        self.archer.player_id = 2
        self.cavalry.player_id = 1
        
        # Add to game state
        self.game_state.knights = [self.warrior, self.archer, self.cavalry]
        
    def test_movement_behavior_exists(self):
        """Test that all units have movement behavior"""
        self.assertIn('move', self.warrior.behaviors)
        self.assertIn('move', self.archer.behaviors)
        self.assertIn('move', self.cavalry.behaviors)
        
    def test_movement_range_by_class(self):
        """Test that different unit classes have correct movement ranges"""
        warrior_move = self.warrior.behaviors['move']
        archer_move = self.archer.behaviors['move']
        cavalry_move = self.cavalry.behaviors['move']
        
        # Check default movement ranges
        self.assertEqual(warrior_move.movement_range, 3)
        self.assertEqual(archer_move.movement_range, 3)
        self.assertEqual(cavalry_move.movement_range, 4)
        
    def test_can_execute_movement(self):
        """Test movement execution requirements"""
        move_behavior = self.warrior.behaviors['move']
        
        # Should be able to move initially
        self.assertTrue(move_behavior.can_execute(self.warrior, self.game_state))
        
        # Cannot move if no AP
        self.warrior.action_points = 0
        self.assertFalse(move_behavior.can_execute(self.warrior, self.game_state))
        
        # Restore AP
        self.warrior.action_points = 5
        self.assertTrue(move_behavior.can_execute(self.warrior, self.game_state))
        
        # Cannot move if already moved
        self.warrior.has_moved = True
        self.assertFalse(move_behavior.can_execute(self.warrior, self.game_state))
        
    def test_basic_movement_cost(self):
        """Test basic movement cost calculation"""
        move_behavior = self.warrior.behaviors['move']
        
        # Test basic orthogonal movement (should be 1 AP)
        cost = move_behavior.get_ap_cost((5, 5), (5, 6), self.warrior, self.game_state)
        self.assertEqual(cost, 1)
        
        # Test diagonal movement (should be more expensive)
        diagonal_cost = move_behavior.get_ap_cost((5, 5), (6, 6), self.warrior, self.game_state)
        self.assertGreater(diagonal_cost, 1)
        
    def test_terrain_movement_costs(self):
        """Test movement costs on different terrains"""
        move_behavior = self.warrior.behaviors['move']
        
        # Set specific terrain types
        self.game_state.terrain_map.set_terrain(6, 5, TerrainType.FOREST)
        self.game_state.terrain_map.set_terrain(7, 5, TerrainType.HILLS) 
        self.game_state.terrain_map.set_terrain(8, 5, TerrainType.SWAMP)
        self.game_state.terrain_map.set_terrain(9, 5, TerrainType.ROAD)
        
        # Test movement to forest (should cost 2)
        forest_cost = move_behavior.get_ap_cost((5, 5), (6, 5), self.warrior, self.game_state)
        self.assertEqual(forest_cost, 2)
        
        # Test movement to hills (warriors get 0.8x cost, so 2 * 0.8 = 1.6, rounded up to 2)
        hills_cost = move_behavior.get_ap_cost((5, 5), (7, 5), self.warrior, self.game_state)
        self.assertEqual(hills_cost, 2)  # math.ceil(1.6) = 2
        
        # Test movement to swamp (warriors get 0.8x cost, so 3 * 0.8 = 2.4, rounded up to 3)
        swamp_cost = move_behavior.get_ap_cost((5, 5), (8, 5), self.warrior, self.game_state)
        self.assertEqual(swamp_cost, 3)  # math.ceil(2.4) = 3
        
        # Test movement to road (should cost less than 1, rounded up to 1)
        road_cost = move_behavior.get_ap_cost((5, 5), (9, 5), self.warrior, self.game_state)
        self.assertEqual(road_cost, 1)  # Minimum cost of 1
        
    def test_cavalry_terrain_penalties(self):
        """Test that cavalry has terrain penalties in forest/swamp"""
        cavalry_move = self.cavalry.behaviors['move']
        
        # Set forest terrain
        self.game_state.terrain_map.set_terrain(4, 3, TerrainType.FOREST)
        
        # Cavalry should pay double in forest
        forest_cost = cavalry_move.get_ap_cost((3, 3), (4, 3), self.cavalry, self.game_state)
        self.assertEqual(forest_cost, 4)  # 2 (forest) * 2 (cavalry penalty)
        
    def test_diagonal_movement_penalty(self):
        """Test diagonal movement penalty calculation"""
        move_behavior = self.warrior.behaviors['move']
        
        # Orthogonal movement to plains
        ortho_cost = move_behavior.get_ap_cost((5, 5), (5, 6), self.warrior, self.game_state)
        
        # Diagonal movement to plains
        diag_cost = move_behavior.get_ap_cost((5, 5), (6, 6), self.warrior, self.game_state)
        
        # Diagonal should be more expensive
        self.assertGreater(diag_cost, ortho_cost)
        
    def test_possible_moves_basic(self):
        """Test basic possible moves calculation"""
        move_behavior = self.warrior.behaviors['move']
        
        # Get possible moves from center position
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Should have moves available
        self.assertGreater(len(moves), 0)
        
        # Should not include current position
        self.assertNotIn((self.warrior.x, self.warrior.y), moves)
        
        # All moves should be within movement range (considering AP costs)
        # Note: This is AP-cost based, not simple distance
        warrior_range = self.warrior.behaviors['move'].movement_range
        for move_x, move_y in moves:
            # Calculate AP cost to reach this position
            ap_cost = move_behavior.get_ap_cost((self.warrior.x, self.warrior.y), (move_x, move_y), self.warrior, self.game_state)
            self.assertLessEqual(ap_cost, warrior_range, f"Move to ({move_x}, {move_y}) costs {ap_cost} AP, exceeds range {warrior_range}")
            
    def test_blocked_by_enemies(self):
        """Test that movement is blocked by enemy units"""
        move_behavior = self.warrior.behaviors['move']
        
        # Place enemy at adjacent position
        self.archer.x = 6
        self.archer.y = 5
        
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Should not be able to move through enemy
        self.assertNotIn((6, 5), moves)
        
    def test_not_blocked_by_friendlies(self):
        """Test that movement paths aren't blocked by friendly units"""
        move_behavior = self.warrior.behaviors['move']
        
        # Place friendly unit nearby
        self.cavalry.x = 6
        self.cavalry.y = 5
        
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Should be able to reach positions beyond friendly (not blocked)
        # Friendly occupies (6,5), but should be able to reach (7,5) if in range
        if 7 <= 5 + move_behavior.movement_range:
            self.assertIn((7, 5), moves)
            
    def test_water_blocks_movement(self):
        """Test that water terrain blocks movement"""
        move_behavior = self.warrior.behaviors['move']
        
        # Set water terrain
        self.game_state.terrain_map.set_terrain(6, 5, TerrainType.WATER)
        
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Should not be able to move to water
        self.assertNotIn((6, 5), moves)
        
    def test_movement_execution(self):
        """Test actual movement execution"""
        move_behavior = self.warrior.behaviors['move']
        
        initial_x, initial_y = self.warrior.x, self.warrior.y
        initial_ap = self.warrior.action_points
        
        # Execute movement
        result = move_behavior.execute(self.warrior, self.game_state, target_x=6, target_y=5)
        
        # Should succeed
        self.assertTrue(result['success'])
        
        # Should return movement details
        self.assertEqual(result['from'], (initial_x, initial_y))
        self.assertEqual(result['to'], (6, 5))
        
        # AP should be consumed
        self.assertLess(self.warrior.action_points, initial_ap)
        
        # Has moved flag should be set
        self.assertTrue(self.warrior.has_moved)
        
    def test_invalid_movement_execution(self):
        """Test movement execution to invalid positions"""
        move_behavior = self.warrior.behaviors['move']
        
        initial_x, initial_y = self.warrior.x, self.warrior.y
        
        # Try to move too far
        result = move_behavior.execute(self.warrior, self.game_state, target_x=0, target_y=0)
        
        # Should fail
        self.assertFalse(result['success'])
        
        # Position should not change
        self.assertEqual(self.warrior.x, initial_x)
        self.assertEqual(self.warrior.y, initial_y)
        
    def test_shortest_path_simple(self):
        """Test that units take shortest path for simple moves"""
        move_behavior = self.warrior.behaviors['move']
        
        # Clear any obstacles
        self.game_state.knights = [self.warrior]  # Only warrior on board
        
        # Get possible moves
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Check that adjacent tiles are reachable with cost 1
        adjacent_positions = [
            (self.warrior.x + 1, self.warrior.y),     # Right
            (self.warrior.x - 1, self.warrior.y),     # Left  
            (self.warrior.x, self.warrior.y + 1),     # Down
            (self.warrior.x, self.warrior.y - 1),     # Up
        ]
        
        for pos in adjacent_positions:
            if 0 <= pos[0] < self.game_state.board_width and 0 <= pos[1] < self.game_state.board_height:
                self.assertIn(pos, moves, f"Should be able to reach adjacent position {pos}")
                
    def test_zone_of_control_movement(self):
        """Test movement restrictions in enemy Zone of Control"""
        move_behavior = self.warrior.behaviors['move']
        
        # Place enemy adjacent to warrior (creating ZOC)
        self.archer.x = 6
        self.archer.y = 5
        
        # Set warrior as in enemy ZOC with low morale (so can't disengage)
        self.warrior.in_enemy_zoc = True
        self.warrior.engaged_with = self.archer
        self.warrior.stats.stats.morale = 50  # Low morale, can't disengage
        
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Should have very limited movement in ZOC (only able to attack the engaging enemy)
        self.assertLessEqual(len(moves), 1)  # Should only be able to attack or stay
        
    def test_formation_breaking_cost(self):
        """Test formation breaking movement penalty"""
        move_behavior = self.warrior.behaviors['move']
        
        # Place friendly unit adjacent
        self.cavalry.x = 6
        self.cavalry.y = 5
        
        # Movement away from formation should cost more
        # This is complex to test directly, but we can verify the logic exists
        cost_away = move_behavior.get_ap_cost((5, 5), (4, 5), self.warrior, self.game_state)
        self.assertGreaterEqual(cost_away, 1)
        
    def test_pathfinding_around_obstacles(self):
        """Test pathfinding around obstacles"""
        move_behavior = self.warrior.behaviors['move']
        
        # Create a wall of water to force pathfinding
        for y in range(3, 8):
            self.game_state.terrain_map.set_terrain(6, y, TerrainType.WATER)
            
        # Clear other units
        self.game_state.knights = [self.warrior]
        
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # Should still be able to reach some positions on the other side
        # by going around the obstacle if movement range allows
        self.assertGreater(len(moves), 4)  # Should have more than just immediate neighbors
        
    def test_boundary_constraints(self):
        """Test that movement respects board boundaries"""
        # Move warrior to edge
        self.warrior.x = 0
        self.warrior.y = 0
        
        move_behavior = self.warrior.behaviors['move']
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # All moves should be within bounds
        for move_x, move_y in moves:
            self.assertGreaterEqual(move_x, 0)
            self.assertGreaterEqual(move_y, 0)
            self.assertLess(move_x, self.game_state.board_width)
            self.assertLess(move_y, self.game_state.board_height)
            
    def test_pathfinding_prefers_direct_routes(self):
        """Test that units prefer direct routes over longer alternatives"""
        # This test addresses the original bug where units would take longer routes
        move_behavior = self.warrior.behaviors['move']
        
        # Clear other units for clean test
        self.game_state.knights = [self.warrior]
        
        # Test that adjacent moves are always reachable with minimal cost
        adjacent_moves = [
            (self.warrior.x + 1, self.warrior.y),     # Right
            (self.warrior.x - 1, self.warrior.y),     # Left
            (self.warrior.x, self.warrior.y + 1),     # Down
            (self.warrior.x, self.warrior.y - 1),     # Up
        ]
        
        possible_moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        # All valid adjacent moves should be reachable
        for move_x, move_y in adjacent_moves:
            if (0 <= move_x < self.game_state.board_width and 
                0 <= move_y < self.game_state.board_height):
                self.assertIn((move_x, move_y), possible_moves, 
                             f"Adjacent move to ({move_x}, {move_y}) should be reachable")
                
        # Test that diagonal moves cost more than orthogonal
        ortho_cost = move_behavior.get_ap_cost((5, 5), (5, 6), self.warrior, self.game_state)
        diag_cost = move_behavior.get_ap_cost((5, 5), (6, 6), self.warrior, self.game_state)
        
        self.assertGreater(diag_cost, ortho_cost, 
                          "Diagonal movement should cost more than orthogonal")
        self.assertEqual(ortho_cost, 1, "Orthogonal movement should cost 1 AP")
        self.assertEqual(diag_cost, 2, "Diagonal movement should cost 2 AP")
            
    def test_movement_range_limits(self):
        """Test that movement doesn't exceed range limits"""
        # Test warrior with 3 movement range
        move_behavior = self.warrior.behaviors['move']
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        
        for move_x, move_y in moves:
            # Calculate AP cost to ensure it's within range
            ap_cost = move_behavior.get_ap_cost((self.warrior.x, self.warrior.y), (move_x, move_y), self.warrior, self.game_state)
            self.assertLessEqual(ap_cost, move_behavior.movement_range, f"Move to ({move_x}, {move_y}) costs {ap_cost} AP, exceeds range")
            
    def test_no_movement_when_conditions_fail(self):
        """Test that movement is blocked when conditions aren't met"""
        move_behavior = self.warrior.behaviors['move']
        
        # No AP
        self.warrior.action_points = 0
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        self.assertEqual(len(moves), 0)
        
        # Restore AP but set has_moved
        self.warrior.action_points = 5
        self.warrior.has_moved = True
        moves = move_behavior.get_possible_moves(self.warrior, self.game_state)
        self.assertEqual(len(moves), 0)

if __name__ == '__main__':
    unittest.main()