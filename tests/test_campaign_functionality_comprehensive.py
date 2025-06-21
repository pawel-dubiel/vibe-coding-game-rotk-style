import pytest
import pygame
import time
from game.ui.campaign_screen import CampaignScreen
from game.campaign.campaign_state import CampaignState, City, Country, Army
from game.hex_utils import HexCoord


@pytest.fixture
def pygame_setup():
    """Setup pygame for testing"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    yield screen
    pygame.quit()


@pytest.fixture
def campaign_screen_with_data(pygame_setup):
    """Create campaign screen with test data"""
    screen = pygame_setup
    campaign_screen = CampaignScreen(screen)
    campaign_screen._ensure_campaign_state()
    
    # Add test country if needed
    if "test_country" not in campaign_screen.campaign_state.countries:
        test_country = Country(
            id="test_country",
            name="Test Kingdom",
            color=(255, 0, 0),
            capital="Test City",
            description="A test kingdom",
            starting_resources={"treasury": 1000},
            bonuses={}
        )
        campaign_screen.campaign_state.countries["test_country"] = test_country
        campaign_screen.campaign_state.country_treasury["test_country"] = 1000
    
    # Add test city
    test_city = City(
        name="Test City",
        country="test_country",
        position=HexCoord(10, 10),
        city_type="capital",
        income=100,
        castle_level=3,
        population=50000,
        specialization="trade",
        description="A test city for comprehensive testing"
    )
    campaign_screen.campaign_state.cities["test_city"] = test_city
    
    # Add test army
    test_army = Army(
        id="test_army",
        country="test_country",
        position=HexCoord(11, 11),
        knights=10,
        archers=5,
        cavalry=3,
        movement_points=3
    )
    campaign_screen.campaign_state.armies["test_army"] = test_army
    
    # Set test country as current
    campaign_screen.campaign_state.current_country = "test_country"
    campaign_screen.campaign_state.player_country = "test_country"
    
    return campaign_screen


class TestCityInformationModal:
    """Test city information modal functionality"""
    
    def test_city_info_modal_shows_from_context_menu(self, campaign_screen_with_data):
        """Test that city information modal opens when selected from context menu"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        
        # Show context menu for city
        campaign_screen.context_menu.show_for_city(400, 300, city, campaign_screen.campaign_state)
        
        # Verify context menu is visible
        assert campaign_screen.context_menu.visible
        assert campaign_screen.context_menu.target_city == city
        
        # Find "City Information" option
        info_option_index = None
        for i, option in enumerate(campaign_screen.context_menu.options):
            if option['action'] == 'show_info':
                info_option_index = i
                break
        
        assert info_option_index is not None, "City Information option not found in context menu"
        
        # Test the action directly
        campaign_screen._handle_context_action('show_info')
        
        # Verify modal is now visible
        assert campaign_screen.city_info_modal.visible, "City info modal should be visible after action"
        assert campaign_screen.city_info_modal.city == city
        assert campaign_screen.city_info_modal.country is not None
        assert campaign_screen.city_info_modal.country.name == "Test Kingdom"
    
    def test_city_info_modal_displays_correct_information(self, campaign_screen_with_data):
        """Test that city information modal displays the correct city data"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        country = campaign_screen.campaign_state.countries["test_country"]
        
        # Show modal directly
        campaign_screen.city_info_modal.show(city, country, (800, 600))
        
        # Verify modal contains correct data
        assert campaign_screen.city_info_modal.visible
        assert campaign_screen.city_info_modal.city.name == "Test City"
        assert campaign_screen.city_info_modal.city.income == 100
        assert campaign_screen.city_info_modal.city.population == 50000
        assert campaign_screen.city_info_modal.city.castle_level == 3
        assert campaign_screen.city_info_modal.city.specialization == "trade"
        assert campaign_screen.city_info_modal.country.name == "Test Kingdom"
    
    def test_city_info_modal_closes_on_escape(self, campaign_screen_with_data):
        """Test that city information modal closes when pressing ESC"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        country = campaign_screen.campaign_state.countries["test_country"]
        
        # Show modal
        campaign_screen.city_info_modal.show(city, country, (800, 600))
        assert campaign_screen.city_info_modal.visible
        
        # Press ESC
        esc_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE})
        consumed = campaign_screen.city_info_modal.handle_event(esc_event)
        
        assert consumed, "ESC event should be consumed by modal"
        assert not campaign_screen.city_info_modal.visible, "Modal should be hidden after ESC"


