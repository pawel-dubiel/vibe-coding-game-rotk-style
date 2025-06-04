#!/usr/bin/env python3
"""
Visual test to verify hex visibility fix when zooming.
This demonstrates that hexes are properly rendered at all zoom levels.
"""

import pygame
import sys
from game.game_state import GameState
from game.rendering.core_renderer import CoreRenderer
from game.input_handler import InputHandler

def draw_debug_info(screen, game_state, renderer):
    """Draw debug information about visible hexes"""
    font = pygame.font.Font(None, 24)
    
    # Get current zoom and camera info
    zoom = game_state.camera_manager.zoom_level
    cam_x = game_state.camera_manager.camera_x
    cam_y = game_state.camera_manager.camera_y
    
    # Calculate visible hex range using the same logic as terrain renderer
    if hasattr(renderer, 'terrain_renderer'):
        hex_layout = renderer.terrain_renderer.hex_layout
        screen_width = game_state.camera_manager.screen_width
        screen_height = game_state.camera_manager.screen_height
        
        # Use unscaled hex dimensions (the fix)
        base_hex_width = hex_layout.col_spacing / zoom
        base_hex_height = hex_layout.row_spacing / zoom
        
        start_col = max(0, int(cam_x / base_hex_width) - 1)
        end_col = min(game_state.board_width, int((cam_x + screen_width / zoom) / base_hex_width) + 2)
        start_row = max(0, int(cam_y / base_hex_height) - 1)
        end_row = min(game_state.board_height, int((cam_y + screen_height / zoom) / base_hex_height) + 2)
        
        visible_cols = end_col - start_col
        visible_rows = end_row - start_row
        
        # Draw debug text
        debug_lines = [
            f"Zoom: {zoom:.2f}",
            f"Camera: ({cam_x:.0f}, {cam_y:.0f})",
            f"Hex Size: {hex_layout.hex_size}",
            f"Visible Cols: {start_col}-{end_col} ({visible_cols} total)",
            f"Visible Rows: {start_row}-{end_row} ({visible_rows} total)",
            "",
            "Controls:",
            "Mouse wheel or +/-: Zoom",
            "Arrow keys: Move camera",
            "ESC: Exit"
        ]
        
        y_offset = 10
        for line in debug_lines:
            text = font.render(line, True, (255, 255, 255))
            shadow = font.render(line, True, (0, 0, 0))
            screen.blit(shadow, (12, y_offset + 2))
            screen.blit(text, (10, y_offset))
            y_offset += 25

def test_hex_visibility():
    """Test hex visibility at different zoom levels"""
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Hex Visibility Fix Test")
    
    # Create a test game with a grid
    battle_config = {
        'board_size': (30, 20),  # Large board to test edge cases
        'knights': 0,
        'castles': 0
    }
    
    game_state = GameState(battle_config, vs_ai=False)
    renderer = CoreRenderer(screen)
    input_handler = InputHandler()
    
    # Connect renderer to game state for zoom consistency
    game_state.renderer = renderer
    renderer.input_handler = input_handler
    
    # Start with camera at center
    game_state.camera_manager.set_camera_position(500, 300)
    
    clock = pygame.time.Clock()
    running = True
    
    print("Hex Visibility Fix Test")
    print("======================")
    print("This test verifies that hexes are properly rendered at all zoom levels.")
    print("Before the fix, zooming in/out would cause hexes at screen edges to disappear.")
    print("")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # Let input handler process all events
            input_handler.handle_event(event, game_state)
        
        # Update game state
        game_state.update(clock.tick(60) / 1000.0)
        
        # Render the game
        renderer.render(game_state)
        
        # Draw debug overlay
        draw_debug_info(screen, game_state, renderer)
        
        pygame.display.flip()
    
    pygame.quit()
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_hex_visibility()