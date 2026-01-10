"""
BDD Test for Battle End Conditions.
"""
import pytest
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.state.victory_manager import VictoryManager

class TestBDDBattleEnd:
    """
    BDD-style tests for battle end conditions.
    """

    def test_battle_ends_when_player_eliminated(self):
        """
        Scenario: Battle ends when one side is unable to fight (all units eliminated).
        """
        
        # --------------------------------------------------------------------------
        # Given: A battle with two players
        # --------------------------------------------------------------------------
        game_state = MockGameState(board_width=20, board_height=20)
        victory_manager = VictoryManager()

        # And: Player 1 has one Warrior
        p1_unit = UnitFactory.create_unit("P1 Warrior", KnightClass.WARRIOR, 5, 5)
        p1_unit.player_id = 1
        game_state.add_knight(p1_unit)

        # And: Player 2 has one Warrior
        p2_unit = UnitFactory.create_unit("P2 Warrior", KnightClass.WARRIOR, 6, 6)
        p2_unit.player_id = 2
        game_state.add_knight(p2_unit)

        # And: The game is currently in progress (no winner yet)
        initial_winner = victory_manager.check_victory(game_state.knights, game_state.castles)
        assert initial_winner is None, "Game should be in progress initially"

        # --------------------------------------------------------------------------
        # When: Player 1's unit is eliminated (removed from the board)
        # --------------------------------------------------------------------------
        game_state.remove_knight(p1_unit)

        # --------------------------------------------------------------------------
        # Then: The battle should end
        # And: Player 2 should be declared the winner
        # --------------------------------------------------------------------------
        winner = victory_manager.check_victory(game_state.knights, game_state.castles)
        
        assert winner is not None, "Battle should have ended"
        assert winner == 2, f"Expected Player 2 to win, but got Player {winner}"
        
        # And: The victory reason should reflect unit elimination
        summary = victory_manager.get_victory_summary(winner, game_state.knights, game_state.castles)
        assert "eliminating all enemy units" in summary, \
            f"Victory summary should mention unit elimination, got: '{summary}'"
