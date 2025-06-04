import unittest
import pygame
from game.entities.unit_factory import UnitFactory
from game.game_state import GameState

class TestAttackWithSelectedKnightHex(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game_state = GameState(vs_ai=False)
        self.game_state.knights.clear()
        self.game_state.current_player = 1
        self.attacker = UnitFactory.create_warrior("Attacker", 4, 4)
        self.attacker.player_id = 1
        self.game_state.knights.append(self.attacker)
        self.game_state.selected_knight = self.attacker

    def test_returns_false_when_no_target(self):
        result = self.game_state.attack_with_selected_knight_hex(5, 4)
        self.assertFalse(result)

    def test_returns_false_when_target_is_friendly(self):
        friend = UnitFactory.create_warrior("Friend", 5, 4)
        friend.player_id = 1
        self.game_state.knights.append(friend)
        result = self.game_state.attack_with_selected_knight_hex(5, 4)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
