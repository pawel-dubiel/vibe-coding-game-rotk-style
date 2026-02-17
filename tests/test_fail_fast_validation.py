import json

import pytest

from game.campaign.campaign_state import CampaignState
from game.entities.unit import Unit
from game.state.battle_state import BattleState
from game.terrain import Terrain
from game.test_scenario_loader import TestScenarioLoader


def test_terrain_rejects_non_enum_terrain_type():
    with pytest.raises(ValueError, match="terrain_type must be TerrainType"):
        Terrain("plains")


def test_unit_rejects_non_enum_unit_class():
    with pytest.raises(ValueError, match="unit_class must be KnightClass"):
        Unit("Invalid Unit", "warrior", 0, 0)


def test_battle_state_rejects_too_small_board():
    with pytest.raises(ValueError, match="at least 7x7"):
        BattleState({"board_size": (6, 6), "knights": 1, "castles": 1})


def test_campaign_state_raises_for_missing_map_file():
    with pytest.raises(FileNotFoundError, match="Campaign map file not found"):
        CampaignState(map_file="/tmp/does_not_exist_campaign_map.json")


def test_scenario_loader_rejects_unknown_terrain_type(tmp_path):
    scenario_path = tmp_path / "invalid_scenario.json"
    scenario_path.write_text(
        json.dumps(
            {
                "name": "Invalid Terrain Scenario",
                "description": "Invalid scenario should fail fast",
                "board_size": [10, 10],
                "terrain": {"base": "lava", "tiles": []},
                "units": [],
                "castles": [],
                "victory_conditions": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown base terrain type"):
        TestScenarioLoader.load_scenario(str(scenario_path))
