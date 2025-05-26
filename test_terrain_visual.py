#!/usr/bin/env python3
"""Visual test to check terrain rendering alignment"""

import pygame
import sys
sys.path.append('.')

from game.hex_layout import HexLayout
from game.terrain import TerrainMap, TerrainType
from game.hex_utils import HexGrid

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Terrain Coordinate Test")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 20)

# Create terrain map with specific pattern
width, height = 15, 15
terrain_map = TerrainMap(width, height, use_legacy_generation=True)

# Create a checkerboard pattern to see alignment
for y in range(height):
    for x in range(width):
        if (x + y) % 2 == 0:
            terrain_map.set_terrain(x, y, TerrainType.WATER)
        else:
            terrain_map.set_terrain(x, y, TerrainType.FOREST)

# Special markers
terrain_map.set_terrain(0, 0, TerrainType.HILLS)  # Top-left
terrain_map.set_terrain(width-1, 0, TerrainType.DESERT)  # Top-right
terrain_map.set_terrain(0, height-1, TerrainType.SWAMP)  # Bottom-left
terrain_map.set_terrain(width-1, height-1, TerrainType.SNOW)  # Bottom-right

# Setup hex layout
hex_layout = HexLayout(hex_size=36, orientation='flat')
hex_grid = HexGrid(hex_size=36)

colors = {
    TerrainType.WATER: (64, 164, 223),
    TerrainType.FOREST: (34, 139, 34),
    TerrainType.HILLS: (139, 90, 43),
    TerrainType.DESERT: (238, 203, 173),
    TerrainType.SWAMP: (47, 79, 47),
    TerrainType.SNOW: (255, 250, 250)
}

running = True
show_coords = True
camera_x, camera_y = 0, 0
mouse_hex = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_c:
                show_coords = not show_coords
            elif event.key == pygame.K_LEFT:
                camera_x -= 50
            elif event.key == pygame.K_RIGHT:
                camera_x += 50
            elif event.key == pygame.K_UP:
                camera_y -= 50
            elif event.key == pygame.K_DOWN:
                camera_y += 50
    
    # Get mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()
    world_x = mouse_x + camera_x
    world_y = mouse_y + camera_y
    mouse_hex = hex_layout.pixel_to_hex(world_x, world_y)
    
    # Clear screen
    screen.fill((50, 50, 50))
    
    # Draw hexagons
    for col in range(width):
        for row in range(height):
            # Get hex center
            pixel_x, pixel_y = hex_layout.hex_to_pixel(col, row)
            screen_x = pixel_x - camera_x
            screen_y = pixel_y - camera_y
            
            # Skip if off-screen
            if screen_x < -100 or screen_x > 900 or screen_y < -100 or screen_y > 700:
                continue
            
            # Get terrain
            terrain = terrain_map.get_terrain(col, row)
            if terrain:
                color = colors.get(terrain.type, (100, 100, 100))
            else:
                color = (255, 0, 0)  # Red for missing terrain
            
            # Get hex corners
            corners = hex_layout.get_hex_corners(screen_x, screen_y)
            
            # Highlight if mouse is over this hex
            if mouse_hex and mouse_hex[0] == col and mouse_hex[1] == row:
                pygame.draw.polygon(screen, (255, 255, 255), corners, 3)
            
            # Draw hex
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, (0, 0, 0), corners, 1)
            
            # Show coordinates
            if show_coords:
                coord_text = font.render(f"{col},{row}", True, (255, 255, 255))
                text_rect = coord_text.get_rect(center=(int(screen_x), int(screen_y)))
                screen.blit(coord_text, text_rect)
    
    # Show mouse info
    if mouse_hex:
        mx, my = mouse_hex
        if 0 <= mx < width and 0 <= my < height:
            terrain = terrain_map.get_terrain(mx, my)
            if terrain:
                info_text = font.render(f"Mouse at ({mx},{my}): {terrain.type.value}", True, (255, 255, 255))
            else:
                info_text = font.render(f"Mouse at ({mx},{my}): No terrain!", True, (255, 0, 0))
            screen.blit(info_text, (10, 10))
    
    # Instructions
    inst_text = font.render("Arrow keys: move camera, C: toggle coords, ESC: quit", True, (255, 255, 255))
    screen.blit(inst_text, (10, 580))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()