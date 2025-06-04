import pygame
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.hex_utils import HexGrid
from game.hex_layout import HexLayout


def visualize_hex_grid():
    """Visual test to verify hex alignment"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Hex Grid Visual Test")
    clock = pygame.time.Clock()
    
    # Use HexLayout like the game does
    hex_layout = HexLayout(hex_size=30)
    font = pygame.font.Font(None, 20)
    
    running = True
    show_coords = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    show_coords = not show_coords
        
        screen.fill((50, 50, 50))
        
        # Draw hex grid
        for col in range(12):
            for row in range(10):
                # Use HexLayout for positioning (same as game renderer)
                pixel_x, pixel_y = hex_layout.hex_to_pixel(col, row)
                
                # Offset to center on screen
                screen_x = pixel_x + 50
                screen_y = pixel_y + 50
                
                # Get hex corners
                corners = hex_layout.get_hex_corners(screen_x, screen_y)
                
                # Draw hex
                color = (100, 100, 100) if (col + row) % 2 == 0 else (80, 80, 80)
                pygame.draw.polygon(screen, color, corners)
                pygame.draw.polygon(screen, (200, 200, 200), corners, 1)
                
                # Draw coordinates
                if show_coords:
                    text = font.render(f"{col},{row}", True, (255, 255, 255))
                    text_rect = text.get_rect(center=(int(screen_x), int(screen_y)))
                    screen.blit(text, text_rect)
        
        # Draw info
        info_text = font.render("Press 'C' to toggle coordinates, ESC to exit", True, (255, 255, 255))
        screen.blit(info_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)
        
        # Exit on ESC
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
    
    pygame.quit()


def test_hex_neighbor_positions():
    """Test that hex neighbors are positioned correctly"""
    hex_layout = HexLayout(hex_size=30)
    hex_grid = HexGrid(hex_size=30)  # For axial coordinate calculations
    
    print("\nHex dimensions (using HexLayout):")
    print(f"Hex size: {hex_layout.hex_size}")
    
    # Test specific positions using HexLayout
    positions = []
    for col in range(3):
        for row in range(3):
            pixel_x, pixel_y = hex_layout.hex_to_pixel(col, row)
            positions.append(((col, row), (pixel_x, pixel_y)))
            print(f"Hex ({col},{row}) at ({pixel_x:.1f}, {pixel_y:.1f})")
    
    # Check distances between adjacent hexes
    print("\nDistances between adjacent hexes:")
    
    # Test all 6 neighbors of hex (1,1)
    center_col, center_row = 1, 1
    center_hex = hex_grid.offset_to_axial(center_col, center_row)
    center_pixel = hex_layout.hex_to_pixel(center_col, center_row)
    
    print(f"\nNeighbors of hex ({center_col},{center_row}):")
    neighbors = center_hex.get_neighbors()
    
    for i, neighbor_hex in enumerate(neighbors):
        neighbor_col, neighbor_row = hex_grid.axial_to_offset(neighbor_hex)
        if 0 <= neighbor_col < 3 and 0 <= neighbor_row < 3:
            neighbor_pixel = hex_layout.hex_to_pixel(neighbor_col, neighbor_row)
            dist = math.sqrt((neighbor_pixel[0] - center_pixel[0])**2 + 
                           (neighbor_pixel[1] - center_pixel[1])**2)
            print(f"  Neighbor {i} at ({neighbor_col},{neighbor_row}): distance = {dist:.1f}")
    
    # All neighbors should be at the same distance
    expected_dist = hex_layout.hex_size * 2  # For flat-top hexes
    print(f"\nExpected neighbor distance: {expected_dist:.1f}")


if __name__ == "__main__":
    # Run visual test
    print("Running visual hex grid test...")
    print("Look for gaps or overlaps between hexagons")
    
    # First show the analysis
    test_hex_neighbor_positions()
    
    # Then show visual
    visualize_hex_grid()