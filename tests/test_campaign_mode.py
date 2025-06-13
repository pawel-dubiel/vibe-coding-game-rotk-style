import pytest
import pygame
from game.campaign.campaign_state import CampaignState, Country, Army, City
from game.campaign.campaign_renderer import CampaignRenderer
from game.ui.campaign_screen import CampaignScreen
from game.hex_utils import HexCoord


class TestCampaignMode:
    
    def test_campaign_state_initialization(self):
        """Test campaign state initializes correctly"""
        # Create campaign state with test data
        state = CampaignState(player_country="poland")
        
        # Clear any default data
        state.cities.clear()
        state.armies.clear()
        state.countries.clear()
        state.country_treasury.clear()
        
        # Add test countries
        state.countries["poland"] = Country(
            id="poland",
            name="Poland",
            color=(255, 0, 0),
            capital="Krakow",
            description="Kingdom of Poland",
            starting_resources={"gold": 1000},
            bonuses={}
        )
        state.countries["teutons"] = Country(
            id="teutons",
            name="Teutonic Order",
            color=(255, 255, 255),
            capital="Marienburg",
            description="Teutonic Knights",
            starting_resources={"gold": 1200},
            bonuses={}
        )
        
        # Add test cities
        state.cities["krakow"] = City(
            name="Krakow",
            country="poland",
            position=HexCoord(10, 10),
            city_type="capital",
            income=100,
            castle_level=2,
            population=20000,
            specialization="trade",
            description="Polish capital"
        )
        state.cities["warsaw"] = City(
            name="Warsaw",
            country="poland",
            position=HexCoord(12, 10),
            city_type="city",
            income=100,
            castle_level=1,
            population=15000,
            specialization="agriculture",
            description="Major Polish city"
        )
        state.cities["gniezno"] = City(
            name="Gniezno",
            country="poland",
            position=HexCoord(11, 9),
            city_type="city",
            income=100,
            castle_level=1,
            population=10000,
            specialization="military",
            description="Historic Polish city"
        )
        
        # Add test armies
        state.armies["poland_main"] = Army(
            id="poland_main",
            country="poland",
            position=HexCoord(10, 10),
            knights=10,
            archers=5,
            cavalry=3,
            movement_points=3
        )
        state.armies["teutonic_main"] = Army(
            id="teutonic_main",
            country="teutons",
            position=HexCoord(15, 15),
            knights=12,
            archers=6,
            cavalry=4,
            movement_points=3
        )
        
        # Initialize treasuries
        state.country_treasury["poland"] = 1000
        state.country_treasury["teutons"] = 1200
        
        # Check initial state
        assert state.current_country == "poland"
        assert state.turn_number == 1
        assert len(state.cities) == 3
        assert len(state.armies) == 2
        
        # Check Poland has cities
        poland_cities = state.get_country_cities("poland")
        assert len(poland_cities) == 3
        assert any(c.name == "Krakow" for c in poland_cities)
        
        # Check Poland has army
        poland_armies = state.get_country_armies("poland")
        assert len(poland_armies) == 1
        assert poland_armies[0].knights == 10
        assert poland_armies[0].archers == 5
        assert poland_armies[0].cavalry == 3
        
        # Check enemy armies exist
        assert len(state.armies) > 1
        teutonic_armies = state.get_country_armies("teutons")
        assert len(teutonic_armies) == 1
        
    def test_army_movement(self):
        """Test army movement mechanics"""
        state = CampaignState(player_country="poland")
        
        # Create test army
        army = Army(
            id="test_army",
            country="poland",
            position=HexCoord(10, 10),
            knights=5,
            archers=3,
            cavalry=2,
            movement_points=3
        )
        state.armies["test_army"] = army
        state.current_country = "poland"
        
        original_pos = army.position
        
        # Test valid movement (1 hex away)
        new_pos = HexCoord(original_pos.q + 1, original_pos.r)
        assert state.move_army("test_army", new_pos) == True
        assert army.position == new_pos
        assert army.movement_points < army.max_movement_points
        
        # Test invalid movement (too far)
        far_pos = HexCoord(original_pos.q + 10, original_pos.r)
        assert state.move_army("test_army", far_pos) == False
        assert army.position == new_pos  # Position unchanged
        
    def test_country_turn_cycle(self):
        """Test turn cycling through countries"""
        state = CampaignState(player_country="poland")
        
        # Setup countries
        state.countries = {
            "poland": Country("poland", "Poland", (255, 0, 0), "Krakow", "", {}, {}),
            "france": Country("france", "France", (0, 0, 255), "Paris", "", {}, {}),
            "england": Country("england", "England", (255, 255, 255), "London", "", {}, {})
        }
        
        # Record initial country
        assert state.current_country == "poland"
        assert state.turn_number == 1
        
        # End turn
        state.end_turn()
        assert state.current_country == "france"
        
        state.end_turn()
        assert state.current_country == "england"
        
        state.end_turn()
        # Should be back to Poland, turn 2
        assert state.current_country == "poland"
        assert state.turn_number == 2
        
    def test_country_income(self):
        """Test income collection from cities"""
        state = CampaignState(player_country="poland")
        
        # Clear any default data
        state.cities.clear()
        state.armies.clear()
        state.countries.clear()
        state.country_treasury.clear()
        
        # Setup test data
        state.countries["poland"] = Country(
            id="poland",
            name="Poland",
            color=(255, 0, 0),
            capital="Krakow",
            description="",
            starting_resources={},
            bonuses={}
        )
        
        # Add cities with income
        for i in range(3):
            state.cities[f"city_{i}"] = City(
                name=f"City {i}",
                country="poland",
                position=HexCoord(10 + i, 10),
                city_type="city",
                income=100,
                castle_level=1,
                population=10000,
                specialization="trade",
                description=""
            )
        
        # Setup treasury
        state.country_treasury["poland"] = 1000
        initial_gold = state.country_treasury["poland"]
        
        # Calculate expected income
        poland_cities = state.get_country_cities("poland")
        expected_income = sum(c.income for c in poland_cities)
        assert expected_income == 300
        
        # End turn to collect income
        state.end_turn()
        
        # Check income was collected
        assert state.country_treasury["poland"] == initial_gold + expected_income
        
    def test_unit_recruitment(self):
        """Test recruiting new units"""
        state = CampaignState(player_country="poland")
        
        # Clear any default data
        state.cities.clear()
        state.armies.clear()
        state.countries.clear()
        state.country_treasury.clear()
        
        # Setup country and city
        state.countries["poland"] = Country(
            id="poland",
            name="Poland",
            color=(255, 0, 0),
            capital="Krakow",
            description="",
            starting_resources={},
            bonuses={}
        )
        
        state.cities["krakow"] = City(
            name="Krakow",
            country="poland",
            position=HexCoord(10, 10),
            city_type="capital",
            income=100,
            castle_level=2,
            population=20000,
            specialization="military",
            description=""
        )
        
        # Give Poland gold for recruitment
        state.country_treasury["poland"] = 5000
        
        # Test recruitment
        state.current_country = "poland"  # Must be poland's turn to recruit
        result = state.recruit_units("poland", "krakow", knights=5, archers=3, cavalry=2)
        assert result == True
        
        # Check cost deducted (knights=100, archers=80, cavalry=150)
        expected_cost = 5 * 100 + 3 * 80 + 2 * 150  # 1040 gold
        assert state.country_treasury["poland"] == 5000 - expected_cost
        
        # Check army was created
        poland_armies = state.get_country_armies("poland")
        assert len(poland_armies) > 0
        
        # Find the newly created army
        new_army = None
        for army in poland_armies:
            if army.position == state.cities["krakow"].position:
                new_army = army
                break
        
        assert new_army is not None
        assert new_army.knights == 5
        assert new_army.archers == 3
        assert new_army.cavalry == 2
        
    def test_campaign_screen_initialization(self):
        """Test campaign screen setup"""
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        campaign_screen = CampaignScreen(screen)
        campaign_screen._ensure_campaign_state()
        
        assert campaign_screen.visible == True
        assert campaign_screen.ready_for_battle == False
        
        # Campaign state should be initialized but may not have default player country
        assert campaign_screen.campaign_state is not None
        
        pygame.quit()
        
    def test_army_selection(self):
        """Test army selection mechanics"""
        state = CampaignState(player_country="poland")
        
        # Create test army
        army = Army(
            id="poland_main",
            country="poland",
            position=HexCoord(10, 10),
            knights=10,
            archers=5,
            cavalry=3,
            movement_points=3
        )
        state.armies["poland_main"] = army
        state.current_country = "poland"
        
        # Select Poland's army
        state.selected_army = "poland_main"
        assert state.selected_army == "poland_main"
        
        # Verify selected army belongs to current country
        selected_army = state.armies[state.selected_army]
        assert selected_army.country == state.current_country
        
    def test_campaign_battle_setup(self):
        """Test battle setup from campaign armies"""
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        campaign_screen = CampaignScreen(screen)
        campaign_screen._ensure_campaign_state()
        
        # Create test armies
        poland_army = Army(
            id="poland_main",
            country="poland",
            position=HexCoord(10, 10),
            knights=10,
            archers=5,
            cavalry=3,
            movement_points=3
        )
        
        teutonic_army = Army(
            id="teutonic_main",
            country="teutons",
            position=HexCoord(10, 10),
            knights=12,
            archers=6,
            cavalry=4,
            movement_points=3
        )
        
        # Simulate armies meeting
        campaign_screen.ready_for_battle = True
        campaign_screen.battle_armies = {
            'attacker': poland_army,
            'defender': teutonic_army
        }
        
        # Get battle config
        battle_config = campaign_screen.get_battle_config()
        
        assert battle_config is not None
        assert battle_config['campaign_battle'] == True
        assert battle_config['attacker_army'] == poland_army
        assert battle_config['defender_army'] == teutonic_army
        assert battle_config['attacker_country'] == "poland"
        assert battle_config['defender_country'] == "teutons"
        assert battle_config['board_size'] == (20, 20)
        assert battle_config['castles'] == 0
        
        pygame.quit()
        
    def test_hex_movement_distances(self):
        """Test that hex movement correctly calculates distances"""
        state = CampaignState(player_country="poland")
        
        # Create a test army
        test_army = Army(
            id="test_army",
            country="poland",
            position=HexCoord(25, 20),
            knights=5,
            archers=3,
            cavalry=2,
            movement_points=3
        )
        state.armies["test_army"] = test_army
        state.current_country = "poland"
        
        # Test 1-hex movement (distance = 1)
        target1 = HexCoord(26, 20)  # 1 hex east
        assert test_army.position.distance_to(target1) == 1
        assert state.move_army("test_army", target1) == True
        assert test_army.movement_points == 2
        
        # Test 2-hex movement (distance = 2)
        target2 = HexCoord(26, 18)  # 2 hexes northeast
        assert test_army.position.distance_to(target2) == 2
        assert state.move_army("test_army", target2) == True
        assert test_army.movement_points == 0
        
        # Test invalid movement (no movement points left)
        target3 = HexCoord(27, 18)  # 1 hex east
        assert state.move_army("test_army", target3) == False
        assert test_army.position == target2  # Position unchanged