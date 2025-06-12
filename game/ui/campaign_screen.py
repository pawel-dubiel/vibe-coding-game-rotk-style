import pygame
from typing import Optional, Tuple
from game.campaign.campaign_state import CampaignState, Army
from game.campaign.campaign_renderer import CampaignRenderer
from game.hex_utils import HexCoord
from game.ui.campaign_context_menu import CampaignContextMenu
from game.ui.city_info_modal import CityInfoModal
from game.ui.army_info_modal import ArmyInfoModal


class CampaignScreen:
    """Main campaign mode screen"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.campaign_state = None  # Will be set externally or default
        self.renderer = CampaignRenderer(screen)
        self.visible = True
        self.ready_for_battle = False
        self.battle_armies = None  # Will store armies involved in battle
        
        # Mouse tracking
        self.mouse_pos = (0, 0)
        self.dragging = False
        self.drag_start = None
        
        # AI turn processing
        self.ai_turn_timer = 0
        self.ai_turn_delay = 1.0  # 1 second delay for AI turns
        
        # UI elements
        self.context_menu = CampaignContextMenu()
        self.city_info_modal = CityInfoModal()
        self.army_info_modal = ArmyInfoModal()
        
        # Selection state
        self.selected_hex = None  # Currently selected hex
        self.selected_city = None  # City at selected hex
        self.selected_army = None  # Army at selected hex
        self.selection_focus = 'army'  # 'army' or 'city' - which to prioritize when both present
    
    def _ensure_campaign_state(self):
        """Ensure campaign state is initialized"""
        if self.campaign_state is None:
            self.campaign_state = CampaignState()
        
    def handle_event(self, event: pygame.event.Event) -> Optional[dict]:
        """Handle campaign screen events"""
        if not self.visible:
            return None
        self._ensure_campaign_state()
        
        # Handle modals events first
        if self.city_info_modal.handle_event(event):
            return None
        if self.army_info_modal.handle_event(event):
            return None
            
        # Handle context menu events
        if self.context_menu.visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Store the target before handling click (in case menu gets hidden)
                target_city = self.context_menu.target_city
                target_army = self.context_menu.target_army
                
                action = self.context_menu.handle_click(event.pos[0], event.pos[1])
                if action:
                    # Restore targets if they were cleared by hide()
                    if not self.context_menu.target_city and target_city:
                        self.context_menu.target_city = target_city
                    if not self.context_menu.target_army and target_army:
                        self.context_menu.target_army = target_army
                    
                    self._handle_context_action(action)
                    return None
                elif action is None and self.context_menu.visible == False:
                    # Menu was closed by clicking outside
                    return None
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_left_click(event.pos)
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.drag_start = None
                
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            if self.dragging and self.drag_start:
                # Camera panning
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                self.renderer.camera_x += dx
                self.renderer.camera_y += dy
                self.drag_start = event.pos
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to main menu
                return {'action': 'back_to_menu'}
            elif event.key == pygame.K_SPACE:
                # End turn - only if it's player's turn
                if self.campaign_state.current_country == self.campaign_state.player_country:
                    self.campaign_state.end_turn()
                    self.ai_turn_timer = self.ai_turn_delay
            elif event.key == pygame.K_TAB:
                # Switch between city and army selection when both present
                if self.selected_city and self.selected_army:
                    self.selection_focus = 'city' if self.selection_focus == 'army' else 'army'
                    # Update campaign state army selection based on focus
                    if self.selection_focus == 'army' and self.selected_army[1].country == self.campaign_state.current_country:
                        self.campaign_state.selected_army = self.selected_army[0]
                    else:
                        self.campaign_state.selected_army = None
                
        return None
        
    def _handle_left_click(self, pos: Tuple[int, int]):
        """Handle left mouse click"""
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        
        # Store selected hex
        self.selected_hex = hex_pos
        
        # Check what's at this hex
        city_at_hex = None
        army_at_hex = None
        
        # Find city at hex
        for city_id, city in self.campaign_state.cities.items():
            if city.position == hex_pos:
                city_at_hex = city
                break
                
        # Find army at hex
        for army_id, army in self.campaign_state.armies.items():
            if army.position == hex_pos:
                army_at_hex = (army_id, army)
                break
        
        # Update selection state
        self.selected_city = city_at_hex
        self.selected_army = army_at_hex
        
        # If army exists and belongs to player, select it for movement
        if army_at_hex and army_at_hex[1].country == self.campaign_state.current_country:
            self.campaign_state.selected_army = army_at_hex[0]
        else:
            self.campaign_state.selected_army = None
            # Start camera dragging if nothing selected
            if not city_at_hex and not army_at_hex:
                self.dragging = True
                self.drag_start = pos
            
    def _handle_right_click(self, pos: Tuple[int, int]):
        """Handle right mouse click - show context menu based on selection or move army"""
        if not self.campaign_state or not self.campaign_state.hex_layout:
            return
            
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        
        # If clicking on the selected hex, show context menu based on what's selected
        if self.selected_hex and hex_pos == self.selected_hex:
            if self.selected_army and self.selected_city:
                # Both army and city present - show menu based on selection focus
                if self.selection_focus == 'army':
                    self.context_menu.show_for_army(pos[0], pos[1], self.selected_army[1], self.campaign_state, has_city=True)
                    # Store city for switching
                    self.context_menu.target_city = self.selected_city
                else:
                    self.context_menu.show_for_city(pos[0], pos[1], self.selected_city, self.campaign_state, has_army=True)
                    # Store army for switching
                    self.context_menu.target_army = self.selected_army[1]
            elif self.selected_army:
                # Only army present
                self.context_menu.show_for_army(pos[0], pos[1], self.selected_army[1], self.campaign_state)
            elif self.selected_city:
                # Only city present
                self.context_menu.show_for_city(pos[0], pos[1], self.selected_city, self.campaign_state)
        else:
            # Right-clicking elsewhere - check what's at that position
            city_at_pos = None
            army_at_pos = None
            
            for city_id, city in self.campaign_state.cities.items():
                if city.position == hex_pos:
                    city_at_pos = city
                    break
            
            for army in self.campaign_state.armies.values():
                if army.position == hex_pos:
                    army_at_pos = army
                    break
            
            if city_at_pos or army_at_pos:
                # Show context menu for what's at the clicked position
                if army_at_pos and city_at_pos:
                    # Both army and city present - show army menu with city option
                    self.context_menu.show_for_army(pos[0], pos[1], army_at_pos, self.campaign_state, has_city=True)
                    # Also store the city for switching
                    self.context_menu.target_city = city_at_pos
                elif army_at_pos:
                    self.context_menu.show_for_army(pos[0], pos[1], army_at_pos, self.campaign_state, has_city=False)
                else:
                    self.context_menu.show_for_city(pos[0], pos[1], city_at_pos, self.campaign_state, has_army=False)
            else:
                # No city or army - try to move selected army
                if not self.campaign_state.selected_army:
                    return
                    
                army = self.campaign_state.armies.get(self.campaign_state.selected_army)
                if not army or army.country != self.campaign_state.current_country:
                    return
                
                # Try to move the army
                if self.campaign_state.move_army(self.campaign_state.selected_army, hex_pos):
                    # Update our selection tracking
                    self.selected_hex = hex_pos
                    self.selected_army = (self.campaign_state.selected_army, army)
                    self.selected_city = None
                    
                    # Check for city at new position
                    for city_id, city in self.campaign_state.cities.items():
                        if city.position == hex_pos:
                            self.selected_city = city
                            break
                    
                    # Check if we're at an enemy territory/army
                    enemy_army = self._get_enemy_army_at_position(hex_pos)
                    if enemy_army:
                        # Trigger battle
                        self.ready_for_battle = True
                        self.battle_armies = {
                            'attacker': army,
                            'defender': enemy_army
                        }
                
    def _get_enemy_army_at_position(self, hex_pos: HexCoord) -> Optional[Army]:
        """Check if there's an enemy army at the given hex position"""
        for army in self.campaign_state.armies.values():
            if (army.country != self.campaign_state.current_country and
                army.position == hex_pos):
                return army
        return None
    
    def _handle_context_action(self, action: str):
        """Handle action selected from context menu"""
        if action == 'show_info':
            if self.context_menu.target_city:
                # Get country for this city
                country = self.campaign_state.countries.get(self.context_menu.target_city.country)
                
                if country:
                    self.city_info_modal.show(
                        self.context_menu.target_city,
                        country,
                        self.screen.get_size()
                    )
                else:
                    # Create a fallback country if not found
                    from game.campaign.campaign_state import Country
                    fallback_country = Country(
                        id=self.context_menu.target_city.country,
                        name=self.context_menu.target_city.country.title(),
                        color=(128, 128, 128),
                        capital=self.context_menu.target_city.name,
                        description=f"Unknown country: {self.context_menu.target_city.country}",
                        starting_resources={},
                        bonuses={}
                    )
                    self.city_info_modal.show(
                        self.context_menu.target_city,
                        fallback_country,
                        self.screen.get_size()
                    )
            elif self.context_menu.target_army:
                # Show army info modal
                country = self.campaign_state.countries.get(self.context_menu.target_army.country)
                if country:
                    self.army_info_modal.show(
                        self.context_menu.target_army,
                        country,
                        self.screen.get_size()
                    )
                
        elif action == 'select_army':
            if self.context_menu.target_army:
                # Find army ID
                for army_id, army in self.campaign_state.armies.items():
                    if army == self.context_menu.target_army:
                        self.campaign_state.selected_army = army_id
                        break
                        
        elif action == 'switch_to_army':
            # Switch focus to army and show army info
            self.selection_focus = 'army'
            if self.selected_army and self.selected_army[1].country == self.campaign_state.current_country:
                self.campaign_state.selected_army = self.selected_army[0]
            
            # If we have a target army, show its info
            if self.context_menu.target_army:
                country = self.campaign_state.countries.get(self.context_menu.target_army.country)
                if country:
                    self.army_info_modal.show(
                        self.context_menu.target_army,
                        country,
                        self.screen.get_size()
                    )
                
        elif action == 'switch_to_city':
            # Switch focus to city and show city info
            self.selection_focus = 'city'
            self.campaign_state.selected_army = None
            
            # If we have a target city, show its info
            if self.context_menu.target_city:
                country = self.campaign_state.countries.get(self.context_menu.target_city.country)
                if country:
                    self.city_info_modal.show(
                        self.context_menu.target_city,
                        country,
                        self.screen.get_size()
                    )
                else:
                    # Create a fallback country if not found
                    from game.campaign.campaign_state import Country
                    fallback_country = Country(
                        id=self.context_menu.target_city.country,
                        name=self.context_menu.target_city.country.title(),
                        color=(128, 128, 128),
                        capital=self.context_menu.target_city.name,
                        description=f"Unknown country: {self.context_menu.target_city.country}",
                        starting_resources={},
                        bonuses={}
                    )
                    self.city_info_modal.show(
                        self.context_menu.target_city,
                        fallback_country,
                        self.screen.get_size()
                    )
                
        elif action == 'recruit':
            if self.context_menu.target_city:
                # Find city id
                city_id = None
                for cid, city in self.campaign_state.cities.items():
                    if city.name == self.context_menu.target_city.name:
                        city_id = cid
                        break
                        
                if city_id is not None:
                    # Basic recruitment - 5 knights, 3 archers, 2 cavalry
                    units = {'knights': 5, 'archers': 3, 'cavalry': 2}
                    # Create new army at city position
                    import uuid
                    new_army_id = str(uuid.uuid4())[:8]
                    new_army = Army(
                        id=new_army_id,
                        country=self.campaign_state.current_country,
                        position=self.context_menu.target_city.position,
                        knights=units['knights'],
                        archers=units['archers'],
                        cavalry=units['cavalry'],
                        movement_points=3
                    )
                    self.campaign_state.armies[new_army_id] = new_army
                    # Deduct cost from treasury
                    if self.campaign_state.current_country in self.campaign_state.country_treasury:
                        self.campaign_state.country_treasury[self.campaign_state.current_country] -= 100
        
    def update(self, dt: float):
        """Update campaign screen state"""
        if not self.visible:
            return
        self._ensure_campaign_state()
            
        # Process AI turns
        if self.campaign_state.current_country != self.campaign_state.player_country:
            self.ai_turn_timer -= dt
            if self.ai_turn_timer <= 0:
                # Simple AI: move armies randomly for now
                self._process_ai_turn()
                self.campaign_state.end_turn()
                self.ai_turn_timer = self.ai_turn_delay
                
    def _process_ai_turn(self):
        """Process AI country turn"""
        # For now, AI doesn't move - just processes the turn
        # In future, add AI movement logic here
        pass
        
    def draw(self):
        """Draw the campaign screen"""
        self._ensure_campaign_state()
        if not self.visible:
            return
            
        # Render the campaign map
        self.renderer.render(self.campaign_state)
        
        # Handle continuous camera movement with arrow keys
        keys = pygame.key.get_pressed()
        self.renderer.handle_camera_movement(keys)
        
        # Show AI turn indicator
        if self.campaign_state.current_country != self.campaign_state.player_country:
            self._draw_ai_turn_indicator()
            
        # Draw context menu
        self.context_menu.render(self.screen)
        
        # Draw city info modal
        self.city_info_modal.draw(self.screen)
        
        # Draw army info modal
        self.army_info_modal.draw(self.screen)
        
        # Draw selection indicator if both city and army are present at selected hex
        if self.selected_city and self.selected_army:
            self._draw_selection_indicator()
    
    def _draw_ai_turn_indicator(self):
        """Draw indicator that AI is taking its turn"""
        font = pygame.font.Font(None, 48)
        current_country_obj = self.campaign_state.countries.get(self.campaign_state.current_country, None)
        country_name = current_country_obj.name if current_country_obj else self.campaign_state.current_country.title()
        text = f"{country_name} is thinking..."
        text_surface = font.render(text, True, (255, 255, 0))
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        
        # Draw semi-transparent background
        padding = 20
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, bg_rect)
        
        self.screen.blit(text_surface, text_rect)
    
    def _draw_selection_indicator(self):
        """Draw indicator showing which entity is selected when both city and army are present"""
        font = pygame.font.Font(None, 24)
        text_color = (255, 255, 255)
        highlight_color = (255, 255, 0)
        
        # Position at top-right corner
        x = self.screen.get_width() - 250
        y = 10
        width = 240
        height = 80
        
        # Draw background
        bg_surface = pygame.Surface((width, height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, (x, y))
        
        # Draw border
        pygame.draw.rect(self.screen, (100, 100, 100), (x, y, width, height), 2)
        
        # Draw title
        title_text = font.render("Selection (TAB to switch):", True, text_color)
        self.screen.blit(title_text, (x + 10, y + 10))
        
        # Draw city option
        city_color = highlight_color if self.selection_focus == 'city' else text_color
        city_text = font.render(f"City: {self.selected_city.name}", True, city_color)
        self.screen.blit(city_text, (x + 20, y + 35))
        
        # Draw army option
        army_color = highlight_color if self.selection_focus == 'army' else text_color
        army_text = font.render(f"Army: {self.selected_army[0]}", True, army_color)
        self.screen.blit(army_text, (x + 20, y + 55))
        
    def show(self):
        """Show the campaign screen"""
        self.visible = True
        
    def hide(self):
        """Hide the campaign screen"""
        self.visible = False
        
    def get_battle_config(self) -> Optional[dict]:
        self._ensure_campaign_state()
        """Get configuration for battle when armies meet"""
        if not self.ready_for_battle or not self.battle_armies:
            return None
            
        attacker = self.battle_armies['attacker']
        defender = self.battle_armies['defender']
        
        # Create battle configuration
        # Total units for simplified placement
        total_attacker_units = attacker.knights + attacker.archers + attacker.cavalry
        total_defender_units = defender.knights + defender.archers + defender.cavalry
        
        config = {
            'board_size': (20, 20),
            'knights': max(total_attacker_units, total_defender_units),  # Set to max for placement
            'castles': 0,
            'campaign_battle': True,  # Flag to indicate this is from campaign
            'attacker_country': attacker.country,
            'defender_country': defender.country,
            'attacker_army': attacker,
            'defender_army': defender
        }
        
        return config