class TestArmyInformationModal:
    """Test army information modal functionality"""
    
    def test_army_info_modal_shows_from_context_menu(self, campaign_screen_with_data):
        """Test that army information modal opens when selected from context menu"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Show context menu for army
        campaign_screen.context_menu.show_for_army(400, 300, army, campaign_screen.campaign_state)
        
        # Verify context menu is visible
        assert campaign_screen.context_menu.visible
        assert campaign_screen.context_menu.target_army == army
        
        # Find "Army Information" option
        info_option_index = None
        for i, option in enumerate(campaign_screen.context_menu.options):
            if option['action'] == 'show_info':
                info_option_index = i
                break
        
        assert info_option_index is not None, "Army Information option not found in context menu"
        
        # Test the action directly
        campaign_screen._handle_context_action('show_info')
        
        # Verify modal is now visible
        assert campaign_screen.army_info_modal.visible, "Army info modal should be visible after action"
        assert campaign_screen.army_info_modal.army == army
        assert campaign_screen.army_info_modal.country is not None
        assert campaign_screen.army_info_modal.country.name == "Test Kingdom"
    
    def test_army_info_modal_displays_correct_information(self, campaign_screen_with_data):
        """Test that army information modal displays the correct army data"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        country = campaign_screen.campaign_state.countries["test_country"]
        
        # Show modal directly
        campaign_screen.army_info_modal.show(army, country, (800, 600))
        
        # Verify modal contains correct data
        assert campaign_screen.army_info_modal.visible
        assert campaign_screen.army_info_modal.army.id == "test_army"
        assert campaign_screen.army_info_modal.army.knights == 10
        assert campaign_screen.army_info_modal.army.archers == 5
        assert campaign_screen.army_info_modal.army.cavalry == 3
        assert campaign_screen.army_info_modal.army.movement_points == 3
        assert campaign_screen.army_info_modal.country.name == "Test Kingdom"


class TestArmySelection:
    """Test army selection functionality"""
    
    def test_select_army_from_context_menu(self, campaign_screen_with_data):
        """Test selecting an army from context menu"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Initially no army selected
        assert campaign_screen.campaign_state.selected_army is None
        
        # Show context menu for army
        campaign_screen.context_menu.show_for_army(400, 300, army, campaign_screen.campaign_state)
        
        # Execute select army action
        campaign_screen._handle_context_action('select_army')
        
        # Verify army is now selected
        assert campaign_screen.campaign_state.selected_army == "test_army"
    
    def test_army_selection_via_left_click(self, campaign_screen_with_data):
        """Test selecting army via left-click"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Convert hex position to screen position
        screen_pos = campaign_screen.renderer.hex_to_screen(army.position, campaign_screen.campaign_state.hex_layout)
        
        # Simulate left-click on army position
        left_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'pos': (int(screen_pos[0]), int(screen_pos[1])),
            'button': 1
        })
        
        campaign_screen.handle_event(left_click_event)
        
        # Verify army is selected
        assert campaign_screen.campaign_state.selected_army == "test_army"


