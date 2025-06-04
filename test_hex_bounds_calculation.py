"""Test hex bounds calculation to verify the missing hexes issue."""
import pygame
from game.hex_layout import HexLayout
from game.state.camera_manager import CameraManager

# Initialize pygame
pygame.init()

# Setup
screen_width, screen_height = 1024, 768
board_width, board_height = 20, 15
hex_size = 36

# Create hex layout and camera
hex_layout = HexLayout(hex_size=hex_size, orientation='flat')
camera = CameraManager(screen_width, screen_height)

# Test at different zoom levels
zoom_levels = [0.5, 1.0, 1.5, 2.0, 2.5]

for zoom in zoom_levels:
    print(f"\n=== Zoom Level: {zoom}x ===")
    
    # Update hex layout for zoom
    scaled_hex_size = int(36 * zoom)
    hex_layout = HexLayout(hex_size=scaled_hex_size, orientation='flat')
    camera.set_zoom(zoom)
    
    # Position camera at bottom-right to test edge visibility
    camera.set_camera_position(400, 300)
    
    # Calculate visible hex range using CURRENT terrain renderer logic
    base_hex_width = hex_layout.col_spacing / zoom
    base_hex_height = hex_layout.row_spacing / zoom
    
    start_col = max(0, int(camera.camera_x / base_hex_width) - 1)
    end_col = min(board_width, int((camera.camera_x + screen_width / zoom) / base_hex_width) + 2)
    start_row = max(0, int(camera.camera_y / base_hex_height) - 1)
    end_row = min(board_height, int((camera.camera_y + screen_height / zoom) / base_hex_height) + 2)
    
    print(f"Camera position: ({camera.camera_x}, {camera.camera_y})")
    print(f"Base hex dimensions: {base_hex_width:.2f} x {base_hex_height:.2f}")
    print(f"Scaled hex dimensions: {hex_layout.col_spacing:.2f} x {hex_layout.row_spacing:.2f}")
    print(f"Visible columns: {start_col} to {end_col-1} (count: {end_col - start_col})")
    print(f"Visible rows: {start_row} to {end_row-1} (count: {end_row - start_row})")
    
    # Check if we're missing hexes at the edges
    # Calculate the rightmost hex that should be visible
    rightmost_hex_x = (board_width - 1) * hex_layout.col_spacing
    rightmost_screen_x = rightmost_hex_x - camera.camera_x
    if rightmost_screen_x < screen_width and end_col < board_width:
        print(f"WARNING: Missing hexes on the right! Last hex at screen x={rightmost_screen_x:.2f}")
    
    # Calculate the bottommost hex that should be visible  
    bottommost_hex_y = (board_height - 1) * hex_layout.row_spacing
    bottommost_screen_y = bottommost_hex_y - camera.camera_y
    if bottommost_screen_y < screen_height and end_row < board_height:
        print(f"WARNING: Missing hexes at the bottom! Last hex at screen y={bottommost_screen_y:.2f}")
    
    # Alternative calculation (without dividing by zoom)
    print("\nAlternative calculation (treating camera as scaled space):")
    alt_start_col = max(0, int(camera.camera_x / hex_layout.col_spacing) - 1)
    alt_end_col = min(board_width, int((camera.camera_x + screen_width) / hex_layout.col_spacing) + 2)
    alt_start_row = max(0, int(camera.camera_y / hex_layout.row_spacing) - 1)
    alt_end_row = min(board_height, int((camera.camera_y + screen_height) / hex_layout.row_spacing) + 2)
    
    print(f"Alt visible columns: {alt_start_col} to {alt_end_col-1} (count: {alt_end_col - alt_start_col})")
    print(f"Alt visible rows: {alt_start_row} to {alt_end_row-1} (count: {alt_end_row - alt_start_row})")