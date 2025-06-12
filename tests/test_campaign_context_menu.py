import pytest
import pygame
from game.ui.campaign_screen import CampaignScreen
from game.campaign.campaign_state import CampaignState, City, Country, Army
from game.hex_utils import HexCoord


@pytest.fixture
def setup_pygame():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    yield screen
    pygame.quit()


@pytest.fixture
def campaign_screen(setup_pygame):
    screen = setup_pygame
    campaign_screen = CampaignScreen(screen)
    # Create a minimal campaign state without loading default data
    campaign_screen.campaign_state = CampaignState.__new__(CampaignState)
    campaign_screen.campaign_state.player_country = "france"
    campaign_screen.campaign_state.current_country = "france"
    campaign_screen.campaign_state.turn_number = 1
    campaign_screen.campaign_state.countries = {}
    campaign_screen.campaign_state.cities = {}
    campaign_screen.campaign_state.armies = {}
    campaign_screen.campaign_state.country_treasury = {}
    campaign_screen.campaign_state.territory_ownership = {}
    campaign_screen.campaign_state.selected_army = None
    campaign_screen.campaign_state.selected_city = None
    campaign_screen.campaign_state.map_width = 20
    campaign_screen.campaign_state.map_height = 20
    from game.hex_layout import HexLayout
    campaign_screen.campaign_state.hex_layout = HexLayout(hex_size=24)
    
    # Add test country
    test_country = Country(
        id="france",
        name="France",
        color=(0, 0, 255),
        capital="Paris",
        description="Kingdom of France",
        starting_resources={"treasury": 1000},
        bonuses={}
    )
    campaign_screen.campaign_state.countries["france"] = test_country
    campaign_screen.campaign_state.player_country = "france"
    campaign_screen.campaign_state.current_country = "france"
    campaign_screen.campaign_state.country_treasury["france"] = 1000
    
    # Add test city
    test_city = City(
        name="Paris",
        country="france",
        position=HexCoord(5, 5),
        city_type="capital",
        income=100,
        castle_level=3,
        population=50000,
        specialization="trade",
        description="The capital of France"
    )
    campaign_screen.campaign_state.cities["paris"] = test_city
    
    # Add test army
    test_army = Army(
        id="army1",
        country="france",
        position=HexCoord(5, 5),
        knights=10,
        archers=5,
        cavalry=3,
        movement_points=3
    )
    campaign_screen.campaign_state.armies["army1"] = test_army
    
    return campaign_screen


def test_right_click_on_city_shows_context_menu(campaign_screen):
    """Test that right-clicking on a city shows the context menu"""
    # Set camera to (0, 0) for predictable positioning
    campaign_screen.renderer.camera_x = 0
    campaign_screen.renderer.camera_y = 0
    
    # Calculate screen position for hex (5, 5)
    hex_layout = campaign_screen.campaign_state.hex_layout
    screen_pos = campaign_screen.renderer.hex_to_screen(HexCoord(5, 5), hex_layout)
    
    # Simulate right-click
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'pos': (int(screen_pos[0]), int(screen_pos[1])),
        'button': 3
    })
    
    campaign_screen.handle_event(event)
    
    # Check that context menu is visible
    assert campaign_screen.context_menu.visible
    assert campaign_screen.context_menu.target_city is not None
    assert campaign_screen.context_menu.target_city.name == "Paris"


def test_context_menu_city_info_opens_modal(campaign_screen):
    """Test that selecting 'City Information' opens the city info modal"""
    # Show context menu for city
    city = campaign_screen.campaign_state.cities["paris"]
    campaign_screen.context_menu.show_for_city(400, 300, city, campaign_screen.campaign_state)
    
    # Find the 'City Information' option
    info_action = None
    for i, option in enumerate(campaign_screen.context_menu.options):
        if option['action'] == 'show_info':
            # Calculate click position for this option
            click_y = campaign_screen.context_menu.y + i * campaign_screen.context_menu.option_height + 15
            info_action = (campaign_screen.context_menu.x + 50, click_y)
            break
    
    assert info_action is not None
    
    # Simulate clicking on 'City Information'
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'pos': info_action,
        'button': 1
    })
    
    campaign_screen.handle_event(event)
    
    # Check that city info modal is visible
    assert campaign_screen.city_info_modal.visible
    assert campaign_screen.city_info_modal.city.name == "Paris"
    assert campaign_screen.city_info_modal.country.name == "France"


