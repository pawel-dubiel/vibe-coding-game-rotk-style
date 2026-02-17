"""Test scenario loader for JSON-based scenario definitions"""
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from game.terrain import TerrainType
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.entities.castle import Castle
from game.components.facing import FacingDirection


@dataclass
class ScenarioDefinition:
    """Container for scenario data loaded from JSON"""
    name: str
    description: str
    board_size: Tuple[int, int]
    terrain_base: str
    terrain_tiles: List[Dict]
    units: List[Dict]
    castles: List[Dict]
    victory_conditions: Dict


class TestScenarioLoader:
    """Loads test scenarios from JSON files"""
    
    # Map JSON terrain types to game TerrainType enum
    TERRAIN_MAPPING = {
        'plains': TerrainType.PLAINS,
        'grassland': TerrainType.PLAINS,  # Map grassland to plains
        'hills': TerrainType.HILLS,
        'forest': TerrainType.FOREST,
        'light_forest': TerrainType.LIGHT_FOREST,
        'dense_forest': TerrainType.DENSE_FOREST,
        'high_hills': TerrainType.HIGH_HILLS,
        'water': TerrainType.WATER,
        'deep_water': TerrainType.DEEP_WATER,
        'mountains': TerrainType.MOUNTAINS,
        'swamp': TerrainType.SWAMP,
        'marsh': TerrainType.MARSH,
        'desert': TerrainType.DESERT,
        'snow': TerrainType.SNOW,
        'bridge': TerrainType.BRIDGE,
        'road': TerrainType.ROAD
    }
    
    # Map JSON unit types to KnightClass enum
    UNIT_TYPE_MAPPING = {
        'warrior': KnightClass.WARRIOR,
        'archer': KnightClass.ARCHER,
        'cavalry': KnightClass.CAVALRY,
        'mage': KnightClass.MAGE,
        'pikeman': KnightClass.WARRIOR  # Map pikeman to warrior for now
    }
    
    # Map JSON facing directions to FacingDirection enum
    FACING_MAPPING = {
        'NORTH_EAST': FacingDirection.NORTH_EAST,
        'EAST': FacingDirection.EAST,
        'SOUTH_EAST': FacingDirection.SOUTH_EAST,
        'SOUTH_WEST': FacingDirection.SOUTH_WEST,
        'WEST': FacingDirection.WEST,
        'NORTH_WEST': FacingDirection.NORTH_WEST
    }

    @staticmethod
    def _require_keys(data: Dict, required_keys: List[str], context: str) -> None:
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise ValueError(f"Missing required {context} keys: {', '.join(missing)}")

    @classmethod
    def _validate_terrain_definition(cls, terrain_data: Dict) -> None:
        cls._require_keys(terrain_data, ['base', 'tiles'], "terrain")
        base_type = terrain_data['base']
        if base_type not in cls.TERRAIN_MAPPING:
            raise ValueError(f"Unknown base terrain type: {base_type}")
        if not isinstance(terrain_data['tiles'], list):
            raise ValueError("terrain.tiles must be a list")

        for index, tile in enumerate(terrain_data['tiles']):
            if not isinstance(tile, dict):
                raise ValueError(f"terrain tile at index {index} must be an object")
            cls._require_keys(tile, ['x', 'y', 'type'], f"terrain tile {index}")
            if tile['type'] not in cls.TERRAIN_MAPPING:
                raise ValueError(f"Unknown terrain tile type at index {index}: {tile['type']}")

    @classmethod
    def _validate_unit_definitions(cls, units: List[Dict]) -> None:
        if not isinstance(units, list):
            raise ValueError("units must be a list")
        for index, unit in enumerate(units):
            if not isinstance(unit, dict):
                raise ValueError(f"unit at index {index} must be an object")
            cls._require_keys(unit, ['name', 'type', 'x', 'y', 'player'], f"unit {index}")
            if unit['type'] not in cls.UNIT_TYPE_MAPPING:
                raise ValueError(f"Unknown unit type at index {index}: {unit['type']}")
            if 'facing' in unit and unit['facing'] not in cls.FACING_MAPPING:
                raise ValueError(f"Unknown facing direction at index {index}: {unit['facing']}")

    @staticmethod
    def _validate_castle_definitions(castles: List[Dict]) -> None:
        if not isinstance(castles, list):
            raise ValueError("castles must be a list")
        for index, castle in enumerate(castles):
            if not isinstance(castle, dict):
                raise ValueError(f"castle at index {index} must be an object")
            missing = [key for key in ['x', 'y', 'player'] if key not in castle]
            if missing:
                raise ValueError(f"Missing required castle {index} keys: {', '.join(missing)}")
    
    @classmethod
    def load_scenario(cls, filename: str) -> ScenarioDefinition:
        """Load a scenario from a JSON file"""
        # Check if it's a full path or just a filename
        if os.path.exists(filename):
            filepath = filename
        else:
            # Look in the test_scenarios directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(base_dir, 'test_scenarios', filename)
            
            # Add .json extension if not present
            if not filepath.endswith('.json'):
                filepath += '.json'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cls._require_keys(
            data,
            ['name', 'description', 'board_size', 'terrain', 'units', 'castles', 'victory_conditions'],
            "scenario",
        )
        board_size = data['board_size']
        if (
            not isinstance(board_size, (list, tuple))
            or len(board_size) != 2
            or not all(isinstance(value, int) for value in board_size)
        ):
            raise ValueError("board_size must be a list/tuple of two integers")

        terrain_data = data['terrain']
        if not isinstance(terrain_data, dict):
            raise ValueError("terrain must be an object")
        cls._validate_terrain_definition(terrain_data)
        cls._validate_unit_definitions(data['units'])
        cls._validate_castle_definitions(data['castles'])
        if not isinstance(data['victory_conditions'], dict):
            raise ValueError("victory_conditions must be an object")
        
        return ScenarioDefinition(
            name=data['name'],
            description=data['description'],
            board_size=tuple(board_size),
            terrain_base=terrain_data['base'],
            terrain_tiles=terrain_data['tiles'],
            units=data['units'],
            castles=data['castles'],
            victory_conditions=data['victory_conditions']
        )
    
    @classmethod
    def list_scenarios(cls) -> List[str]:
        """List all available scenario files"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scenario_dir = os.path.join(base_dir, 'test_scenarios')
        
        if not os.path.exists(scenario_dir):
            return []
        
        scenarios = []
        for filename in os.listdir(scenario_dir):
            if filename.endswith('.json') and filename != 'scenario_schema.json':
                scenarios.append(filename[:-5])  # Remove .json extension
        
        return sorted(scenarios)
    
    @classmethod
    def apply_to_game_state(cls, scenario: ScenarioDefinition, game_state):
        """Apply a scenario definition to a game state"""
        if scenario is None:
            raise ValueError("scenario is required")
        if game_state is None:
            raise ValueError("game_state is required")
        if not hasattr(game_state, 'terrain_map') or game_state.terrain_map is None:
            raise ValueError("game_state.terrain_map is required to apply scenario")
        if not hasattr(game_state, 'board_width') or not hasattr(game_state, 'board_height'):
            raise ValueError("game_state board dimensions are required to apply scenario")

        # Clear existing units and castles
        game_state.knights.clear()
        game_state.castles.clear()
        
        # Set up terrain
        base_terrain = cls.TERRAIN_MAPPING[scenario.terrain_base]
        for x in range(game_state.board_width):
            for y in range(game_state.board_height):
                game_state.terrain_map.set_terrain(x, y, base_terrain)
        
        # Apply specific terrain tiles
        for tile in scenario.terrain_tiles:
            terrain_type = cls.TERRAIN_MAPPING[tile['type']]
            game_state.terrain_map.set_terrain(tile['x'], tile['y'], terrain_type)
        
        # Create units
        for unit_def in scenario.units:
            unit_type = cls.UNIT_TYPE_MAPPING[unit_def['type']]
            unit = UnitFactory.create_unit(
                name=unit_def['name'],
                unit_class=unit_type,
                x=unit_def['x'],
                y=unit_def['y']
            )
            unit.player_id = unit_def['player']
            
            # Set optional attributes
            if 'facing' in unit_def:
                facing_dir = cls.FACING_MAPPING[unit_def['facing']]
                unit.facing.facing = facing_dir
            
            if 'health' in unit_def:
                health_percent = unit_def['health'] / 100.0
                unit.stats.stats.current_soldiers = int(unit.max_soldiers * health_percent)
            
            if 'morale' in unit_def:
                unit.morale = unit_def['morale']
            
            game_state.knights.append(unit)
        
        # Create castles
        for castle_def in scenario.castles:
            castle = Castle(castle_def['x'], castle_def['y'], castle_def['player'])
            game_state.castles.append(castle)
        
        # Update fog of war if present
        if hasattr(game_state, '_update_all_fog_of_war'):
            game_state._update_all_fog_of_war()
    
    @classmethod
    def create_test_function(cls, scenario_file: str):
        """Create a test scenario setup function for the game"""
        def setup_scenario(game_state):
            scenario = cls.load_scenario(scenario_file)
            cls.apply_to_game_state(scenario, game_state)
            return scenario.name, scenario.description
        
        return setup_scenario
