import os
import pygame
import unittest
from game.game_state import GameState
from game.input_handler import InputHandler

class TestCameraZoomBounds(unittest.TestCase):
    def setUp(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        config = {'board_size': (20, 20), 'knights': 0, 'castles': 0}
        self.game_state = GameState(config)
        self.input_handler = InputHandler()

    def tearDown(self):
        pygame.quit()

    def test_camera_bounds_after_zoom_in(self):
        # Zoom in to maximum
        for _ in range(10):
            self.input_handler.zoom_in(self.game_state)
        hl = self.input_handler.hex_layout

        # Expected world bounds based on hex layout
        board_pixel_width = ((self.game_state.board_width - 1) * hl.col_spacing +
                             hl.hex_width + (hl.row_offset if self.game_state.board_height > 1 else 0))
        board_pixel_height = ((self.game_state.board_height - 1) * hl.row_spacing +
                              hl.hex_height)

        expected_x = max(0, int(board_pixel_width) - self.game_state.camera_manager.screen_width)
        expected_y = max(0, int(board_pixel_height) - self.game_state.camera_manager.screen_height)

        # Move camera beyond bounds and ensure clamping
        self.game_state.camera_manager.set_camera_position(999999, 999999)
        self.assertEqual(int(self.game_state.camera_manager.camera_x), expected_x)
        self.assertEqual(int(self.game_state.camera_manager.camera_y), expected_y)

if __name__ == '__main__':
    unittest.main()
