"""Test scenarios for demonstrating game mechanics"""
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType
from game.test_scenario_loader import TestScenarioLoader, ScenarioDefinition

class ScenarioType(Enum):
    """Different test scenario types"""
    ARCHER_ATTACK = "Archer Attack Demo"
    CAVALRY_CHARGE = "Cavalry Charge Demo"
    COMBAT_MODES = "Combat Modes Demo"
    TERRAIN_EFFECTS = "Terrain Effects Demo"
    FLANKING_ATTACK = "Flanking Attack Demo"
    GENERAL_ABILITIES = "General Abilities Demo"
    FOG_OF_WAR = "Fog of War Demo"
    DISRUPTION_MECHANICS = "Disruption Mechanics Demo"
    MOVEMENT_TERRAIN = "Movement & Terrain Demo"
    SIEGE_WARFARE = "Siege Warfare Demo"
    MORALE_SYSTEM = "Morale System Demo"
    # JSON-based scenarios
    JSON_ARCHER_MECHANICS = "JSON: Archer Mechanics Test"
    JSON_CAVALRY_CHARGE = "JSON: Cavalry Charge Test"
    JSON_FOG_OF_WAR = "JSON: Fog of War Test"
    JSON_CAVALRY_SCREENING = "JSON: Cavalry Screening Test"

