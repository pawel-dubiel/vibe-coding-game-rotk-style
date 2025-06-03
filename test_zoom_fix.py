#!/usr/bin/env python3
"""
Quick test to verify zoom and hex alignment fixes.
"""

import pygame
import sys
from game.game_state import GameState
from game.rendering import CoreRenderer
from game.input_handler import InputHandler

def test_zoom_functionality():
    """Test that zoom works correctly without alignment issues."""
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Zoom Test")
    
    # Create a small game for testing
    battle_config = {
        'board_size': (10, 10),
        'knights': 2,
        'castles': 1
    }
    
    game_state = GameState(battle_config, vs_ai=False)
    renderer = CoreRenderer(screen)
    input_handler = InputHandler()
    
    # Connect renderer to game state for zoom consistency
    game_state.renderer = renderer
    renderer.input_handler = input_handler
    
    clock = pygame.time.Clock()
    
    print("Zoom test started. Controls:")
    print("- Mouse wheel: Zoom in/out")
    print("- +/-: Zoom in/out (keyboard)")
    print("- Arrow keys: Move camera")
    print("- ESC: Exit")
    print("\nCurrent zoom level: 1.0")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    old_zoom = getattr(game_state.camera_manager, 'zoom_level', 1.0)
                    input_handler.handle_event(event, game_state)
                    new_zoom = getattr(game_state.camera_manager, 'zoom_level', 1.0)
                    if abs(old_zoom - new_zoom) > 0.01:
                        print(f"Zoom level: {new_zoom:.2f}")
            elif event.type == pygame.MOUSEWHEEL:
                old_zoom = getattr(game_state.camera_manager, 'zoom_level', 1.0)
                input_handler.handle_event(event, game_state)
                new_zoom = getattr(game_state.camera_manager, 'zoom_level', 1.0)
                if abs(old_zoom - new_zoom) > 0.01:
                    print(f"Zoom level: {new_zoom:.2f}")
            else:
                input_handler.handle_event(event, game_state)
        
        # Update and render
        game_state.update(clock.tick(60) / 1000.0)
        renderer.render(game_state)
        
        # Display debug info
        font = pygame.font.Font(None, 24)
        zoom_level = getattr(game_state.camera_manager, 'zoom_level', 1.0)
        hex_size = getattr(input_handler.hex_layout, 'hex_size', 36)
        info_text = f"Zoom: {zoom_level:.2f} | Hex Size: {hex_size}"
        text_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()
    print("Zoom test completed successfully!")

if __name__ == "__main__":
    test_zoom_functionality()