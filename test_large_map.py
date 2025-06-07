#!/usr/bin/env python3
"""Test script to verify the large map functionality"""

import pygame
from game.campaign.campaign_state import CampaignState
from game.campaign.campaign_renderer import CampaignRenderer

def test_large_map():
    """Test that the large map (180x192) works correctly"""
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    
    # Create campaign state
    campaign_state = CampaignState()
    
    # Verify map dimensions
    print(f"Map dimensions: {campaign_state.map_width}x{campaign_state.map_height}")
    assert campaign_state.map_width == 180, f"Expected width 180, got {campaign_state.map_width}"
    assert campaign_state.map_height == 192, f"Expected height 192, got {campaign_state.map_height}"
    
    # Test renderer initialization
    renderer = CampaignRenderer(screen)
    print(f"Renderer camera position: ({renderer.camera_x}, {renderer.camera_y})")
    
    # Test visibility calculation
    min_q, max_q, min_r, max_r = renderer._get_visible_hex_range(campaign_state)
    print(f"Visible hex range: q({min_q}-{max_q}), r({min_r}-{max_r})")
    
    # Verify that we don't try to render the entire map at once
    visible_hexes = (max_q - min_q) * (max_r - min_r)
    total_hexes = campaign_state.map_width * campaign_state.map_height
    
    print(f"Visible hexes: {visible_hexes} out of {total_hexes} total")
    print(f"Performance ratio: {visible_hexes/total_hexes*100:.1f}% of map visible")
    
    # Should be rendering much less than the full map for performance
    assert visible_hexes < total_hexes * 0.1, "Too many hexes visible at once"
    
    # Test that cities are positioned within bounds
    for city_id, city in campaign_state.cities.items():
        assert 0 <= city.position.q < campaign_state.map_width, f"City {city_id} q={city.position.q} out of bounds"
        assert 0 <= city.position.r < campaign_state.map_height, f"City {city_id} r={city.position.r} out of bounds"
        print(f"City {city.name} at ({city.position.q}, {city.position.r}) - OK")
    
    print("✅ Large map test passed!")
    pygame.quit()

if __name__ == "__main__":
    test_large_map()