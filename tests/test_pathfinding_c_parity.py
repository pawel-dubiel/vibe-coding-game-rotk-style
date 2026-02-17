"""Ensure Python and C pathfinding implementations return identical results."""
from game.c_pathfinding_wrapper import C_EXTENSION_AVAILABLE, CPathFinder
from game.pathfinding import AStarPathFinder
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType


def _require_c_extension():
    assert C_EXTENSION_AVAILABLE, "C pathfinding extension is required for parity tests"


def _force_python_astar():
    pathfinder = AStarPathFinder()

    def cost_fn(from_pos, to_pos, game_state, unit):
        return pathfinder._get_movement_cost(from_pos, to_pos, game_state, unit)

    return pathfinder, cost_fn


def _set_corridor_map(game_state, width, height, open_row):
    for x in range(width):
        for y in range(height):
            terrain = TerrainType.PLAINS if y == open_row else TerrainType.MOUNTAINS
            game_state.terrain_map.set_terrain(x, y, terrain)


def test_c_and_python_match_on_unique_corridor_path():
    _require_c_extension()
    width, height = 7, 7
    game_state = MockGameState(board_width=width, board_height=height)
    _set_corridor_map(game_state, width, height, open_row=3)

    unit = UnitFactory.create_unit("Unit", KnightClass.WARRIOR, 0, 3)
    unit.player_id = 1
    game_state.add_knight(unit)

    start = (0, 3)
    end = (6, 3)

    py_pathfinder, cost_fn = _force_python_astar()
    py_path = py_pathfinder.find_path(start, end, game_state, unit=unit, cost_function=cost_fn)

    c_pathfinder = CPathFinder()
    c_path = c_pathfinder.find_path(start, end, game_state, unit=unit)

    assert py_path == c_path


def test_c_and_python_match_when_blocked_by_enemy():
    _require_c_extension()
    width, height = 7, 7
    game_state = MockGameState(board_width=width, board_height=height)
    _set_corridor_map(game_state, width, height, open_row=3)

    unit = UnitFactory.create_unit("Unit", KnightClass.WARRIOR, 0, 3)
    unit.player_id = 1
    game_state.add_knight(unit)

    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 3, 3)
    enemy.player_id = 2
    game_state.add_knight(enemy)

    start = (0, 3)
    end = (6, 3)

    py_pathfinder, cost_fn = _force_python_astar()
    py_path = py_pathfinder.find_path(start, end, game_state, unit=unit, cost_function=cost_fn)

    c_pathfinder = CPathFinder()
    c_path = c_pathfinder.find_path(start, end, game_state, unit=unit)

    assert py_path is None
    assert c_path is None


def test_c_and_python_respect_max_cost_limit():
    _require_c_extension()
    width, height = 7, 7
    game_state = MockGameState(board_width=width, board_height=height)
    _set_corridor_map(game_state, width, height, open_row=3)

    unit = UnitFactory.create_unit("Unit", KnightClass.WARRIOR, 0, 3)
    unit.player_id = 1
    game_state.add_knight(unit)

    start = (0, 3)
    end = (6, 3)

    py_pathfinder, cost_fn = _force_python_astar()
    py_path = py_pathfinder.find_path(
        start, end, game_state, unit=unit, max_cost=3, cost_function=cost_fn
    )

    c_pathfinder = CPathFinder()
    c_path = c_pathfinder.find_path(start, end, game_state, unit=unit, max_cost=3)

    assert py_path is None
    assert c_path is None


def test_c_pathfinder_cache_invalidates_when_terrain_changes():
    _require_c_extension()
    width, height = 7, 7
    game_state = MockGameState(board_width=width, board_height=height)

    unit = UnitFactory.create_unit("Unit", KnightClass.WARRIOR, 0, 3)
    unit.player_id = 1
    game_state.add_knight(unit)

    c_pathfinder = CPathFinder()
    initial_path = c_pathfinder.find_path((0, 3), (6, 3), game_state, unit=unit)
    assert initial_path is not None

    # Block the board with an impassable vertical wall.
    for y in range(height):
        game_state.terrain_map.set_terrain(3, y, TerrainType.MOUNTAINS)

    blocked_path = c_pathfinder.find_path((0, 3), (6, 3), game_state, unit=unit)
    assert blocked_path is None
