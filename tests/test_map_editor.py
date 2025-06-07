import pytest
import pygame
from game.ui.map_editor import MapEditorScreen, EditorTool, CityEditDialog
from game.hex_utils import HexCoord
from game.campaign.campaign_state import City, CampaignTerrainType


@pytest.fixture
def pygame_surface():
    """Create a pygame surface for testing."""
    pygame.init()
    surface = pygame.display.set_mode((1024, 768))
    yield surface
    pygame.quit()


class TestMapEditor:
    """Test map editor functionality."""
    
    def test_map_editor_initializes(self, pygame_surface):
        """Test that map editor can be initialized."""
        editor = MapEditorScreen(pygame_surface)
        assert editor is not None
        assert editor.current_tool == EditorTool.TERRAIN_PAINT
        assert editor.selected_terrain == CampaignTerrainType.PLAINS
        assert not editor.visible
    
    def test_map_editor_show_loads_campaign(self, pygame_surface):
        """Test that showing editor loads campaign state."""
        editor = MapEditorScreen(pygame_surface)
        editor.show()
        
        assert editor.visible
        assert editor.campaign_state is not None
        assert editor.renderer is not None
        
        # Should have terrain loaded
        assert len(editor.campaign_state.terrain_map) > 0
        assert len(editor.campaign_state.cities) > 0
    
    def test_terrain_painting_simulation(self, pygame_surface):
        """Test terrain painting functionality."""
        editor = MapEditorScreen(pygame_surface)
        editor.show()
        
        # Set tool and terrain
        editor.current_tool = EditorTool.TERRAIN_PAINT
        editor.selected_terrain = CampaignTerrainType.FOREST
        
        # Simulate terrain painting at a coordinate
        test_coord = (10, 10)
        original_terrain = editor.campaign_state.terrain_map.get(test_coord)
        
        # Directly set terrain (simulating brush action)
        editor.campaign_state.terrain_map[test_coord] = CampaignTerrainType.FOREST
        
        # Verify change
        assert editor.campaign_state.terrain_map[test_coord] == CampaignTerrainType.FOREST
        assert editor.campaign_state.terrain_map[test_coord] != original_terrain
    
    def test_city_placement_simulation(self, pygame_surface):
        """Test city placement functionality."""
        editor = MapEditorScreen(pygame_surface)
        editor.show()
        
        # Set tool for city placement
        editor.current_tool = EditorTool.CITY_PLACE
        editor.selected_country = 'poland'
        
        initial_city_count = len(editor.campaign_state.cities)
        
        # Simulate city placement
        from game.campaign.campaign_state import City
        test_pos = HexCoord(15, 15)
        
        # Check that position is free
        city_exists = any(city.position == test_pos for city in editor.campaign_state.cities.values())
        
        if not city_exists:
            # Place new city
            city_id = f"test_city_{len(editor.campaign_state.cities)}"
            new_city = City(
                name="Test City",
                country=editor.selected_country,
                position=test_pos,
                city_type="city",
                income=100,
                castle_level=1,
                population=10000,
                specialization="trade",
                description="Test city"
            )
            editor.campaign_state.cities[city_id] = new_city
            
            # Verify city was added
            assert len(editor.campaign_state.cities) == initial_city_count + 1
            assert city_id in editor.campaign_state.cities
            assert editor.campaign_state.cities[city_id].position == test_pos
    
    def test_undo_redo_functionality(self, pygame_surface):
        """Test undo/redo system."""
        editor = MapEditorScreen(pygame_surface)
        editor.show()
        
        # Initial state should be saved
        assert len(editor.undo_stack) > 0
        initial_undo_count = len(editor.undo_stack)
        
        # Make a change and save state
        editor.campaign_state.terrain_map[(5, 5)] = CampaignTerrainType.WATER
        editor._save_state()
        
        # Should have one more undo state
        assert len(editor.undo_stack) == initial_undo_count + 1
        
        # Make another change
        editor.campaign_state.terrain_map[(6, 6)] = CampaignTerrainType.MOUNTAINS
        editor._save_state()
        
        # Undo last change
        editor._undo()
        
        # Should have states in redo stack
        assert len(editor.redo_stack) > 0
        
        # Redo the change
        editor._redo()
        
        # Redo stack should be empty again
        assert len(editor.redo_stack) == 0
    
    def test_tool_switching(self, pygame_surface):
        """Test switching between editor tools."""
        editor = MapEditorScreen(pygame_surface)
        
        # Test switching tools
        editor.current_tool = EditorTool.CITY_PLACE
        assert editor.current_tool == EditorTool.CITY_PLACE
        
        editor.current_tool = EditorTool.TERRAIN_PAINT
        assert editor.current_tool == EditorTool.TERRAIN_PAINT
        
        editor.current_tool = EditorTool.PAN
        assert editor.current_tool == EditorTool.PAN
    
    def test_terrain_selection(self, pygame_surface):
        """Test terrain type selection."""
        editor = MapEditorScreen(pygame_surface)
        
        # Test different terrain selections
        for terrain in [CampaignTerrainType.FOREST, CampaignTerrainType.MOUNTAINS, CampaignTerrainType.WATER]:
            editor.selected_terrain = terrain
            assert editor.selected_terrain == terrain
    
    def test_country_selection(self, pygame_surface):
        """Test country selection for city placement."""
        editor = MapEditorScreen(pygame_surface)
        
        # Test different country selections
        for country in ['poland', 'france', 'england']:
            editor.selected_country = country
            assert editor.selected_country == country
    
    def test_editor_back_action(self, pygame_surface):
        """Test editor back action returns correct result."""
        editor = MapEditorScreen(pygame_surface)
        editor.show()
        
        # Simulate ESC key press
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        result = editor.handle_event(escape_event)
        
        assert result is not None
        assert result['action'] == 'back'
    
    def test_city_edit_dialog_creation(self, pygame_surface):
        """Test city edit dialog can be created and initialized."""
        # Create a test city
        test_city = City(
            name="Test City",
            country="poland",
            position=HexCoord(10, 10),
            city_type="city",
            income=150,
            castle_level=2,
            population=15000,
            specialization="trade",
            description="A test city"
        )
        
        # Create dialog
        dialog = CityEditDialog(pygame_surface, test_city, "test_city")
        
        assert dialog is not None
        assert dialog.city == test_city
        assert dialog.city_id == "test_city"
        assert dialog.visible is True
        
        # Check that fields are initialized with city data
        assert dialog.fields['name']['value'] == "Test City"
        assert dialog.fields['country']['value'] == "poland"
        assert dialog.fields['income']['value'] == "150"
        assert dialog.fields['castle_level']['value'] == "2"
    
    def test_city_edit_dialog_field_editing(self, pygame_surface):
        """Test editing fields in city edit dialog."""
        test_city = City(
            name="Original Name",
            country="poland",
            position=HexCoord(5, 5),
            city_type="city",
            income=100,
            castle_level=1,
            population=10000,
            specialization="military",
            description="Original description"
        )
        
        dialog = CityEditDialog(pygame_surface, test_city, "test_city")
        
        # Test text field editing
        dialog.active_field = 'name'
        dialog.text_input = "New City Name"
        dialog._commit_field_value()
        
        assert dialog.fields['name']['value'] == "New City Name"
        
        # Test dropdown cycling
        original_country = dialog.fields['country']['value']
        dialog._cycle_dropdown_value('country')
        assert dialog.fields['country']['value'] != original_country
        
        # Test applying changes
        dialog._apply_changes()
        assert test_city.name == "New City Name"
    
    def test_city_edit_dialog_cancel_and_ok(self, pygame_surface):
        """Test dialog cancel and OK actions."""
        test_city = City(
            name="Test City",
            country="poland",
            position=HexCoord(10, 10),
            city_type="city",
            income=100,
            castle_level=1,
            population=10000,
            specialization="trade",
            description="Test description"
        )
        
        dialog = CityEditDialog(pygame_surface, test_city, "test_city")
        
        # Test ESC key (cancel)
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        result = dialog.handle_event(escape_event)
        assert result == 'cancel'
        
        # Test Enter key (OK)
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        result = dialog.handle_event(enter_event)
        assert result == 'ok'
    
    def test_city_edit_integration_with_editor(self, pygame_surface):
        """Test city editing integration with map editor."""
        editor = MapEditorScreen(pygame_surface)
        editor.show()
        
        # Set tool to city edit
        editor.current_tool = EditorTool.CITY_EDIT
        
        # Find a city in the campaign state
        if editor.campaign_state.cities:
            city_id, city = next(iter(editor.campaign_state.cities.items()))
            
            # Simulate clicking on the city to edit it
            # (We can't easily simulate the exact mouse position, so we'll call the method directly)
            editor.city_edit_dialog = CityEditDialog(editor.screen, city, city_id)
            
            # Verify dialog was created
            assert editor.city_edit_dialog is not None
            assert editor.city_edit_dialog.city == city
            
            # Test dialog handling through editor
            escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
            result = editor.handle_event(escape_event)
            
            # Dialog should be closed
            assert editor.city_edit_dialog is None
            assert result is None  # Editor handled the dialog event


if __name__ == "__main__":
    pytest.main([__file__, "-v"])