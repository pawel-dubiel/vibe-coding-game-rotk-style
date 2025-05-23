import pygame
import math
from game.hex_utils import HexGrid


def visualize_hex_grid():
    """Visual test to verify hex alignment"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Hex Grid Visual Test")
    clock = pygame.time.Clock()
    
    hex_grid = HexGrid(hex_size=30)
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
                # Current positioning logic from renderer
                pixel_x = col * hex_grid.hex_width * 0.75
                pixel_y = row * hex_grid.hex_height
                
                # Offset odd rows
                if row % 2 == 1:
                    pixel_x += hex_grid.hex_width * 0.375
                
                # Get hex corners
                corners = hex_grid.get_hex_corners(pixel_x + 50, pixel_y + 50)
                
                # Draw hex
                color = (100, 100, 100) if (col + row) % 2 == 0 else (80, 80, 80)
                pygame.draw.polygon(screen, color, corners)
                pygame.draw.polygon(screen, (200, 200, 200), corners, 1)
                
                # Draw coordinates
                if show_coords:
                    text = font.render(f"{col},{row}", True, (255, 255, 255))
                    text_rect = text.get_rect(center=(pixel_x + 50, pixel_y + 50))
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
    hex_grid = HexGrid(hex_size=30)
    
    # For flat-top hexes, the width between hex centers should be:
    # - Horizontal: hex_width * 3/4 (for the overlapping columns)
    # - Vertical: hex_height (for rows)
    
    print("\nHex dimensions:")
    print(f"Hex size: {hex_grid.hex_size}")
    print(f"Hex width: {hex_grid.hex_width}")
    print(f"Hex height: {hex_grid.hex_height}")
    
    print("\nExpected distances between hex centers:")
    print(f"Horizontal spacing: {hex_grid.hex_width * 0.75}")
    print(f"Vertical spacing: {hex_grid.hex_height}")
    
    # Test specific positions
    positions = []
    for col in range(3):
        for row in range(3):
            pixel_x = col * hex_grid.hex_width * 0.75
            pixel_y = row * hex_grid.hex_height
            
            if row % 2 == 1:
                pixel_x += hex_grid.hex_width * 0.375
            
            positions.append(((col, row), (pixel_x, pixel_y)))
            print(f"Hex ({col},{row}) at ({pixel_x:.1f}, {pixel_y:.1f})")
    
    # Check distances between adjacent hexes
    print("\nDistances between adjacent hexes:")
    
    # (0,0) to (1,0) - horizontal neighbors in same row
    p1 = next(p for (c, r), p in positions if c == 0 and r == 0)
    p2 = next(p for (c, r), p in positions if c == 1 and r == 0)
    dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    print(f"(0,0) to (1,0): {dist:.1f} (expected: {hex_grid.hex_width * 0.75:.1f})")
    
    # (0,0) to (0,1) - vertical neighbors
    p1 = next(p for (c, r), p in positions if c == 0 and r == 0)
    p2 = next(p for (c, r), p in positions if c == 0 and r == 1)
    dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    print(f"(0,0) to (0,1): {dist:.1f} (expected: ~{hex_grid.hex_height:.1f})")
    
    # The issue: for proper hex interlocking, neighbors should be at equal distances
    # A hex has 6 neighbors, all at the same distance from center
    expected_neighbor_dist = hex_grid.hex_size * math.sqrt(3)
    print(f"\nFor proper interlocking, all neighbors should be at distance: {expected_neighbor_dist:.1f}")


if __name__ == "__main__":
    # Run visual test
    print("Running visual hex grid test...")
    print("Look for gaps or overlaps between hexagons")
    
    # First show the analysis
    test_hex_neighbor_positions()
    
    # Then show visual
    visualize_hex_grid()