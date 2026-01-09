import pytest

from game.entities.castle import Castle
from game.entities.knight import KnightClass
from game.entities.unit_factory import UnitFactory
from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
from game.test_utils.mock_game_state import MockGameState
from game.terrain import TerrainType


def _create_game_state():
    game_state = MockGameState(board_width=8, board_height=8)
    game_state.knights.clear()
    game_state.castles.clear()
    for y in range(game_state.board_height):
        for x in range(game_state.board_width):
            game_state.terrain_map.set_terrain(x, y, TerrainType.PLAINS)
    return game_state


@pytest.mark.parametrize("terrain_type", [TerrainType.FOREST, TerrainType.HILLS])
def test_cavalry_disrupted_on_difficult_terrain(terrain_type):
    game_state = _create_game_state()
    unit = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 2, 2, add_generals=False)
    unit.player_id = 1
    game_state.knights.append(unit)

    game_state.terrain_map.set_terrain(2, 2, terrain_type)
    check_cavalry_disruption_for_terrain(unit, game_state)

    assert unit.is_disrupted is True


def test_cavalry_not_disrupted_on_plains():
    game_state = _create_game_state()
    unit = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 1, 1, add_generals=False)
    unit.player_id = 1
    game_state.knights.append(unit)

    game_state.terrain_map.set_terrain(1, 1, TerrainType.PLAINS)
    check_cavalry_disruption_for_terrain(unit, game_state)

    assert unit.is_disrupted is False


def test_cavalry_disrupted_in_castle():
    game_state = _create_game_state()
    game_state.castles.append(Castle(2, 2, 1))

    unit = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 2, 2, add_generals=False)
    unit.player_id = 1
    game_state.knights.append(unit)

    check_cavalry_disruption_for_terrain(unit, game_state)

    assert unit.is_disrupted is True