class TestScenario:
    """Base class for test scenarios
    
    Test scenarios provide:
    - Deterministic terrain (always starts as flat plains)
    - Specific terrain modifications for testing
    - Pre-positioned units
    - Clear instructions
    - Repeatable test conditions
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.units: List[Dict] = []
        self.terrain_modifications: List[Tuple[int, int, TerrainType]] = []
        self.player_count = 2
        self.starting_player = 1
        self.camera_position: Optional[Tuple[int, int]] = None
        self.instructions: List[str] = []
        
    def add_unit(self, unit_class: KnightClass, x: int, y: int, player_id: int, 
                 name: Optional[str] = None, **kwargs):
        """Add a unit to the scenario"""
        self.units.append({
            'class': unit_class,
            'x': x,
            'y': y,
            'player_id': player_id,
            'name': name or f"{unit_class.value} {len(self.units) + 1}",
            'kwargs': kwargs
        })
        
    def add_terrain(self, x: int, y: int, terrain_type: TerrainType):
        """Add terrain modification"""
        self.terrain_modifications.append((x, y, terrain_type))
        
    def set_camera(self, x: int, y: int):
        """Set initial camera position"""
        self.camera_position = (x, y)
        
    def add_instruction(self, instruction: str):
        """Add instruction for the player"""
        self.instructions.append(instruction)
        
    def _setup_flat_terrain(self, game_state):
        """Create a flat plains terrain for consistent testing"""
        from game.terrain import Terrain, TerrainType
        
        # Create a new terrain grid filled with plains
        terrain_grid = []
        for y in range(game_state.terrain_map.height):
            row = []
            for x in range(game_state.terrain_map.width):
                terrain = Terrain(TerrainType.PLAINS)
                row.append(terrain)
            terrain_grid.append(row)
            
        # Replace the terrain map's grid
        game_state.terrain_map.terrain_grid = terrain_grid
        
    def setup(self, game_state):
        """Setup the scenario in the game state"""
        # Clear existing units
        game_state.knights.clear()
        
        # Replace terrain map with a flat plains map for consistency
        self._setup_flat_terrain(game_state)
        
        # Apply terrain modifications BEFORE creating units
        for x, y, terrain_type in self.terrain_modifications:
            # Get terrain at offset coordinates and modify it
            terrain = game_state.terrain_map.get_terrain(x, y)
            if terrain:
                terrain.type = terrain_type
        
        # Create units
        for unit_data in self.units:
            unit = UnitFactory.create_unit(
                unit_data['name'],
                unit_data['class'],
                unit_data['x'],
                unit_data['y']
            )
            unit.player_id = unit_data['player_id']
            
            # Apply any additional kwargs
            for key, value in unit_data['kwargs'].items():
                setattr(unit, key, value)
                
            game_state.knights.append(unit)
            
        # Set camera position
        if self.camera_position:
            # Use the hex layout to get proper positioning
            pos = game_state.hex_layout.hex_to_pixel(self.camera_position[0], self.camera_position[1])
            game_state.camera_x = pos[0] - game_state.screen_width // 2
            game_state.camera_y = pos[1] - game_state.screen_height // 2
            
        # Set starting player
        game_state.current_player = self.starting_player
        game_state.player_count = self.player_count
        
        # Update fog of war visibility for all units
        game_state._update_all_fog_of_war()
        
        # Show instructions
        if self.instructions:
            print("\n" + "="*50)
            print(f"Scenario: {self.name}")
            print("="*50)
            print("IMPORTANT: Both players are human-controlled!")
            print("Player 1 (Blue) goes first, then Player 2 (Red)")
            print("Fog of War works normally - each player sees their own units")
            print("-"*50)
            for instruction in self.instructions:
                print(f"• {instruction}")
            print("="*50 + "\n")

class TestScenarios:
    """Manager for test scenarios"""
    
    def __init__(self):
        self.scenarios: Dict[ScenarioType, TestScenario] = {}
        self._create_scenarios()
        
    def _create_scenarios(self):
        """Create all test scenarios"""
        
        # Archer Attack Demo
        scenario = TestScenario(
            "Archer Attack Demo",
            "Demonstrates archer ranged attacks without counter-damage"
        )
        # Place units closer together so they're within vision range
        # Player 1 units
        scenario.add_unit(KnightClass.ARCHER, 10, 10, 1, "P1 Archer")
        scenario.add_unit(KnightClass.WARRIOR, 10, 8, 1, "P1 Warrior")
        scenario.add_unit(KnightClass.CAVALRY, 8, 9, 1, "P1 Cavalry")
        
        # Player 2 units - within vision range
        scenario.add_unit(KnightClass.WARRIOR, 12, 10, 2, "P2 Warrior")  # 2 tiles from P1 archer
        scenario.add_unit(KnightClass.ARCHER, 10, 12, 2, "P2 Archer")   # 2 tiles away
        scenario.add_unit(KnightClass.CAVALRY, 12, 12, 2, "P2 Cavalry")
        scenario.set_camera(10, 10)
        scenario.add_instruction("Archers can attack from 3 tiles away without receiving counter-damage")
        scenario.add_instruction("Try attacking the enemy units from different ranges")
        scenario.add_instruction("Notice that at range 1, you'll receive counter-damage")
        scenario.add_instruction("Units start within vision range - fog of war works normally")
        self.scenarios[ScenarioType.ARCHER_ATTACK] = scenario
        
        # Cavalry Charge Demo
        scenario = TestScenario(
            "Cavalry Charge Demo",
            "Shows cavalry charge mechanics with damage bonus"
        )
        # Player 1 units
        scenario.add_unit(KnightClass.CAVALRY, 8, 10, 1, "P1 Cavalry 1")
        scenario.add_unit(KnightClass.CAVALRY, 8, 12, 1, "P1 Cavalry 2")
        scenario.add_unit(KnightClass.WARRIOR, 9, 11, 1, "P1 Warrior")
        
        # Player 2 units - positioned for testing charges
        scenario.add_unit(KnightClass.WARRIOR, 11, 10, 2, "P2 Warrior")
        scenario.add_unit(KnightClass.ARCHER, 11, 12, 2, "P2 Archer")
        scenario.add_unit(KnightClass.CAVALRY, 10, 11, 2, "P2 Cavalry")
        scenario.set_camera(10, 10)
        scenario.add_instruction("Cavalry gets a 30% damage bonus on their first charge")
        scenario.add_instruction("Charge attacks have reduced counter-damage (75%)")
        scenario.add_instruction("After charging once, cavalry attacks normally")
        self.scenarios[ScenarioType.CAVALRY_CHARGE] = scenario
        
        # Combat Modes Demo
        scenario = TestScenario(
            "Combat Modes Demo",
            "Shows all different combat modes in action"
        )
        # Create a battlefield with different unit types
        scenario.add_unit(KnightClass.ARCHER, 8, 8, 1, "Archer 1")
        scenario.add_unit(KnightClass.WARRIOR, 10, 8, 1, "Warrior 1")
        scenario.add_unit(KnightClass.CAVALRY, 12, 8, 1, "Cavalry 1")
        scenario.add_unit(KnightClass.MAGE, 14, 8, 1, "Mage 1")
        
        scenario.add_unit(KnightClass.WARRIOR, 8, 11, 2, "Enemy Warrior 1")
        scenario.add_unit(KnightClass.ARCHER, 10, 11, 2, "Enemy Archer 1")
        scenario.add_unit(KnightClass.CAVALRY, 12, 11, 2, "Enemy Cavalry 1")
        scenario.add_unit(KnightClass.WARRIOR, 14, 11, 2, "Enemy Warrior 2")
        
        scenario.set_camera(11, 9)
        scenario.add_instruction("Combat modes: RANGED (no counter), MELEE (full counter)")
        scenario.add_instruction("Special: CHARGE (cavalry +30% damage, 75% counter)")
        scenario.add_instruction("Archers don't counter-attack in melee")
        self.scenarios[ScenarioType.COMBAT_MODES] = scenario
        
        # Terrain Effects Demo
        scenario = TestScenario(
            "Terrain Effects Demo",
            "Demonstrates how terrain affects combat"
        )
        # Create units on different terrain
        scenario.add_unit(KnightClass.ARCHER, 8, 10, 1, "Hill Archer")
        scenario.add_unit(KnightClass.ARCHER, 12, 10, 1, "Plains Archer")
        scenario.add_unit(KnightClass.WARRIOR, 10, 8, 2, "Plains Warrior")
        scenario.add_unit(KnightClass.WARRIOR, 10, 12, 2, "Hill Warrior")
        
        # Add terrain - create a clear test pattern
        # Hills on left and bottom
        scenario.add_terrain(8, 10, TerrainType.HILLS)  # Hill for archer
        scenario.add_terrain(10, 12, TerrainType.HILLS)  # Hill for warrior
        scenario.add_terrain(7, 10, TerrainType.HILLS)
        scenario.add_terrain(8, 9, TerrainType.HILLS)
        scenario.add_terrain(8, 11, TerrainType.HILLS)
        scenario.add_terrain(9, 12, TerrainType.HILLS)
        scenario.add_terrain(11, 12, TerrainType.HILLS)
        
        # Forest in the middle
        scenario.add_terrain(9, 10, TerrainType.FOREST)
        scenario.add_terrain(11, 10, TerrainType.FOREST)
        scenario.add_terrain(10, 9, TerrainType.FOREST)
        scenario.add_terrain(10, 11, TerrainType.FOREST)
        
        # Plains everywhere else (already set by default)
        
        scenario.set_camera(10, 10)
        scenario.add_instruction("Archers on hills get +50% damage when shooting downhill")
        scenario.add_instruction("Archers shooting uphill get -50% damage penalty")
        scenario.add_instruction("Forest provides defense bonus but slows movement")
        scenario.add_instruction("All terrain is consistent - Hills (brown), Forest (green), Plains (tan)")
        self.scenarios[ScenarioType.TERRAIN_EFFECTS] = scenario
        
        # Flanking Attack Demo
        scenario = TestScenario(
            "Flanking Attack Demo",
            "Shows facing and flanking mechanics"
        )
        # Create a surrounded unit
        scenario.add_unit(KnightClass.WARRIOR, 10, 10, 2, "Surrounded Enemy", facing_direction=0)
        scenario.add_unit(KnightClass.WARRIOR, 10, 8, 1, "Front Attacker")
        scenario.add_unit(KnightClass.CAVALRY, 11, 9, 1, "Flank Attacker")
        scenario.add_unit(KnightClass.ARCHER, 10, 12, 1, "Rear Attacker")
        
        scenario.set_camera(10, 10)
        scenario.add_instruction("Units have facing directions (shown by shield icon)")
        scenario.add_instruction("Flanking attacks deal more damage and cause morale loss")
        scenario.add_instruction("Rear attacks are especially devastating")
        self.scenarios[ScenarioType.FLANKING_ATTACK] = scenario
        
        # Movement & Terrain Demo
        scenario = TestScenario(
            "Movement & Terrain Demo",
            "Test movement costs and terrain interactions"
        )
        # Create units to test movement
        scenario.add_unit(KnightClass.WARRIOR, 5, 10, 1, "Test Warrior")
        scenario.add_unit(KnightClass.CAVALRY, 5, 12, 1, "Test Cavalry")
        scenario.add_unit(KnightClass.ARCHER, 5, 14, 1, "Test Archer")
        
        # Create terrain strips to test movement
        # Column 7: Forest (high movement cost)
        for y in range(8, 16):
            scenario.add_terrain(7, y, TerrainType.FOREST)
            
        # Column 9: Hills (medium movement cost)
        for y in range(8, 16):
            scenario.add_terrain(9, y, TerrainType.HILLS)
            
        # Column 11: Water (impassable)
        for y in range(8, 16):
            scenario.add_terrain(11, y, TerrainType.WATER)
            
        # Add a bridge over water
        scenario.add_terrain(11, 11, TerrainType.BRIDGE)
        
        # Column 13: Road (low movement cost)
        for y in range(8, 16):
            scenario.add_terrain(13, y, TerrainType.ROAD)
            
        scenario.set_camera(9, 12)
        scenario.add_instruction("Test movement costs: Plains (1), Forest (2), Hills (1.5), Road (0.5)")
        scenario.add_instruction("Water is impassable except at bridges")
        scenario.add_instruction("Cavalry moves faster on roads and plains")
        scenario.add_instruction("All terrain is predictable - move units to test different paths")
        self.scenarios[ScenarioType.MOVEMENT_TERRAIN] = scenario
        
        # Load JSON-based scenarios
        self._load_json_scenarios()
        
    def _load_json_scenarios(self):
        """Load scenarios from JSON files"""
        # Map ScenarioType to JSON filename
        json_scenarios = {
            ScenarioType.JSON_ARCHER_MECHANICS: 'archer_mechanics.json',
            ScenarioType.JSON_CAVALRY_CHARGE: 'cavalry_charge.json',
            ScenarioType.JSON_FOG_OF_WAR: 'fog_of_war.json',
            ScenarioType.JSON_CAVALRY_SCREENING: 'cavalry_screening.json'
        }
        
        for scenario_type, filename in json_scenarios.items():
            try:
                # Create a wrapper scenario that loads from JSON
                json_scenario = JsonTestScenario(filename)
                self.scenarios[scenario_type] = json_scenario
            except Exception as e:
                print(f"Warning: Could not load JSON scenario {filename}: {e}")
        
    def get_scenario(self, scenario_type: ScenarioType) -> TestScenario:
        """Get a specific scenario"""
        return self.scenarios.get(scenario_type)
        
    def get_all_scenarios(self) -> List[Tuple[ScenarioType, TestScenario]]:
        """Get all available scenarios"""
        return list(self.scenarios.items())
        
    def get_available_json_scenarios(self) -> List[str]:
        """Get list of available JSON scenario files"""
        return TestScenarioLoader.list_scenarios()


class JsonTestScenario(TestScenario):
    """Test scenario that loads from a JSON file"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.scenario_def: Optional[ScenarioDefinition] = None
        
        # Load the scenario definition
        try:
            self.scenario_def = TestScenarioLoader.load_scenario(filename)
            super().__init__(self.scenario_def.name, self.scenario_def.description)
            
            # Add instructions based on victory conditions
            if self.scenario_def.victory_conditions:
                vc = self.scenario_def.victory_conditions
                if 'description' in vc:
                    self.add_instruction(vc['description'])
                    
        except Exception as e:
            super().__init__(f"Error: {filename}", f"Failed to load: {str(e)}")
            self.add_instruction(f"Error loading scenario: {str(e)}")
    
    def setup(self, game_state):
        """Setup the scenario from JSON definition"""
        if self.scenario_def:
            # Clear existing units
            game_state.knights.clear()
            
            # Apply the scenario using the loader
            TestScenarioLoader.apply_to_game_state(self.scenario_def, game_state)
            
            # Set camera position if specified
            if hasattr(self.scenario_def, 'camera_position') and self.scenario_def.camera_position:
                self.set_camera(*self.scenario_def.camera_position)
                super().setup(game_state)  # This will handle camera positioning
            else:
                # Default camera to center of board
                self.set_camera(
                    self.scenario_def.board_size[0] // 2,
                    self.scenario_def.board_size[1] // 2
                )
                
            # Show instructions
            if self.instructions:
                print("\n" + "="*50)
                print(f"Scenario: {self.name}")
                print("="*50)
                print("IMPORTANT: Both players are human-controlled!")
                print("Player 1 (Blue) goes first, then Player 2 (Red)")
                print("Fog of War works normally - each player sees their own units")
                print("-"*50)
                for instruction in self.instructions:
                    print(f"• {instruction}")
                print("="*50 + "\n")