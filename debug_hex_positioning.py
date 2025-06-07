#!/usr/bin/env python3
"""
Debug script to analyze hex positioning in campaign vs battle renderers
"""
import pygame
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.hex_layout import HexLayout
from game.campaign.campaign_state import CampaignState
from game.campaign.campaign_renderer import CampaignRenderer

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Hex Positioning Debug")
    
    # Create hex layout and campaign state
    hex_layout = HexLayout(hex_size=24)
    campaign_state = CampaignState()
    campaign_renderer = CampaignRenderer(screen)
    
    print("=== HEX LAYOUT ANALYSIS ===")
    print(f"hex_size: {hex_layout.hex_size}")
    print(f"col_spacing: {hex_layout.col_spacing:.3f}")
    print(f"row_spacing: {hex_layout.row_spacing:.3f}")
    print(f"row_offset: {hex_layout.row_offset:.3f}")
    print()
    
    print("=== COORDINATE MAPPING (first few hexes) ===")
    for row in range(3):
        for col in range(4):
            x, y = hex_layout.hex_to_pixel(col, row)
            print(f"({col},{row}) -> ({x:6.2f}, {y:6.2f})", end="  ")
        print()
    print()
    
    print("=== TESTING VISIBLE RANGE CALCULATION ===")
    # Simulate camera at center
    campaign_renderer.camera_x = -200
    campaign_renderer.camera_y = -150
    
    min_q, max_q, min_r, max_r = campaign_renderer._get_visible_hex_range(campaign_state)
    print(f"Camera: ({campaign_renderer.camera_x}, {campaign_renderer.camera_y})")
    print(f"Visible range: q=[{min_q}, {max_q}), r=[{min_r}, {max_r})")
    print()
    
    print("=== CORNER CALCULATIONS COMPARISON ===")
    center_x, center_y = 100, 100
    
    # HexLayout method (flat-top, 30° offset)
    corners_layout = hex_layout.get_hex_corners(center_x, center_y)
    print("HexLayout corners (30° offset, flat-top):")
    for i, (x, y) in enumerate(corners_layout):
        print(f"  {i}: ({x:6.2f}, {y:6.2f})")
    
    # Campaign renderer method (0° offset, pointy-top?)
    corners_campaign = campaign_renderer._get_hex_corners_cached(center_x, center_y, hex_layout.hex_size)
    print("Campaign renderer corners (0° offset):")
    for i, (x, y) in enumerate(corners_campaign):
        print(f"  {i}: ({x:6.2f}, {y:6.2f})")
    
    print()
    print("=== GRID PATTERN SIMULATION ===")
    print("Expected interlocking pattern (should show offset for odd rows):")
    for row in range(3):
        line = ""
        for col in range(6):
            x, y = hex_layout.hex_to_pixel(col, row)
            if row % 2 == 0:
                line += f"({col},{row})"
            else:
                line += f"  ({col},{row})"
            line += "  "
        print(line)
    
if __name__ == "__main__":
    main()