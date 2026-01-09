"""Detailed engagement state transition tests."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.test_utils.mock_game_state import MockGameState
from game.combat_config import CombatConfig


class TestEngagementStateTransitions:
    """Verify engagement status transitions across common combat edge cases."""

    def setup_method(self):
        self.game_state = MockGameState(board_width=12, board_height=12)

    def _prepare_melee_pair(self):
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 5, 5)
        defender = UnitFactory.create_unit("Defender", KnightClass.WARRIOR, 6, 5)
        attacker.player_id = 1
        defender.player_id = 2
        attacker.stats.stats.current_soldiers = 10
        defender.stats.stats.current_soldiers = 10
        self.game_state.add_knight(attacker)
        self.game_state.add_knight(defender)
        return attacker, defender

    def _engage_units(self, attacker, defender):
        result = attacker.behaviors['attack'].execute(attacker, self.game_state, defender)
        assert result['success']
        return result

    def _reset_combat_state(self, *units):
        for unit in units:
            unit.is_routing = False
            unit.morale = unit.stats.stats.max_morale
            unit.cohesion = unit.max_cohesion

    def _reset_positions(self, attacker, defender):
        attacker.x = 5
        attacker.y = 5
        defender.x = 6
        defender.y = 5

    def test_engagement_persists_when_adjacent_after_update(self):
        attacker, defender = self._prepare_melee_pair()
        self._engage_units(attacker, defender)
        self._reset_combat_state(attacker, defender)
        self._reset_positions(attacker, defender)
        self.game_state._update_zoc_status()

        assert attacker.is_engaged_in_combat
        assert defender.is_engaged_in_combat
        assert attacker.engaged_with == defender
        assert defender.engaged_with == attacker

    def test_engagement_not_set_by_zoc_only(self):
        attacker, defender = self._prepare_melee_pair()
        self.game_state._update_zoc_status()

        assert attacker.in_enemy_zoc
        assert defender.in_enemy_zoc
        assert not attacker.is_engaged_in_combat
        assert not defender.is_engaged_in_combat
        assert attacker.engaged_with == defender
        assert defender.engaged_with == attacker

    def test_engagement_clears_when_enemy_moves_away(self):
        attacker, defender = self._prepare_melee_pair()
        self._engage_units(attacker, defender)

        defender.x = 9
        defender.y = 9
        self.game_state._update_zoc_status()

        assert not attacker.in_enemy_zoc
        assert not defender.in_enemy_zoc
        assert not attacker.is_engaged_in_combat
        assert not defender.is_engaged_in_combat
        assert attacker.engaged_with is None
        assert defender.engaged_with is None

    def test_engagement_clears_when_enemy_removed(self):
        attacker, defender = self._prepare_melee_pair()
        self._engage_units(attacker, defender)

        self.game_state.remove_knight(defender)
        self.game_state._update_zoc_status()

        assert not attacker.in_enemy_zoc
        assert not attacker.is_engaged_in_combat
        assert attacker.engaged_with is None

    def test_engagement_clears_when_enemy_loses_zoc(self):
        attacker, defender = self._prepare_melee_pair()
        self._engage_units(attacker, defender)

        defender.morale = CombatConfig.ZOC_MORALE_THRESHOLD - 1
        defender.cohesion = CombatConfig.ZOC_COHESION_THRESHOLD - 1
        self.game_state._update_zoc_status()

        assert not attacker.in_enemy_zoc
        assert not attacker.is_engaged_in_combat
        assert attacker.engaged_with is None

    def test_breakaway_clears_engagement_even_while_adjacent(self):
        attacker = UnitFactory.create_unit("Attacker", KnightClass.WARRIOR, 5, 5)
        defender = UnitFactory.create_unit("Defender", KnightClass.ARCHER, 6, 5)
        attacker.player_id = 1
        defender.player_id = 2
        attacker.stats.stats.current_soldiers = 10
        defender.stats.stats.current_soldiers = 10
        self.game_state.add_knight(attacker)
        self.game_state.add_knight(defender)

        self._engage_units(attacker, defender)
        self._reset_combat_state(attacker, defender)
        self._reset_positions(attacker, defender)

        defender.action_points = CombatConfig.MIN_AP_FOR_BREAKAWAY
        defender.is_engaged_in_combat = True
        defender.engaged_with = attacker
        attacker.is_engaged_in_combat = True
        attacker.engaged_with = defender

        result = defender.attempt_breakaway(attacker, self.game_state)
        assert result['success']

        self.game_state._update_zoc_status()
        assert defender.in_enemy_zoc
        assert attacker.in_enemy_zoc
        assert not defender.is_engaged_in_combat
        assert not attacker.is_engaged_in_combat
        assert defender.engaged_with == attacker
        assert attacker.engaged_with == defender

    def test_engaged_with_points_to_adjacent_enemy_when_multiple_present(self):
        attacker, defender = self._prepare_melee_pair()
        extra_enemy = UnitFactory.create_unit("Extra Enemy", KnightClass.WARRIOR, 5, 6)
        extra_enemy.player_id = 2
        extra_enemy.stats.stats.current_soldiers = 10
        self.game_state.add_knight(extra_enemy)

        self._engage_units(attacker, defender)
        self.game_state._update_zoc_status()

        assert attacker.in_enemy_zoc
        assert attacker.engaged_with in (defender, extra_enemy)
        assert attacker.engaged_with.player_id == 2

        defender.x = 9
        defender.y = 9
        self.game_state._update_zoc_status()

        assert attacker.in_enemy_zoc
        assert attacker.engaged_with == extra_enemy

    def test_routing_enemy_does_not_exert_zoc(self):
        attacker, defender = self._prepare_melee_pair()
        self._engage_units(attacker, defender)
        self._reset_combat_state(attacker, defender)
        self._reset_positions(attacker, defender)

        defender.is_routing = True
        self.game_state._update_zoc_status()
        assert not attacker.in_enemy_zoc

    def test_routing_unit_can_be_in_enemy_zoc(self):
        attacker, defender = self._prepare_melee_pair()
        self._engage_units(attacker, defender)
        self._reset_combat_state(attacker, defender)
        self._reset_positions(attacker, defender)

        defender.is_routing = True
        self.game_state._update_zoc_status()

        assert defender.in_enemy_zoc
        assert not attacker.in_enemy_zoc
