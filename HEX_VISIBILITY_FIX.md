# Hex Visibility Fix for Zoom Functionality

## Problem Description

When zooming in or out, hexes at the screen edges would disappear. This was particularly noticeable when zoomed in - the visible area would shrink more than expected, leaving blank areas at the screen edges where hexes should be rendered.

## Root Cause

The issue was in the terrain renderer's calculation of which hexes are visible on screen. There was a mismatch between coordinate systems:

1. **Camera coordinates** are in unscaled world space
2. **Hex layout dimensions** (hex_width, hex_height) are scaled by the zoom factor
3. The visible hex range calculation was mixing these two coordinate systems incorrectly

In `terrain_renderer.py`, the code was using scaled hex dimensions to determine which hexes fall within the unscaled camera viewport:

```python
# OLD CODE (incorrect)
hex_width = self.hex_layout.col_spacing    # This is already scaled by zoom
hex_height = self.hex_layout.row_spacing   # This is already scaled by zoom

start_col = max(0, int(camera_x / hex_width) - 1)  # camera_x is unscaled!
```

## Solution

The fix divides the hex dimensions by the zoom level to get base (unscaled) dimensions that match the camera coordinate system:

```python
# NEW CODE (correct)
# Use unscaled hex dimensions for calculating visible range
base_hex_width = self.hex_layout.col_spacing / zoom_level
base_hex_height = self.hex_layout.row_spacing / zoom_level

start_col = max(0, int(camera_x / base_hex_width) - 1)
end_col = min(game_state.board_width, int((camera_x + screen_width / zoom_level) / base_hex_width) + 2)
```

## Technical Details

### Coordinate Systems

1. **World Coordinates**: Unscaled coordinates where hex (0,0) is always at the same position regardless of zoom
2. **Screen Coordinates**: Pixel coordinates on the display
3. **Hex Coordinates**: Grid coordinates (col, row)

### Zoom Implementation

- When zooming, the `hex_layout` is recreated with a new hex_size (base_size * zoom_level)
- This affects `hex_to_pixel()` conversions, making hexes appear larger/smaller
- Camera position remains in unscaled world coordinates
- The viewport calculation must account for this scaling difference

### Files Modified

- `/Users/pawel/work/game/game/rendering/terrain_renderer.py` - Fixed the visible hex calculation in `render_terrain()` method

### Tests Added

- `/Users/pawel/work/game/tests/test_hex_rendering_zoom.py` - Unit tests verifying hex visibility calculations at different zoom levels
- `/Users/pawel/work/game/test_hex_visibility_fix.py` - Visual test demonstrating the fix

## Verification

The fix ensures that:
1. Hexes remain visible at screen edges at all zoom levels
2. The correct number of hexes are rendered based on zoom level
3. No blank areas appear when zooming in
4. Camera bounds are properly enforced

Run `python test_hex_visibility_fix.py` to see the fix in action.