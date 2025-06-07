#!/usr/bin/env python3
"""
Test script to visualize the campaign hex grid positioning
"""
import pygame
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.campaign.campaign_state import CampaignState
from game.campaign.campaign_renderer import CampaignRenderer

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 800))
    pygame.display.set_caption("Campaign Hex Grid Test")
    clock = pygame.time.Clock()
    
    # Create campaign state and renderer
    campaign_state = CampaignState()
    campaign_renderer = CampaignRenderer(screen)
    
    # Set a specific camera position to see a small area clearly
    campaign_renderer.camera_x = -500  # Show hexes starting around (10, 10)
    campaign_renderer.camera_y = -300
    campaign_renderer.initial_camera_set = True
    
    print(f"Camera position: ({campaign_renderer.camera_x}, {campaign_renderer.camera_y})")
    print(f"Hex layout: size={campaign_state.hex_layout.hex_size}, col_spacing={campaign_state.hex_layout.col_spacing:.1f}, row_spacing={campaign_state.hex_layout.row_spacing:.1f}")
    
    running = True
    show_grid = True
    show_coords = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                    print(f"Grid display: {show_grid}")
                elif event.key == pygame.K_c:
                    show_coords = not show_coords
                    print(f"Coordinate display: {show_coords}")
                elif event.key == pygame.K_LEFT:
                    campaign_renderer.camera_x += 50
                elif event.key == pygame.K_RIGHT:
                    campaign_renderer.camera_x -= 50
                elif event.key == pygame.K_UP:
                    campaign_renderer.camera_y += 50
                elif event.key == pygame.K_DOWN:
                    campaign_renderer.camera_y -= 50
        
        # Clear screen
        screen.fill((50, 50, 50))
        
        if show_grid:
            # Draw a limited hex grid for testing
            hex_layout = campaign_state.hex_layout
            
            # Calculate a small visible range for testing
            start_col = 8
            end_col = 18
            start_row = 8
            end_row = 15
            
            for col in range(start_col, end_col):
                for row in range(start_row, end_row):
                    # Get pixel position
                    pixel_x, pixel_y = hex_layout.hex_to_pixel(col, row)
                    screen_x = pixel_x + campaign_renderer.camera_x
                    screen_y = pixel_y + campaign_renderer.camera_y
                    
                    # Get hex corners using campaign renderer method
                    corners = campaign_renderer._get_hex_corners_cached(screen_x, screen_y, hex_layout.hex_size)
                    
                    # Color based on row parity to show offset pattern
                    if row % 2 == 0:
                        color = (100, 150, 100)  # Green for even rows
                    else:
                        color = (100, 100, 150)  # Blue for odd rows
                    
                    # Draw filled hex
                    pygame.draw.polygon(screen, color, corners)
                    pygame.draw.polygon(screen, (255, 255, 255), corners, 1)
                    
                    # Draw coordinates if enabled
                    if show_coords:
                        font = pygame.font.Font(None, 16)
                        coord_text = font.render(f"{col},{row}", True, (255, 255, 255))
                        text_rect = coord_text.get_rect(center=(int(screen_x), int(screen_y)))
                        screen.blit(coord_text, text_rect)
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        instructions = [
            "Arrow keys: Move camera",
            "G: Toggle grid",
            "C: Toggle coordinates",
            "ESC: Exit",
            f"Camera: ({campaign_renderer.camera_x}, {campaign_renderer.camera_y})"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, (255, 255, 255))
            screen.blit(text, (10, 10 + i * 25))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()