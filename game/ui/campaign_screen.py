import pygame
from typing import Optional, Tuple
from game.campaign.campaign_state import CampaignState, Army
from game.campaign.campaign_renderer import CampaignRenderer
from game.hex_utils import HexCoord


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
    
    def _ensure_campaign_state(self):
        """Ensure campaign state is initialized"""
        if self.campaign_state is None:
            self.campaign_state = CampaignState()
        
    def handle_event(self, event: pygame.event.Event) -> Optional[dict]:
        """Handle campaign screen events"""
        if not self.visible:
            return None
        self._ensure_campaign_state()
            
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
                
        return None
        
    def _handle_left_click(self, pos: Tuple[int, int]):
        """Handle left mouse click"""
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        
        # Check if clicking on an army
        clicked_army = None
        for army_id, army in self.campaign_state.armies.items():
            if army.position == hex_pos:
                if army.country == self.campaign_state.current_country:
                    clicked_army = army_id
                break
                
        if clicked_army:
            self.campaign_state.selected_army = clicked_army
        else:
            # Check for camera dragging
            self.dragging = True
            self.drag_start = pos
            
    def _handle_right_click(self, pos: Tuple[int, int]):
        """Handle right mouse click - move selected army"""
        if not self.campaign_state.selected_army:
            return
            
        army = self.campaign_state.armies.get(self.campaign_state.selected_army)
        if not army or army.country != self.campaign_state.current_country:
            return
            
        hex_pos = self.renderer.screen_to_hex(pos, self.campaign_state.hex_layout)
        
        # Try to move the army
        if self.campaign_state.move_army(self.campaign_state.selected_army, hex_pos):
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
        current_country = self.campaign_state.current_country
        country_armies = self.campaign_state.get_country_armies(current_country)
        
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