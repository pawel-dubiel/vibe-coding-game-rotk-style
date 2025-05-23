"""Test diagonal movement and attacks"""
import unittest
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.behaviors.movement import MovementBehavior
from game.behaviors.combat import AttackBehavior

class MockTerrain:
    def __init__(self):
        self.type = type('obj', (object,), {'value': 'Plains'})
        self.defense_bonus = 0
        
    def get_combat_modifier_for_unit(self, unit_class):
        return 1.0

class MockTerrainMap:
    def is_passable(self, x, y, unit_class):
        return True
        
    def get_terrain(self, x, y):
        return MockTerrain()
        
    def get_movement_cost(self, x, y, unit_class):
        return 1

class MockGameState:
    def __init__(self):
        self.board_width = 10
        self.board_height = 10
        self.knights = []
        self.castles = []
        self.terrain_map = MockTerrainMap()

class TestDiagonalMovement(unittest.TestCase):
    """Test diagonal movement capabilities"""
    
    def setUp(self):
        self.game_state = MockGameState()
        
    def test_diagonal_movement_possible(self):
        """Test that units can move diagonally"""
        unit = UnitFactory.create_warrior("Test", 5, 5)
        unit.player_id = 1
        self.game_state.knights = [unit]
        
        # Get possible moves
        move_behavior = unit.behaviors['move']
        moves = move_behavior.get_possible_moves(unit, self.game_state)
        
        # Check that diagonal moves are included
        self.assertIn((6, 6), moves)  # Down-right
        self.assertIn((6, 4), moves)  # Up-right
        self.assertIn((4, 6), moves)  # Down-left
        self.assertIn((4, 4), moves)  # Up-left
        
        # Also check orthogonal moves
        self.assertIn((6, 5), moves)  # Right
        self.assertIn((4, 5), moves)  # Left
        self.assertIn((5, 6), moves)  # Down
        self.assertIn((5, 4), moves)  # Up
        
    def test_diagonal_movement_range(self):
        """Test movement range includes diagonals at all distances"""
        unit = UnitFactory.create_cavalry("Cavalry", 5, 5)
        unit.player_id = 1
        self.game_state.knights = [unit]
        
        # Cavalry has 4 movement
        moves = unit.behaviors['move'].get_possible_moves(unit, self.game_state)
        
        # Check 2-tile diagonal moves
        self.assertIn((7, 7), moves)  # 2 diagonal down-right
        self.assertIn((3, 3), moves)  # 2 diagonal up-left
        
        # Check mixed moves (1 diagonal + orthogonal)
        self.assertIn((6, 7), moves)  # Right then down
        self.assertIn((7, 6), moves)  # Down then right
        
    def test_diagonal_blocked_by_enemy(self):
        """Test diagonal movement blocked by enemy units"""
        unit = UnitFactory.create_warrior("Player", 5, 5)
        unit.player_id = 1
        
        enemy = UnitFactory.create_warrior("Enemy", 6, 6)
        enemy.player_id = 2
        
        self.game_state.knights = [unit, enemy]
        
        moves = unit.behaviors['move'].get_possible_moves(unit, self.game_state)
        
        # Diagonal to enemy position should be blocked
        self.assertNotIn((6, 6), moves)
        
        # But other diagonals should be available
        self.assertIn((6, 4), moves)
        self.assertIn((4, 6), moves)
        self.assertIn((4, 4), moves)
        
    def test_diagonal_attack(self):
        """Test attacking diagonally adjacent enemies"""
        attacker = UnitFactory.create_warrior("Attacker", 5, 5)
        attacker.player_id = 1
        
        # Place enemy diagonally adjacent
        target = UnitFactory.create_warrior("Target", 6, 6)
        target.player_id = 2
        
        self.game_state.knights = [attacker, target]
        
        # Check attack is possible
        attack_behavior = attacker.behaviors['attack']
        targets = attack_behavior.get_valid_targets(attacker, self.game_state)
        
        self.assertIn(target, targets)
        
        # Execute attack
        result = attack_behavior.execute(attacker, self.game_state, target)
        self.assertTrue(result['success'])
        self.assertGreater(result['damage'], 0)
        self.assertGreater(result['counter_damage'], 0)  # Melee gets counter
        
    def test_diagonal_zone_of_control(self):
        """Test Zone of Control works diagonally"""
        unit = UnitFactory.create_warrior("Unit", 5, 5)
        unit.player_id = 1
        
        # Place enemy diagonally adjacent
        enemy = UnitFactory.create_warrior("Enemy", 6, 6)
        enemy.player_id = 2
        
        self.game_state.knights = [unit, enemy]
        
        # Check ZOC detection
        in_zoc, zoc_enemy = unit.is_in_enemy_zoc(self.game_state)
        self.assertTrue(in_zoc)
        self.assertEqual(zoc_enemy, enemy)
        
    def test_diagonal_cavalry_charge(self):
        """Test cavalry can charge diagonally"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 5, 5)
        cavalry.player_id = 1
        
        # Enemy diagonally adjacent
        target = UnitFactory.create_archer("Target", 6, 4)  # Up-right
        target.player_id = 2
        
        self.game_state.knights = [cavalry, target]
        
        # Get charge targets
        charge_behavior = cavalry.behaviors['cavalry_charge']
        targets = charge_behavior.get_valid_targets(cavalry, self.game_state)
        
        self.assertIn(target, targets)
        
        # Execute charge
        result = charge_behavior.execute(cavalry, self.game_state, target=target)
        self.assertTrue(result['success'])
        self.assertGreater(result['damage'], 0)
        
    def test_archer_diagonal_range(self):
        """Test archer can attack diagonally at range"""
        archer = UnitFactory.create_archer("Archer", 5, 5)
        archer.player_id = 1
        
        # Enemy 2 tiles away diagonally
        target = UnitFactory.create_warrior("Target", 7, 7)
        target.player_id = 2
        
        self.game_state.knights = [archer, target]
        
        # Archer has range 3 with their special attack behavior
        attack_behavior = archer.behaviors.get('archer_attack', archer.behaviors.get('attack'))
        targets = attack_behavior.get_valid_targets(archer, self.game_state)
        
        self.assertIn(target, targets)
        
        # Execute ranged attack
        result = attack_behavior.execute(archer, self.game_state, target)
        self.assertTrue(result['success'])
        self.assertGreater(result['damage'], 0)
        self.assertEqual(result['counter_damage'], 0)  # No counter at range
        
    def test_all_eight_directions(self):
        """Test all 8 directions are accessible"""
        unit = UnitFactory.create_warrior("Unit", 5, 5)
        unit.player_id = 1
        self.game_state.knights = [unit]
        
        moves = unit.behaviors['move'].get_possible_moves(unit, self.game_state)
        
        # All 8 adjacent squares should be reachable
        expected_adjacent = [
            (4, 4), (5, 4), (6, 4),  # Top row
            (4, 5),         (6, 5),  # Middle row (excluding self)
            (4, 6), (5, 6), (6, 6)   # Bottom row
        ]
        
        for pos in expected_adjacent:
            self.assertIn(pos, moves, f"Position {pos} should be reachable")
            
    def test_diagonal_friendly_formation(self):
        """Test formation breaking with diagonal movement"""
        unit1 = UnitFactory.create_warrior("Unit1", 5, 5)
        unit1.player_id = 1
        
        # Friendly unit diagonally adjacent
        unit2 = UnitFactory.create_warrior("Unit2", 6, 6)
        unit2.player_id = 1
        
        self.game_state.knights = [unit1, unit2]
        
        # Get possible moves
        moves = unit1.behaviors['move'].get_possible_moves(unit1, self.game_state)
        
        # Should be able to move to adjacent squares
        # When breaking formation, movement is limited but still possible
        self.assertTrue(len(moves) > 0, "Unit should have some moves available")
        
        # Check that we can move to positions maintaining formation
        self.assertIn((5, 6), moves)  # Stay adjacent to friendly
        self.assertIn((6, 5), moves)  # Stay adjacent to friendly

if __name__ == '__main__':
    unittest.main()