def test_city_info_modal_closes_on_escape(campaign_screen):
    """Test that the city info modal closes when pressing ESC"""
    # Open the modal
    city = campaign_screen.campaign_state.cities["paris"]
    country = campaign_screen.campaign_state.countries["france"]
    campaign_screen.city_info_modal.show(city, country, (800, 600))
    
    assert campaign_screen.city_info_modal.visible
    
    # Press ESC
    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE})
    campaign_screen.handle_event(event)
    
    # Check that modal is closed
    assert not campaign_screen.city_info_modal.visible


def test_city_info_modal_closes_on_click_outside(campaign_screen):
    """Test that the city info modal closes when clicking outside"""
    # Open the modal
    city = campaign_screen.campaign_state.cities["paris"]
    country = campaign_screen.campaign_state.countries["france"]
    campaign_screen.city_info_modal.show(city, country, (800, 600))
    
    assert campaign_screen.city_info_modal.visible
    
    # Draw the modal to clear the just_shown flag
    screen = pygame.display.get_surface()
    campaign_screen.city_info_modal.draw(screen)
    
    # Click outside the modal
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'pos': (10, 10),  # Far from center where modal appears
        'button': 1
    })
    campaign_screen.handle_event(event)
    
    # Check that modal is closed
    assert not campaign_screen.city_info_modal.visible


def test_select_army_from_context_menu(campaign_screen):
    """Test selecting an army from the context menu"""
    # Show context menu for army
    army = campaign_screen.campaign_state.armies["army1"]
    campaign_screen.context_menu.show_for_army(400, 300, army, campaign_screen.campaign_state)
    
    # Find the 'Select Army' option
    select_action = None
    for i, option in enumerate(campaign_screen.context_menu.options):
        if option['action'] == 'select_army':
            # Calculate click position for this option
            click_y = campaign_screen.context_menu.y + i * campaign_screen.context_menu.option_height + 15
            select_action = (campaign_screen.context_menu.x + 50, click_y)
            break
    
    assert select_action is not None
    
    # Simulate clicking on 'Select Army'
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'pos': select_action,
        'button': 1
    })
    
    campaign_screen.handle_event(event)
    
    # Check that army is selected
    assert campaign_screen.campaign_state.selected_army == "army1"


def test_recruitment_from_context_menu(campaign_screen):
    """Test recruiting units from a city via context menu"""
    # Ensure country has enough treasury
    campaign_screen.campaign_state.country_treasury["france"] = 500
    
    # Show context menu for city
    city = campaign_screen.campaign_state.cities["paris"]
    campaign_screen.context_menu.show_for_city(400, 300, city, campaign_screen.campaign_state)
    
    # Find the 'Recruit Army' option
    recruit_action = None
    for i, option in enumerate(campaign_screen.context_menu.options):
        if option['action'] == 'recruit':
            # Calculate click position for this option
            click_y = campaign_screen.context_menu.y + i * campaign_screen.context_menu.option_height + 15
            recruit_action = (campaign_screen.context_menu.x + 50, click_y)
            break
    
    assert recruit_action is not None
    
    # Count armies before recruitment
    armies_before = len(campaign_screen.campaign_state.armies)
    
    # Simulate clicking on 'Recruit Army'
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'pos': recruit_action,
        'button': 1
    })
    
    campaign_screen.handle_event(event)
    
    # Check that a new army was created
    assert len(campaign_screen.campaign_state.armies) == armies_before + 1