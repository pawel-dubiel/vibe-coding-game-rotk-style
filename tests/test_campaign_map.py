"""Tests for simple campaign map."""
import unittest

from game.campaign import create_poland_campaign


class TestCampaignMap(unittest.TestCase):
    """Ensure armies move and battles trigger."""

    def test_move_and_battle(self):
        cmap = create_poland_campaign()
        cmap.move_army("Polish Army", "Neighbor Country")

        # Distance between locations is 5
        self.assertEqual(cmap.armies["Polish Army"].move_remaining, 5)

        for _ in range(5):
            cmap.advance_turn()

        self.assertEqual(cmap.armies["Polish Army"].location, "Neighbor Country")
        battle_loc = cmap.check_for_battle()
        self.assertEqual(battle_loc, "Neighbor Country")
