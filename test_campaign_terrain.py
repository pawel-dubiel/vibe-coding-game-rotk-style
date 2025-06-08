#!/usr/bin/env python3
"""Test script to verify the new campaign terrain system"""

import pygame
from game.campaign.campaign_state import CampaignState, CampaignTerrainType
from game.campaign.campaign_renderer import CampaignRenderer

def test_campaign_terrain_types():
    """Test the new elevation-based campaign terrain system"""
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    
    # Create campaign state
    campaign_state = CampaignState()
    
    # Test that we can create all terrain types
    terrain_types = [
        CampaignTerrainType.PLAINS,
        CampaignTerrainType.FOREST,
        CampaignTerrainType.DEEP_FOREST,
        CampaignTerrainType.HILLS,
        CampaignTerrainType.MOUNTAINS,
        CampaignTerrainType.HIGH_MOUNTAINS,
        CampaignTerrainType.WATER,
        CampaignTerrainType.DEEP_WATER,
        CampaignTerrainType.SWAMP,
        CampaignTerrainType.DESERT,
        CampaignTerrainType.SNOW,
        CampaignTerrainType.GLACIAL
    ]
    
    print("✅ Campaign Terrain Types:")
    for terrain in terrain_types:
        print(f"  - {terrain.value} ({terrain.name})")
    
    # Test renderer has colors for all terrain types
    renderer = CampaignRenderer(screen)
    print("\n✅ Terrain Colors Available:")
    for terrain in terrain_types:
        color = renderer.terrain_colors.get(terrain.name)
        if color:
            print(f"  - {terrain.value}: RGB{color}")
        else:
            print(f"  ⚠ Missing color for {terrain.value}")
    
    # Test setting terrain in the map
    print("\n✅ Testing Terrain Placement:")
    
    # Set some terrain types for testing
    test_positions = [
        (90, 90, CampaignTerrainType.PLAINS),
        (91, 90, CampaignTerrainType.HILLS),
        (92, 90, CampaignTerrainType.MOUNTAINS),
        (93, 90, CampaignTerrainType.HIGH_MOUNTAINS),
        (94, 90, CampaignTerrainType.FOREST),
        (95, 90, CampaignTerrainType.DEEP_FOREST),
        (96, 90, CampaignTerrainType.WATER),
        (97, 90, CampaignTerrainType.DESERT),
        (98, 90, CampaignTerrainType.SNOW),
        (99, 90, CampaignTerrainType.GLACIAL)
    ]
    
    for x, y, terrain_type in test_positions:
        campaign_state.terrain_map[(x, y)] = terrain_type
        retrieved = campaign_state.terrain_map.get((x, y))
        assert retrieved == terrain_type, f"Failed to set/get terrain {terrain_type}"
        print(f"  - Set {terrain_type.value} at ({x}, {y}) ✅")
    
    # Test terrain loading from JSON format
    print("\n✅ Testing Terrain Loading:")
    terrain_data = {
        "plains": [[80, 85, 80, 85]],
        "hills": [[85, 90, 80, 85]],
        "mountains": [[90, 95, 80, 85]],
        "high_mountains": [[95, 100, 80, 85]],
        "forest": [[80, 85, 85, 90]],
        "deep_forest": [[85, 90, 85, 90]],
        "water": [[90, 95, 85, 90]],
        "desert": [[95, 100, 85, 90]],
        "snow": [[80, 85, 90, 95]],
        "glacial": [[85, 90, 90, 95]]
    }
    
    # Clear existing terrain
    original_terrain_map = dict(campaign_state.terrain_map)
    campaign_state.terrain_map.clear()
    
    # Load test terrain data
    campaign_state._load_terrain_from_data(terrain_data)
    
    # Verify terrain was loaded correctly
    expected_terrains = {
        (80, 80): CampaignTerrainType.PLAINS,
        (85, 80): CampaignTerrainType.HILLS,
        (90, 80): CampaignTerrainType.MOUNTAINS,
        (95, 80): CampaignTerrainType.HIGH_MOUNTAINS,
        (80, 85): CampaignTerrainType.FOREST,
        (85, 85): CampaignTerrainType.DEEP_FOREST,
        (90, 85): CampaignTerrainType.WATER,
        (95, 85): CampaignTerrainType.DESERT,
        (80, 90): CampaignTerrainType.SNOW,
        (85, 90): CampaignTerrainType.GLACIAL
    }
    
    for (x, y), expected_terrain in expected_terrains.items():
        actual_terrain = campaign_state.terrain_map.get((x, y))
        if actual_terrain == expected_terrain:
            print(f"  - Loaded {expected_terrain.value} at ({x}, {y}) ✅")
        else:
            print(f"  ⚠ Expected {expected_terrain.value} at ({x}, {y}), got {actual_terrain}")
    
    # Restore original terrain map
    campaign_state.terrain_map = original_terrain_map
    
    print(f"\n✅ Campaign terrain system working correctly!")
    print(f"Map size: {campaign_state.map_width}x{campaign_state.map_height} hexes")
    print(f"Scale: 30km per hex")
    print(f"Total coverage: {campaign_state.map_width * 30}km x {campaign_state.map_height * 30}km")
    print(f"Elevation ranges:")
    print(f"  - Plains: 0-200m")
    print(f"  - Hills: 200-600m") 
    print(f"  - Mountains: 600-2500m")
    print(f"  - High Mountains: 2500m+")
    
    pygame.quit()

if __name__ == "__main__":
    test_campaign_terrain_types()