class TestArmyMovement:
    """Test army movement functionality"""
    
    def test_army_movement_direct_method(self, campaign_screen_with_data):
        """Test army movement using move_army method directly"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        
        original_pos = army.position
        target_pos = HexCoord(original_pos.q + 1, original_pos.r)
        original_movement = army.movement_points
        
        # Move army
        result = campaign_screen.campaign_state.move_army("test_army", target_pos)
        
        assert result, "Army movement should succeed"
        assert army.position == target_pos, "Army should be at new position"
        assert army.movement_points == original_movement - 1, "Movement points should be reduced"
    
    def test_army_movement_via_right_click(self, campaign_screen_with_data):
        """Test army movement via right-click"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Select the army first
        campaign_screen.campaign_state.selected_army = "test_army"
        
        original_pos = army.position
        target_pos = HexCoord(original_pos.q + 1, original_pos.r)
        original_movement = army.movement_points
        
        # Convert target position to screen coordinates
        target_screen_pos = campaign_screen.renderer.hex_to_screen(target_pos, campaign_screen.campaign_state.hex_layout)
        
        # Simulate right-click on empty hex
        right_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'pos': (int(target_screen_pos[0]), int(target_screen_pos[1])),
            'button': 3
        })
        
        campaign_screen.handle_event(right_click_event)
        
        assert army.position == target_pos, "Army should move to clicked position"
        assert army.movement_points == original_movement - 1, "Movement points should be reduced"
    
    def test_army_movement_insufficient_points(self, campaign_screen_with_data):
        """Test that army cannot move without sufficient movement points"""
        campaign_screen = campaign_screen_with_data
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Reduce movement points to 0
        army.movement_points = 0
        original_pos = army.position
        target_pos = HexCoord(original_pos.q + 1, original_pos.r)
        
        # Try to move army
        result = campaign_screen.campaign_state.move_army("test_army", target_pos)
        
        assert not result, "Army movement should fail with no movement points"
        assert army.position == original_pos, "Army should stay at original position"


class TestCityArmySwitching:
    """Test switching between city and army when both are at same location"""
    
    def test_tab_switching_functionality(self, campaign_screen_with_data):
        """Test TAB key switching between city and army"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Move army to same position as city
        army.position = city.position
        
        # Left-click to select the position
        screen_pos = campaign_screen.renderer.hex_to_screen(city.position, campaign_screen.campaign_state.hex_layout)
        left_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'pos': (int(screen_pos[0]), int(screen_pos[1])),
            'button': 1
        })
        campaign_screen.handle_event(left_click_event)
        
        # Verify both city and army are selected
        assert campaign_screen.selected_city == city
        assert campaign_screen.selected_army is not None
        assert campaign_screen.selected_army[1] == army
        
        # Test TAB switching
        original_focus = campaign_screen.selection_focus
        
        tab_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_TAB})
        campaign_screen.handle_event(tab_event)
        
        # Focus should have switched
        assert campaign_screen.selection_focus != original_focus
    
    def test_context_menu_shows_switch_options(self, campaign_screen_with_data):
        """Test that context menu shows switch options when both city and army present"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        army = campaign_screen.campaign_state.armies["test_army"]
        
        # Test city context menu with army present
        campaign_screen.context_menu.show_for_city(400, 300, city, campaign_screen.campaign_state, has_army=True)
        
        # Check for switch option
        switch_options = [opt for opt in campaign_screen.context_menu.options if 'Switch to Army' in opt['text']]
        assert len(switch_options) > 0, "Context menu should have 'Switch to Army' option"
        
        # Test army context menu with city present
        campaign_screen.context_menu.show_for_army(400, 300, army, campaign_screen.campaign_state, has_city=True)
        
        # Check for switch option
        switch_options = [opt for opt in campaign_screen.context_menu.options if 'Switch to City' in opt['text']]
        assert len(switch_options) > 0, "Context menu should have 'Switch to City' option"


