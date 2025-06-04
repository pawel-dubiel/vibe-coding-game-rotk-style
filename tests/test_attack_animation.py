import unittest
from game.animation import AttackAnimation
from game.entities.unit_factory import UnitFactory
from game.test_utils.mock_game_state import MockGameState

class TestAttackAnimation(unittest.TestCase):
    def setUp(self):
        self.game_state = MockGameState(create_terrain=False)
        self.archer = UnitFactory.create_archer("Archer", 1, 1)
        self.warrior = UnitFactory.create_warrior("Target", 3, 1)

    def test_ranged_animation_arrow(self):
        anim = AttackAnimation(self.archer, self.warrior, damage=5)
        # Start of animation
        anim.elapsed = 0.0
        anim.update(0.0)
        pos_start = anim.get_current_arrow_position()
        self.assertAlmostEqual(pos_start[0], self.archer.x)
        self.assertAlmostEqual(pos_start[1], self.archer.y)

        # Midway before hit
        anim.elapsed = anim.duration * 0.25
        anim.update(0.0)
        pos_mid = anim.get_current_arrow_position()
        self.assertIsNotNone(pos_mid)
        self.assertGreater(pos_mid[0], self.archer.x)
        self.assertLess(pos_mid[0], self.warrior.x)

        # After impact
        anim.elapsed = anim.duration * 0.6
        anim.update(0.0)
        self.assertIsNone(anim.get_current_arrow_position())

    def test_melee_animation_no_arrow(self):
        attacker = UnitFactory.create_warrior("Attacker", 1, 1)
        target = UnitFactory.create_warrior("Defender", 2, 1)
        anim = AttackAnimation(attacker, target, damage=5)
        anim.elapsed = anim.duration * 0.25
        anim.update(0.0)
        self.assertFalse(anim.is_ranged)
        self.assertIsNone(anim.get_current_arrow_position())

if __name__ == '__main__':
    unittest.main()
