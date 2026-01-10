import pygame

from game.ai.ai_player import AIPlayer
from game.combat_config import CombatConfig
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.game_state import GameState
from game.terrain import TerrainType


def test_ai_stops_attacking_when_out_of_ap():
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()

    game_state = GameState(
        battle_config={'board_size': (10, 10), 'knights': 0, 'castles': 1},
        vs_ai=False,
    )
    game_state.knights = []
    game_state.current_player = 2

    ai = AIPlayer(2, 'easy')

    archer = UnitFactory.create_unit("AI Archer", KnightClass.ARCHER, 5, 5)
    archer.player_id = 2
    archer.action_points = CombatConfig.get_attack_ap_cost(archer.unit_class.value)
    archer.has_moved = True
    archer.has_acted = False

    target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 6, 5)
    target.player_id = 1

    game_state.knights.extend([archer, target])
    game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
    game_state.terrain_map.set_terrain(6, 5, TerrainType.PLAINS)
    game_state._update_all_fog_of_war()

    actions_taken = ai.execute_turn(game_state)

    attack_actions = [action for action in actions_taken if "attacked" in action]
    assert len(attack_actions) == 1
    assert archer.action_points == 0
    assert getattr(archer, 'attacks_this_turn', 0) == 1


def test_ai_does_not_attack_without_enough_ap():
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()

    game_state = GameState(
        battle_config={'board_size': (10, 10), 'knights': 0, 'castles': 1},
        vs_ai=False,
    )
    game_state.knights = []
    game_state.current_player = 2

    ai = AIPlayer(2, 'easy')

    archer = UnitFactory.create_unit("AI Archer", KnightClass.ARCHER, 5, 5)
    archer.player_id = 2
    archer.action_points = CombatConfig.get_attack_ap_cost(archer.unit_class.value) - 1
    archer.has_moved = True
    archer.has_acted = False

    target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 6, 5)
    target.player_id = 1

    game_state.knights.extend([archer, target])
    game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
    game_state.terrain_map.set_terrain(6, 5, TerrainType.PLAINS)
    game_state._update_all_fog_of_war()

    actions_taken = ai.execute_turn(game_state)

    attack_actions = [action for action in actions_taken if "attacked" in action]
    assert len(attack_actions) == 0
    assert archer.action_points == CombatConfig.get_attack_ap_cost(archer.unit_class.value) - 1