class TestContextMenuBehavior:
    """Test context menu behavior and edge cases"""
    
    def test_context_menu_appears_on_right_click(self, campaign_screen_with_data):
        """Test that context menu appears when right-clicking on entities"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        
        # Convert city position to screen coordinates
        screen_pos = campaign_screen.renderer.hex_to_screen(city.position, campaign_screen.campaign_state.hex_layout)
        
        # Simulate right-click
        right_click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'pos': (int(screen_pos[0]), int(screen_pos[1])),
            'button': 3
        })
        
        campaign_screen.handle_event(right_click_event)
        
        assert campaign_screen.context_menu.visible, "Context menu should be visible after right-click"
        assert campaign_screen.context_menu.target_city == city, "Context menu should target the city"
    
    def test_context_menu_closes_on_outside_click(self, campaign_screen_with_data):
        """Test that context menu closes when clicking outside"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        
        # Show context menu
        campaign_screen.context_menu.show_for_city(400, 300, city, campaign_screen.campaign_state)
        assert campaign_screen.context_menu.visible
        
        # Click outside menu (at position 10, 10 which should be outside)
        outside_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
            'pos': (10, 10),
            'button': 1
        })
        
        campaign_screen.handle_event(outside_click)
        
        assert not campaign_screen.context_menu.visible, "Context menu should close when clicking outside"


class TestRecruitment:
    """Test army recruitment functionality"""
    
    def test_recruitment_option_available_with_funds(self, campaign_screen_with_data):
        """Test that recruitment option is available when player has sufficient funds"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        
        # Ensure player has enough money
        campaign_screen.campaign_state.country_treasury["test_country"] = 500
        
        # Show context menu for player-owned city
        campaign_screen.context_menu.show_for_city(400, 300, city, campaign_screen.campaign_state)
        
        # Check for recruitment option
        recruit_options = [opt for opt in campaign_screen.context_menu.options 
                          if opt['action'] == 'recruit' and opt['enabled']]
        assert len(recruit_options) > 0, "Recruitment option should be available with sufficient funds"
    
    def test_recruitment_creates_army(self, campaign_screen_with_data):
        """Test that recruitment actually creates a new army"""
        campaign_screen = campaign_screen_with_data
        city = campaign_screen.campaign_state.cities["test_city"]
        
        # Ensure player has enough money
        campaign_screen.campaign_state.country_treasury["test_country"] = 500
        
        # Set up context menu
        campaign_screen.context_menu.target_city = city
        
        # Count armies before recruitment
        armies_before = len(campaign_screen.campaign_state.armies)
        treasury_before = campaign_screen.campaign_state.country_treasury["test_country"]
        
        # Execute recruitment
        campaign_screen._handle_context_action('recruit')
        
        # Verify army was created and treasury reduced
        assert len(campaign_screen.campaign_state.armies) == armies_before + 1, "New army should be created"
        assert campaign_screen.campaign_state.country_treasury["test_country"] == treasury_before - 100, "Treasury should be reduced"


class TestFallbackCountryHandling:
    """Test handling of cities with missing country data"""
    
    def test_city_with_missing_country_shows_modal(self, campaign_screen_with_data):
        """Test that cities with missing country data still show info modal"""
        campaign_screen = campaign_screen_with_data
        
        # Create city with non-existent country
        orphan_city = City(
            name="Orphan City",
            country="nonexistent_country",
            position=HexCoord(20, 20),
            city_type="city",
            income=50,
            castle_level=1,
            population=10000,
            specialization="agriculture",
            description="A city with missing country data"
        )
        campaign_screen.campaign_state.cities["orphan_city"] = orphan_city
        
        # Set up context menu
        campaign_screen.context_menu.target_city = orphan_city
        
        # Execute show_info action
        campaign_screen._handle_context_action('show_info')
        
        # Verify modal shows with fallback country
        assert campaign_screen.city_info_modal.visible, "Modal should show even with missing country"
        assert campaign_screen.city_info_modal.city == orphan_city
        assert campaign_screen.city_info_modal.country is not None, "Fallback country should be created"
        assert campaign_screen.city_info_modal.country.name == "Nonexistent_Country", "Fallback country should have proper name"


if __name__ == "__main__":
    # Run tests with verbose output
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))