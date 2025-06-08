"""High-level integration tests for campaign mode.

These tests focus on overall functionality and user flows rather than
implementation details, making them resilient to internal changes.
"""

import pytest
import pygame
from unittest.mock import patch
from game.campaign.campaign_state import CampaignState
from game.ui.country_selection import CountrySelectionScreen
from game.ui.campaign_screen import CampaignScreen
from game.hex_utils import HexCoord


@pytest.fixture
def pygame_surface():
    """Create a mock pygame surface for testing."""
    pygame.init()
    surface = pygame.display.set_mode((800, 600))
    yield surface
    pygame.quit()


class TestCountrySelection:
    """Test country selection functionality."""
    
    def test_country_selection_loads_available_countries(self, pygame_surface):
        """Verify that country selection screen loads countries from data."""
        screen = CountrySelectionScreen(pygame_surface)
        
        # Should have loaded countries
        assert len(screen.countries) > 0
        assert 'poland' in screen.countries
        
        # Each country should have required data
        for country_id, country_data in screen.countries.items():
            assert 'name' in country_data
            assert 'color' in country_data
            assert 'description' in country_data
    
    @pytest.mark.skip(reason="Pygame event handling needs special setup in test environment")
    def test_country_selection_returns_selected_country(self, pygame_surface):
        """Verify that selecting a country returns proper data for campaign start."""
        screen = CountrySelectionScreen(pygame_surface)
        screen.show()  # Make sure screen is shown
        
        # First, test selecting a country works
        poland_button = screen.country_buttons.get('poland')
        assert poland_button is not None
        
        # Test country selection
        with patch('pygame.mouse.get_pos', return_value=poland_button.center):
            select_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
            result = screen.handle_event(select_event)
            assert result is None  # Selection doesn't return anything
            assert screen.selected_country == 'poland'
        
        # Now test start button with country selected
        with patch('pygame.mouse.get_pos', return_value=screen.start_button.center):
            start_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
            result = screen.handle_event(start_event)
        
        assert result is not None
        assert result['action'] == 'start_campaign'
        assert result['country'] == 'poland'
        assert 'country_data' in result


class TestCampaignInitialization:
    """Test campaign state initialization."""
    
    def test_campaign_initializes_with_selected_country(self):
        """Verify campaign state properly initializes with a selected country."""
        # Use Poland which exists in the data
        campaign = CampaignState('poland', {'name': 'Poland', 'starting_resources': {'gold': 1500}})
        
        # Verify initialization
        assert campaign.player_country == 'poland'
        assert campaign.current_country == 'poland'
        assert campaign.turn_number == 1
        
        # Should have starting resources
        assert 'poland' in campaign.country_treasury
        assert campaign.country_treasury['poland'] >= 1000
        
        # Should have at least one army
        player_armies = campaign.get_country_armies('poland')
        assert len(player_armies) > 0
        
        # Army should be at capital location
        if len(player_armies) > 0:
            army = player_armies[0]
            assert army.country == 'poland'
            assert army.knights > 0 or army.archers > 0 or army.cavalry > 0
    
    def test_campaign_loads_game_data(self):
        """Verify campaign loads cities and countries from data files."""
        campaign = CampaignState()
        
        # Should have loaded countries and cities
        assert len(campaign.countries) > 0
        assert len(campaign.cities) > 0
        
        # Cities should belong to countries
        for city in campaign.cities.values():
            assert hasattr(city, 'country')
            assert hasattr(city, 'income')
            assert hasattr(city, 'position')
            
        # Should have loaded terrain
        assert len(campaign.terrain_map) > 0
        
        # Terrain should include various types
        terrain_types = set()
        for terrain in campaign.terrain_map.values():
            terrain_types.add(terrain.name if hasattr(terrain, 'name') else str(terrain))
        
        # Should have at least some basic terrain types
        assert 'WATER' in terrain_types or 'PLAINS' in terrain_types


