"""Map Editor for campaign maps.

Provides tools to edit terrain, place/remove cities, and modify map data.
"""

import pygame
import json
import os
from typing import Optional, Dict, List, Tuple, Any
from enum import Enum
from game.campaign.campaign_state import CampaignState, City, Country, CampaignTerrainType
from game.campaign.campaign_renderer import CampaignRenderer
from game.hex_utils import HexCoord


class EditorTool(Enum):
    """Available editor tools"""
    TERRAIN_PAINT = "terrain_paint"
    CITY_PLACE = "city_place"
    CITY_REMOVE = "city_remove"
    CITY_EDIT = "city_edit"
    PAN = "pan"


class CityEditDialog:
    """Dialog for editing city properties"""
    
    def __init__(self, screen: pygame.Surface, city: City, city_id: str):
        self.screen = screen
        self.city = city
        self.city_id = city_id
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        
        # Dialog state
        self.visible = True
        self.active_field = None
        self.text_input = ""
        
        # Editable fields
        self.fields = {
            'name': {'value': city.name, 'type': 'text', 'label': 'City Name'},
            'country': {'value': city.country, 'type': 'dropdown', 'label': 'Country', 
                       'options': ['poland', 'france', 'england', 'holy_roman_empire', 'hungary', 'denmark']},
            'city_type': {'value': city.city_type, 'type': 'dropdown', 'label': 'Type',
                         'options': ['capital', 'city', 'port', 'fortress']},
            'income': {'value': str(city.income), 'type': 'number', 'label': 'Income'},
            'castle_level': {'value': str(city.castle_level), 'type': 'number', 'label': 'Castle Level'},
            'population': {'value': str(city.population), 'type': 'number', 'label': 'Population'},
            'specialization': {'value': city.specialization, 'type': 'dropdown', 'label': 'Specialization',
                              'options': ['military', 'trade', 'religious', 'administrative', 'agricultural']},
            'description': {'value': city.description, 'type': 'text', 'label': 'Description'}
        }
        
        # Colors
        self.colors = {
            'dialog_bg': (50, 50, 50),
            'dialog_border': (100, 100, 100),
            'field_bg': (70, 70, 70),
            'field_active': (90, 90, 90),
            'field_border': (120, 120, 120),
            'button': (80, 80, 80),
            'button_hover': (100, 100, 100),
            'button_ok': (80, 120, 80),
            'button_cancel': (120, 80, 80),
            'text': (255, 255, 255),
            'text_dim': (180, 180, 180)
        }
        
        # Setup dialog layout
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup dialog layout and input fields"""
        screen_width, screen_height = self.screen.get_size()
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 500
        self.dialog_x = (screen_width - self.dialog_width) // 2
        self.dialog_y = (screen_height - self.dialog_height) // 2
        
        self.dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        
        # Field layout
        self.field_rects = {}
        self.dropdown_rects = {}
        field_height = 30
        field_spacing = 45
        start_y = self.dialog_y + 50
        
        for i, (field_name, field_data) in enumerate(self.fields.items()):
            y = start_y + i * field_spacing
            field_rect = pygame.Rect(self.dialog_x + 20, y + 20, self.dialog_width - 40, field_height)
            self.field_rects[field_name] = field_rect
            
            # For dropdowns, create button rects for options
            if field_data['type'] == 'dropdown':
                self.dropdown_rects[field_name] = []
        
        # Buttons
        button_width = 80
        button_height = 35
        button_y = self.dialog_y + self.dialog_height - 50
        
        self.ok_button = pygame.Rect(
            self.dialog_x + self.dialog_width - 2 * button_width - 30,
            button_y,
            button_width,
            button_height
        )
        
        self.cancel_button = pygame.Rect(
            self.dialog_x + self.dialog_width - button_width - 10,
            button_y,
            button_width,
            button_height
        )
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle dialog events. Returns 'ok', 'cancel', or None"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # Check buttons
            if self.ok_button.collidepoint(mouse_pos):
                self._apply_changes()
                return 'ok'
            elif self.cancel_button.collidepoint(mouse_pos):
                return 'cancel'
            
            # Check field clicks
            self.active_field = None
            for field_name, rect in self.field_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.active_field = field_name
                    if self.fields[field_name]['type'] == 'text':
                        self.text_input = self.fields[field_name]['value']
                    elif self.fields[field_name]['type'] == 'number':
                        self.text_input = self.fields[field_name]['value']
                    elif self.fields[field_name]['type'] == 'dropdown':
                        self._cycle_dropdown_value(field_name)
                    break
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'cancel'
            elif event.key == pygame.K_RETURN:
                if self.active_field:
                    self._commit_field_value()
                else:
                    self._apply_changes()
                    return 'ok'
            elif event.key == pygame.K_TAB:
                self._next_field()
            elif self.active_field and self.fields[self.active_field]['type'] in ['text', 'number']:
                self._handle_text_input(event)
        
        return None
    
    def _cycle_dropdown_value(self, field_name: str):
        """Cycle through dropdown options"""
        field_data = self.fields[field_name]
        current_value = field_data['value']
        options = field_data['options']
        
        try:
            current_index = options.index(current_value)
            next_index = (current_index + 1) % len(options)
            field_data['value'] = options[next_index]
        except ValueError:
            # Current value not in options, set to first option
            field_data['value'] = options[0]
    
    def _handle_text_input(self, event: pygame.event.Event):
        """Handle text input for active field"""
        if event.key == pygame.K_BACKSPACE:
            self.text_input = self.text_input[:-1]
        elif event.unicode.isprintable():
            # For number fields, only allow digits and one decimal point
            if self.fields[self.active_field]['type'] == 'number':
                if event.unicode.isdigit() or (event.unicode == '.' and '.' not in self.text_input):
                    self.text_input += event.unicode
            else:
                self.text_input += event.unicode
    
    def _commit_field_value(self):
        """Commit the current text input to the active field"""
        if self.active_field and self.fields[self.active_field]['type'] in ['text', 'number']:
            self.fields[self.active_field]['value'] = self.text_input
            self.active_field = None
            self.text_input = ""
    
    def _next_field(self):
        """Move to next editable field"""
        field_names = list(self.fields.keys())
        if self.active_field:
            try:
                current_index = field_names.index(self.active_field)
                next_index = (current_index + 1) % len(field_names)
                self.active_field = field_names[next_index]
            except ValueError:
                self.active_field = field_names[0]
        else:
            self.active_field = field_names[0]
        
        # Set text input for text/number fields
        if self.fields[self.active_field]['type'] in ['text', 'number']:
            self.text_input = self.fields[self.active_field]['value']
    
    def _apply_changes(self):
        """Apply all field changes to the city object"""
        try:
            # Commit current text input
            if self.active_field and self.fields[self.active_field]['type'] in ['text', 'number']:
                self.fields[self.active_field]['value'] = self.text_input
            
            # Apply changes to city
            self.city.name = self.fields['name']['value']
            self.city.country = self.fields['country']['value']
            self.city.city_type = self.fields['city_type']['value']
            self.city.income = int(self.fields['income']['value']) if self.fields['income']['value'].isdigit() else self.city.income
            self.city.castle_level = int(self.fields['castle_level']['value']) if self.fields['castle_level']['value'].isdigit() else self.city.castle_level
            self.city.population = int(self.fields['population']['value']) if self.fields['population']['value'].isdigit() else self.city.population
            self.city.specialization = self.fields['specialization']['value']
            self.city.description = self.fields['description']['value']
            
        except ValueError as e:
            print(f"Error applying city changes: {e}")
    
    def draw(self):
        """Draw the city edit dialog"""
        if not self.visible:
            return
        
        # Draw overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog background
        pygame.draw.rect(self.screen, self.colors['dialog_bg'], self.dialog_rect)
        pygame.draw.rect(self.screen, self.colors['dialog_border'], self.dialog_rect, 2)
        
        # Draw title
        title_text = self.title_font.render(f"Edit City: {self.city.name}", True, self.colors['text'])
        title_rect = title_text.get_rect(centerx=self.dialog_rect.centerx, y=self.dialog_y + 10)
        self.screen.blit(title_text, title_rect)
        
        # Draw fields
        mouse_pos = pygame.mouse.get_pos()
        
        for field_name, field_data in self.fields.items():
            rect = self.field_rects[field_name]
            
            # Draw label
            label_text = self.font.render(field_data['label'] + ":", True, self.colors['text'])
            self.screen.blit(label_text, (rect.x, rect.y - 20))
            
            # Draw field
            is_active = field_name == self.active_field
            field_color = self.colors['field_active'] if is_active else self.colors['field_bg']
            
            pygame.draw.rect(self.screen, field_color, rect)
            pygame.draw.rect(self.screen, self.colors['field_border'], rect, 1)
            
            # Draw field value
            if is_active and field_data['type'] in ['text', 'number']:
                display_text = self.text_input
                # Show cursor
                if pygame.time.get_ticks() % 1000 < 500:  # Blink cursor
                    display_text += "|"
            else:
                display_text = field_data['value']
            
            # Truncate text if too long
            max_chars = (rect.width - 10) // 8  # Approximate character width
            if len(display_text) > max_chars:
                display_text = display_text[:max_chars-3] + "..."
            
            text_surface = self.font.render(display_text, True, self.colors['text'])
            text_rect = text_surface.get_rect(centery=rect.centery, x=rect.x + 5)
            self.screen.blit(text_surface, text_rect)
        
        # Draw buttons
        self._draw_button(self.ok_button, "OK", mouse_pos, self.colors['button_ok'])
        self._draw_button(self.cancel_button, "Cancel", mouse_pos, self.colors['button_cancel'])
        
        # Draw instructions
        instructions = [
            "Click fields to edit • Tab to navigate • Enter to confirm • Esc to cancel"
        ]
        y_offset = self.dialog_y + self.dialog_height - 80
        for instruction in instructions:
            text_surface = pygame.font.Font(None, 18).render(instruction, True, self.colors['text_dim'])
            text_rect = text_surface.get_rect(centerx=self.dialog_rect.centerx, y=y_offset)
            self.screen.blit(text_surface, text_rect)
            y_offset += 20
    
    def _draw_button(self, rect: pygame.Rect, text: str, mouse_pos: Tuple[int, int], base_color: Tuple[int, int, int]):
        """Draw a button"""
        color = self.colors['button_hover'] if rect.collidepoint(mouse_pos) else base_color
        
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.colors['dialog_border'], rect, 1)
        
        text_surface = self.font.render(text, True, self.colors['text'])
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)


class MapEditorScreen:
    """Main map editor interface"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # Editor state
        self.visible = False
        self.campaign_state = None
        self.renderer = None
        self.current_tool = EditorTool.TERRAIN_PAINT
        self.selected_terrain = CampaignTerrainType.PLAINS
        self.selected_country = 'poland'
        
        # UI elements
        self.tool_panel_width = 200
        self.tool_buttons = {}
        self.terrain_buttons = {}
        self.country_buttons = {}
        
        # City edit dialog
        self.city_edit_dialog = None
        
        # Mouse state
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
        self.dragging = False
        self.drag_start = None
        
        # Undo system
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50
        
        # Colors
        self.colors = {
            'panel_bg': (40, 40, 40),
            'panel_border': (80, 80, 80),
            'button': (60, 60, 60),
            'button_hover': (80, 80, 80),
            'button_selected': (100, 150, 100),
            'text': (255, 255, 255),
            'text_dim': (180, 180, 180)
        }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI elements"""
        # Tool buttons
        tools = [
            (EditorTool.TERRAIN_PAINT, "Paint Terrain"),
            (EditorTool.CITY_PLACE, "Place City"),
            (EditorTool.CITY_REMOVE, "Remove City"),
            (EditorTool.CITY_EDIT, "Edit City"),
            (EditorTool.PAN, "Pan View")
        ]
        
        y_offset = 50
        for i, (tool, label) in enumerate(tools):
            rect = pygame.Rect(10, y_offset + i * 35, 180, 30)
            self.tool_buttons[tool] = {'rect': rect, 'label': label}
        
        # Campaign terrain type buttons
        terrain_types = [
            CampaignTerrainType.PLAINS, CampaignTerrainType.FOREST, CampaignTerrainType.DEEP_FOREST,
            CampaignTerrainType.HILLS, CampaignTerrainType.MOUNTAINS, CampaignTerrainType.HIGH_MOUNTAINS,
            CampaignTerrainType.WATER, CampaignTerrainType.DEEP_WATER, CampaignTerrainType.SWAMP,
            CampaignTerrainType.DESERT, CampaignTerrainType.SNOW, CampaignTerrainType.GLACIAL
        ]
        
        y_offset = 200  # Start higher since we have more terrain types
        for i, terrain in enumerate(terrain_types):
            rect = pygame.Rect(10, y_offset + i * 25, 180, 22)  # Smaller buttons to fit more
            # Clean up terrain name for display
            display_name = terrain.value.replace('_', ' ').title()
            self.terrain_buttons[terrain] = {'rect': rect, 'label': display_name}
        
        # Country buttons (for city placement)
        countries = ['poland', 'france', 'england', 'holy_roman_empire', 'hungary', 'denmark']
        y_offset = 500  # Move down to accommodate more terrain buttons
        for i, country in enumerate(countries):
            rect = pygame.Rect(10, y_offset + i * 25, 180, 20)
            self.country_buttons[country] = {'rect': rect, 'label': country.replace('_', ' ').title()}
    
    def show(self):
        """Show the map editor"""
        self.visible = True
        
        # Load or create campaign state for editing
        if not self.campaign_state:
            self.campaign_state = CampaignState()
        
        if not self.renderer:
            self.renderer = CampaignRenderer(self.screen)
        
        # Save initial state for undo
        self._save_state()
    
    def hide(self):
        """Hide the map editor"""
        self.visible = False
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Dict[str, Any]]:
        """Handle editor events"""
        if not self.visible:
            return None
        
        # Handle city edit dialog if open
        if self.city_edit_dialog:
            result = self.city_edit_dialog.handle_event(event)
            if result == 'ok':
                self._save_state()  # Save after editing
                self.city_edit_dialog = None
                return None
            elif result == 'cancel':
                self.city_edit_dialog = None
                return None
            else:
                return None  # Dialog is handling the event
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return {'action': 'back'}
            elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                self._save_map()
                return None
            elif event.key == pygame.K_z and pygame.key.get_pressed()[pygame.K_LCTRL]:
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    self._redo()
                else:
                    self._undo()
                return None
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.mouse_pressed = True
                self._handle_left_click(event.pos)
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_pressed = False
                self.dragging = False
                self.drag_start = None
        
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            if self.mouse_pressed and self.current_tool == EditorTool.TERRAIN_PAINT:
                self._handle_terrain_paint(event.pos)
            elif self.dragging and self.current_tool == EditorTool.PAN:
                self._handle_pan_drag(event.pos)
        
        return None
    
    def _handle_left_click(self, pos: Tuple[int, int]):
        """Handle left mouse click"""
        # Check if click is in tool panel
        if pos[0] < self.tool_panel_width:
            self._handle_panel_click(pos)
            return
        
        # Handle map interaction based on current tool
        if self.current_tool == EditorTool.TERRAIN_PAINT:
            self._handle_terrain_paint(pos)
        elif self.current_tool == EditorTool.CITY_PLACE:
            self._handle_city_place(pos)
        elif self.current_tool == EditorTool.CITY_REMOVE:
            self._handle_city_remove(pos)
        elif self.current_tool == EditorTool.CITY_EDIT:
            self._handle_city_edit(pos)
        elif self.current_tool == EditorTool.PAN:
            self.dragging = True
            self.drag_start = pos
    
    def _handle_right_click(self, pos: Tuple[int, int]):
        """Handle right mouse click"""
        # Right click always pans
        self.dragging = True
        self.drag_start = pos
    
    def _handle_panel_click(self, pos: Tuple[int, int]):
        """Handle clicks in the tool panel"""
        # Check tool buttons
        for tool, data in self.tool_buttons.items():
            if data['rect'].collidepoint(pos):
                self.current_tool = tool
                return
        
        # Check terrain buttons
        for terrain, data in self.terrain_buttons.items():
            if data['rect'].collidepoint(pos):
                self.selected_terrain = terrain
                return
        
        # Check country buttons
        for country, data in self.country_buttons.items():
            if data['rect'].collidepoint(pos):
                self.selected_country = country
                return
    
    def _handle_terrain_paint(self, pos: Tuple[int, int]):
        """Paint terrain at mouse position"""
        if pos[0] < self.tool_panel_width:
            return
        
        # Convert screen pos to hex coordinate
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        if hex_pos:
            # Check bounds
            if 0 <= hex_pos.q < self.campaign_state.map_width and 0 <= hex_pos.r < self.campaign_state.map_height:
                # Paint terrain
                old_terrain = self.campaign_state.terrain_map.get((hex_pos.q, hex_pos.r))
                if old_terrain != self.selected_terrain:
                    self.campaign_state.terrain_map[(hex_pos.q, hex_pos.r)] = self.selected_terrain
    
    def _handle_city_place(self, pos: Tuple[int, int]):
        """Place a city at mouse position"""
        if pos[0] < self.tool_panel_width:
            return
        
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        if hex_pos:
            # Check if city already exists at this position
            for city in self.campaign_state.cities.values():
                if city.position == hex_pos:
                    return  # City already exists here
            
            # Create new city
            city_id = f"city_{len(self.campaign_state.cities)}"
            new_city = City(
                name=f"New City {len(self.campaign_state.cities)}",
                country=self.selected_country,
                position=hex_pos,
                city_type="city",
                income=100,
                castle_level=1,
                population=10000,
                specialization="trade",
                description="A newly founded city"
            )
            
            self.campaign_state.cities[city_id] = new_city
            self._save_state()
    
    def _handle_city_remove(self, pos: Tuple[int, int]):
        """Remove city at mouse position"""
        if pos[0] < self.tool_panel_width:
            return
        
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        if hex_pos:
            # Find city at this position
            city_to_remove = None
            for city_id, city in self.campaign_state.cities.items():
                if city.position == hex_pos:
                    city_to_remove = city_id
                    break
            
            if city_to_remove:
                del self.campaign_state.cities[city_to_remove]
                self._save_state()
    
    def _handle_city_edit(self, pos: Tuple[int, int]):
        """Edit city at mouse position"""
        if pos[0] < self.tool_panel_width:
            return
        
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        if hex_pos:
            # Find city at this position
            for city_id, city in self.campaign_state.cities.items():
                if city.position == hex_pos:
                    # Open city edit dialog
                    self.city_edit_dialog = CityEditDialog(self.screen, city, city_id)
                    break
    
    def _handle_pan_drag(self, pos: Tuple[int, int]):
        """Handle camera panning"""
        if self.drag_start:
            dx = pos[0] - self.drag_start[0]
            dy = pos[1] - self.drag_start[1]
            self.renderer.camera_x += dx
            self.renderer.camera_y += dy
            self.drag_start = pos
    
    def _save_state(self):
        """Save current state for undo"""
        state = {
            'terrain_map': dict(self.campaign_state.terrain_map),
            'cities': {k: {
                'name': v.name,
                'country': v.country,
                'position': (v.position.q, v.position.r),
                'city_type': v.city_type,
                'income': v.income,
                'castle_level': v.castle_level,
                'population': v.population,
                'specialization': v.specialization,
                'description': v.description
            } for k, v in self.campaign_state.cities.items()}
        }
        
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
    
    def _undo(self):
        """Undo last action"""
        if len(self.undo_stack) > 1:  # Keep at least one state
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            
            # Restore previous state
            self._restore_state(self.undo_stack[-1])
    
    def _redo(self):
        """Redo last undone action"""
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self._restore_state(state)
    
    def _restore_state(self, state: Dict):
        """Restore editor state"""
        # Restore terrain
        self.campaign_state.terrain_map.clear()
        for (q, r), terrain in state['terrain_map'].items():
            self.campaign_state.terrain_map[(q, r)] = terrain
        
        # Restore cities
        self.campaign_state.cities.clear()
        for city_id, city_data in state['cities'].items():
            q, r = city_data['position']
            city = City(
                name=city_data['name'],
                country=city_data['country'],
                position=HexCoord(q, r),
                city_type=city_data['city_type'],
                income=city_data['income'],
                castle_level=city_data['castle_level'],
                population=city_data['population'],
                specialization=city_data['specialization'],
                description=city_data['description']
            )
            self.campaign_state.cities[city_id] = city
    
    def _save_map(self):
        """Save current map to JSON file"""
        try:
            # Prepare data for export
            export_data = {
                "map": {
                    "width": self.campaign_state.map_width,
                    "height": self.campaign_state.map_height,
                    "terrain": {}
                },
                "countries": {},
                "cities": {},
                "neutral_regions": []
            }
            
            # Group terrain by type
            terrain_groups = {}
            for (q, r), terrain in self.campaign_state.terrain_map.items():
                terrain_name = terrain.name.lower()
                if terrain_name not in terrain_groups:
                    terrain_groups[terrain_name] = []
                terrain_groups[terrain_name].append((q, r))
            
            # Convert terrain to regions (simplified - just individual hexes for now)
            for terrain_name, coords in terrain_groups.items():
                export_data["map"]["terrain"][terrain_name] = []
                for q, r in coords:
                    export_data["map"]["terrain"][terrain_name].append([q, q+1, r, r+1])
            
            # Export countries (copy existing)
            export_data["countries"] = {k: {
                'name': v.name,
                'color': list(v.color),
                'capital': v.capital,
                'description': v.description,
                'starting_resources': v.starting_resources,
                'bonuses': v.bonuses
            } for k, v in self.campaign_state.countries.items()}
            
            # Export cities
            export_data["cities"] = {k: {
                'name': v.name,
                'country': v.country,
                'position': [v.position.q, v.position.r],
                'type': v.city_type,
                'income': v.income,
                'castle_level': v.castle_level,
                'population': v.population,
                'specialization': v.specialization,
                'description': v.description
            } for k, v in self.campaign_state.cities.items()}
            
            # Save to file
            map_file = os.path.join(os.path.dirname(__file__), '..', 'campaign', 'medieval_europe.json')
            with open(map_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print("Map saved successfully!")
            
        except Exception as e:
            print(f"Failed to save map: {e}")
    
    def draw(self):
        """Draw the map editor"""
        if not self.visible:
            return
        
        # Clear screen
        self.screen.fill((20, 20, 20))
        
        # Draw map area
        if self.campaign_state and self.renderer:
            self.renderer.render(self.campaign_state)
        
        # Draw tool panel
        self._draw_tool_panel()
        
        # Draw cursor info
        self._draw_cursor_info()
        
        # Draw city edit dialog on top
        if self.city_edit_dialog:
            self.city_edit_dialog.draw()
    
    def _draw_tool_panel(self):
        """Draw the tool panel"""
        # Panel background
        panel_rect = pygame.Rect(0, 0, self.tool_panel_width, self.screen.get_height())
        pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, self.colors['panel_border'], panel_rect, 2)
        
        # Title
        title_surface = self.title_font.render("Map Editor", True, self.colors['text'])
        self.screen.blit(title_surface, (10, 10))
        
        # Tool buttons
        self._draw_section_title("Tools", 45)
        for tool, data in self.tool_buttons.items():
            color = self.colors['button_selected'] if tool == self.current_tool else self.colors['button']
            if data['rect'].collidepoint(self.mouse_pos):
                color = self.colors['button_hover']
            
            pygame.draw.rect(self.screen, color, data['rect'])
            pygame.draw.rect(self.screen, self.colors['panel_border'], data['rect'], 1)
            
            text_surface = self.font.render(data['label'], True, self.colors['text'])
            text_rect = text_surface.get_rect(center=data['rect'].center)
            self.screen.blit(text_surface, text_rect)
        
        # Terrain selection
        if self.current_tool == EditorTool.TERRAIN_PAINT:
            self._draw_section_title("Terrain", 245)
            for terrain, data in self.terrain_buttons.items():
                color = self.colors['button_selected'] if terrain == self.selected_terrain else self.colors['button']
                if data['rect'].collidepoint(self.mouse_pos):
                    color = self.colors['button_hover']
                
                pygame.draw.rect(self.screen, color, data['rect'])
                pygame.draw.rect(self.screen, self.colors['panel_border'], data['rect'], 1)
                
                text_surface = self.font.render(data['label'], True, self.colors['text'])
                text_rect = text_surface.get_rect(center=data['rect'].center)
                self.screen.blit(text_surface, text_rect)
        
        # Country selection
        if self.current_tool in [EditorTool.CITY_PLACE, EditorTool.CITY_EDIT]:
            self._draw_section_title("Country", 445)
            for country, data in self.country_buttons.items():
                color = self.colors['button_selected'] if country == self.selected_country else self.colors['button']
                if data['rect'].collidepoint(self.mouse_pos):
                    color = self.colors['button_hover']
                
                pygame.draw.rect(self.screen, color, data['rect'])
                pygame.draw.rect(self.screen, self.colors['panel_border'], data['rect'], 1)
                
                text_surface = self.font.render(data['label'], True, self.colors['text'])
                text_rect = text_surface.get_rect(center=data['rect'].center)
                self.screen.blit(text_surface, text_rect)
        
        # Instructions
        instructions = [
            "Controls:",
            "Left Click - Use Tool",
            "Right Click - Pan",
            "Ctrl+S - Save Map",
            "Ctrl+Z - Undo",
            "Ctrl+Shift+Z - Redo",
            "ESC - Exit Editor"
        ]
        
        y_offset = self.screen.get_height() - len(instructions) * 20 - 10
        for instruction in instructions:
            color = self.colors['text'] if instruction.endswith(':') else self.colors['text_dim']
            text_surface = self.font.render(instruction, True, color)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20
    
    def _draw_section_title(self, title: str, y: int):
        """Draw a section title"""
        text_surface = self.font.render(title + ":", True, self.colors['text'])
        self.screen.blit(text_surface, (10, y))
    
    def _draw_cursor_info(self):
        """Draw information about what's under the cursor"""
        if self.mouse_pos[0] >= self.tool_panel_width and self.campaign_state:
            hex_pos = self.renderer.screen_to_hex(self.mouse_pos, self.campaign_state.hex_layout)
            if hex_pos:
                info_lines = [f"Hex: ({hex_pos.q}, {hex_pos.r})"]
                
                # Show terrain type
                terrain = self.campaign_state.terrain_map.get((hex_pos.q, hex_pos.r))
                if terrain:
                    info_lines.append(f"Terrain: {terrain.name.title()}")
                
                # Show city if present
                for city in self.campaign_state.cities.values():
                    if city.position == hex_pos:
                        info_lines.append(f"City: {city.name} ({city.country})")
                        break
                
                # Draw info box
                if info_lines:
                    max_width = max(self.font.size(line)[0] for line in info_lines)
                    info_rect = pygame.Rect(
                        self.mouse_pos[0] + 10,
                        self.mouse_pos[1] - len(info_lines) * 20 - 10,
                        max_width + 20,
                        len(info_lines) * 20 + 10
                    )
                    
                    pygame.draw.rect(self.screen, self.colors['panel_bg'], info_rect)
                    pygame.draw.rect(self.screen, self.colors['panel_border'], info_rect, 1)
                    
                    for i, line in enumerate(info_lines):
                        text_surface = self.font.render(line, True, self.colors['text'])
                        self.screen.blit(text_surface, (info_rect.x + 10, info_rect.y + 5 + i * 20))