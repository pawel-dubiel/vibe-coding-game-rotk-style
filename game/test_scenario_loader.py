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
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return ScenarioDefinition(
            name=data['name'],
            description=data['description'],
            board_size=tuple(data['board_size']),
            terrain_base=data.get('terrain', {}).get('base', 'plains'),
            terrain_tiles=data.get('terrain', {}).get('tiles', []),
            units=data.get('units', []),
            castles=data.get('castles', []),
            victory_conditions=data.get('victory_conditions', {})
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
        # Clear existing units and castles
        game_state.knights.clear()
        game_state.castles.clear()
        
        # Set up terrain
        if hasattr(game_state, 'terrain_map') and game_state.terrain_map:
            # Set base terrain
            base_terrain = cls.TERRAIN_MAPPING.get(scenario.terrain_base, TerrainType.PLAINS)
            for x in range(game_state.board_width):
                for y in range(game_state.board_height):
                    game_state.terrain_map.set_terrain(x, y, base_terrain)
            
            # Apply specific terrain tiles
            for tile in scenario.terrain_tiles:
                terrain_type = cls.TERRAIN_MAPPING.get(tile['type'], TerrainType.PLAINS)
                game_state.terrain_map.set_terrain(tile['x'], tile['y'], terrain_type)
        
        # Create units
        for unit_def in scenario.units:
            unit_type = cls.UNIT_TYPE_MAPPING.get(unit_def['type'], KnightClass.WARRIOR)
            unit = UnitFactory.create_unit(
                name=unit_def['name'],
                unit_class=unit_type,
                x=unit_def['x'],
                y=unit_def['y']
            )
            unit.player_id = unit_def['player']
            
            # Set optional attributes
            if 'facing' in unit_def:
                facing_dir = cls.FACING_MAPPING.get(unit_def['facing'], FacingDirection.EAST)
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