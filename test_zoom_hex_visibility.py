"""Test that all hexes are properly rendered at different zoom levels."""
import pygame
import sys
import os

# Set up test environment
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from game.game_state import GameState
from game.input_handler import InputHandler
from game.rendering.terrain_renderer import TerrainRenderer
from game.hex_layout import HexLayout

def test_hex_visibility_at_zoom():
    """Test that hexes at board edges are visible when zoomed."""
    screen = pygame.display.set_mode((1024, 768))
    
    # Create game state
    config = {
        'board_size': (20, 15),
        'knights': 0,
        'castles': 0
    }
    game_state = GameState(config)
    input_handler = InputHandler()
    
    # Create renderer
    from game.renderer import Renderer
    renderer = Renderer(screen)
    game_state.renderer = renderer
    
    # Test at different zoom levels
    zoom_levels = [0.5, 1.0, 1.5, 2.0, 2.5]
    
    for zoom in zoom_levels:
        print(f"\nTesting zoom level: {zoom}x")
        
        # Set zoom
        game_state.camera_manager.set_zoom(zoom)
        input_handler.update_zoom(game_state)
        
        # Get the terrain renderer
        terrain_renderer = game_state.renderer.terrain_renderer
        hex_layout = terrain_renderer.hex_layout
        
        # Position camera to see bottom-right corner
        # Calculate position to put bottom-right hex in view
        last_hex_x = (game_state.board_width - 1) * hex_layout.col_spacing
        last_hex_y = (game_state.board_height - 1) * hex_layout.row_spacing
        
        # Position camera so bottom-right hex is visible
        camera_x = max(0, last_hex_x - screen.get_width() + hex_layout.hex_width)
        camera_y = max(0, last_hex_y - screen.get_height() + hex_layout.hex_height)
        game_state.camera_manager.set_camera_position(camera_x, camera_y)
        
        # Calculate visible hex range using the terrain renderer's logic
        hex_width = hex_layout.col_spacing
        hex_height = hex_layout.row_spacing
        
        start_col = max(0, int(camera_x / hex_width) - 1)
        end_col = min(game_state.board_width, int((camera_x + screen.get_width()) / hex_width) + 2)
        start_row = max(0, int(camera_y / hex_height) - 1)
        end_row = min(game_state.board_height, int((camera_y + screen.get_height()) / hex_height) + 2)
        
        print(f"Camera position: ({camera_x:.1f}, {camera_y:.1f})")
        print(f"Visible columns: {start_col} to {end_col-1}")
        print(f"Visible rows: {start_row} to {end_row-1}")
        
        # Check if bottom-right hex is included
        if end_col <= game_state.board_width - 1:
            print(f"ERROR: Missing rightmost column! Last visible: {end_col-1}, should see: {game_state.board_width-1}")
        else:
            print(f"✓ Rightmost column {game_state.board_width-1} is visible")
            
        if end_row <= game_state.board_height - 1:
            print(f"ERROR: Missing bottom row! Last visible: {end_row-1}, should see: {game_state.board_height-1}")
        else:
            print(f"✓ Bottom row {game_state.board_height-1} is visible")
    
    print("\nAll tests completed!")
    pygame.quit()

if __name__ == "__main__":
    test_hex_visibility_at_zoom()