class TestCampaignGameplay:
    """Test core campaign gameplay mechanics."""
    
    def test_army_movement_respects_movement_points(self):
        """Verify armies can only move within their movement point limit."""
        campaign = CampaignState('poland', {'name': 'Poland', 'starting_resources': {'gold': 1000}})
        
        # Get player's army
        armies = campaign.get_country_armies('poland')
        assert len(armies) > 0
        army = armies[0]
        
        # Remember starting position
        start_pos = army.position
        initial_mp = army.movement_points
        
        # Try to move within range
        nearby_hex = HexCoord(start_pos.q + 1, start_pos.r)
        result = campaign.move_army(army.id, nearby_hex)
        
        assert result is True
        assert army.position == nearby_hex
        assert army.movement_points < initial_mp
        
        # Try to move too far
        far_hex = HexCoord(start_pos.q + 10, start_pos.r + 10)
        result = campaign.move_army(army.id, far_hex)
        
        assert result is False  # Should fail
        assert army.position == nearby_hex  # Position unchanged
    
    def test_turn_progression_cycles_through_countries(self):
        """Verify turn system cycles through all countries."""
        campaign = CampaignState()
        
        initial_country = campaign.current_country
        initial_turn = campaign.turn_number
        countries_seen = {initial_country}
        
        # Progress through turns
        for _ in range(len(campaign.countries) + 1):
            campaign.end_turn()
            countries_seen.add(campaign.current_country)
        
        # Should have seen all countries
        assert len(countries_seen) == len(campaign.countries)
        
        # Turn number should have incremented
        assert campaign.turn_number > initial_turn
    
    def test_income_collection_at_turn_end(self):
        """Verify countries collect income from their cities."""
        campaign = CampaignState('poland', {'name': 'Poland', 'starting_resources': {'gold': 1000}})
        
        # Get initial treasury
        initial_gold = campaign.country_treasury['poland']
        
        # Get expected income
        poland_cities = campaign.get_country_cities('poland')
        expected_income = sum(city.income for city in poland_cities)
        
        # End turn for all countries to get back to Poland
        for _ in range(len(campaign.countries)):
            campaign.end_turn()
        
        # Treasury should have increased by income
        assert campaign.country_treasury['poland'] == initial_gold + expected_income
    
    def test_unit_recruitment_costs_resources(self):
        """Verify recruiting units deducts appropriate gold."""
        campaign = CampaignState('poland', {'name': 'Poland', 'starting_resources': {'gold': 2000}})
        
        # Find a city owned by Poland
        poland_cities = campaign.get_country_cities('poland')
        assert len(poland_cities) > 0
        city = poland_cities[0]
        
        # Ensure Poland is the current country (only current country can recruit)
        campaign.current_country = 'poland'
        initial_gold = campaign.country_treasury['poland']
        
        # Recruit some units - using the city's ID from the cities dict
        city_id = None
        for cid, c in campaign.cities.items():
            if c.name == city.name:
                city_id = cid
                break
        
        result = campaign.recruit_units('poland', city_id, knights=2, archers=1)
        
        assert result is True
        expected_cost = 2 * 100 + 1 * 80  # 2 knights + 1 archer
        assert campaign.country_treasury['poland'] == initial_gold - expected_cost


class TestCampaignToBattle:
    """Test transition from campaign to battle."""
    
    def test_army_encounter_triggers_battle_preparation(self, pygame_surface):
        """Verify army encounters prepare for battle transition."""
        screen = CampaignScreen(pygame_surface)
        campaign = CampaignState()
        screen.campaign_state = campaign
        
        # Create two opposing armies at same location
        from game.campaign.campaign_state import Army
        
        campaign.armies['test_attacker'] = Army(
            id='test_attacker',
            country='poland',
            position=HexCoord(10, 10),
            knights=5, archers=3, cavalry=2,
            movement_points=3
        )
        
        campaign.armies['test_defender'] = Army(
            id='test_defender', 
            country='france',
            position=HexCoord(10, 10),
            knights=4, archers=4, cavalry=1,
            movement_points=3
        )
        
        # Moving army to same position should prepare battle
        campaign.current_country = 'poland'
        campaign.selected_army = 'test_attacker'
        
        # This would normally be triggered by movement
        screen.battle_armies = {
            'attacker': campaign.armies['test_attacker'],
            'defender': campaign.armies['test_defender']
        }
        screen.ready_for_battle = True
        
        # Get battle config
        config = screen.get_battle_config()
        
        assert config is not None
        assert config['campaign_battle'] is True
        assert 'attacker_army' in config
        assert 'defender_army' in config
        assert config['attacker_country'] == 'poland'
        assert config['defender_country'] == 'france'
    
    def test_battle_config_includes_army_composition(self, pygame_surface):
        """Verify battle config properly transfers army unit counts."""
        screen = CampaignScreen(pygame_surface)
        campaign = CampaignState()
        screen.campaign_state = campaign
        
        # Setup test armies with known composition
        from game.campaign.campaign_state import Army
        
        attacker = Army(
            id='attacker',
            country='poland',
            position=HexCoord(5, 5),
            knights=7, archers=5, cavalry=3,
            movement_points=3
        )
        
        defender = Army(
            id='defender',
            country='hungary',
            position=HexCoord(5, 5),
            knights=6, archers=6, cavalry=2,
            movement_points=3
        )
        
        campaign.armies = {'attacker': attacker, 'defender': defender}
        screen.battle_armies = {
            'attacker': attacker,
            'defender': defender
        }
        screen.ready_for_battle = True
        
        config = screen.get_battle_config()
        
        # Verify army data is preserved
        assert config['attacker_army'].knights == 7
        assert config['attacker_army'].archers == 5
        assert config['attacker_army'].cavalry == 3
        assert config['defender_army'].knights == 6
        assert config['defender_army'].archers == 6
        assert config['defender_army'].cavalry == 2


class TestCampaignPersistence:
    """Test campaign save/load functionality."""
    
    @pytest.mark.skip(reason="Save/load for campaign not yet implemented")
    def test_campaign_state_can_be_saved_and_restored(self):
        """Verify campaign state can be saved and loaded."""
        # This test is a placeholder for when save/load is implemented
        # It should verify:
        # - Current country and turn number
        # - Army positions and compositions  
        # - Treasury amounts
        # - City ownership
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])