import unittest
import pygame
import os
from unittest.mock import MagicMock, patch
from game.asset_manager import AssetManager

class TestAssetManager(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Mock the display so convert_alpha works
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        self.asset_manager = AssetManager("assets")
        
    def tearDown(self):
        pygame.quit()
        
    @patch('pygame.image.load')
    def test_get_unit_icon_caching(self, mock_load):
        """Test that get_unit_icon loads and caches icons"""
        # Create a mock surface
        mock_surface = pygame.Surface((100, 100))
        mock_load.return_value = mock_surface
        
        # 1. Request icon (should load from disk)
        icon1 = self.asset_manager.get_unit_icon("warrior", 1, 0, 64)
        
        self.assertIsNotNone(icon1)
        mock_load.assert_called_once() # Should be called once for base image
        
        # 2. Request same icon (should be cached)
        icon2 = self.asset_manager.get_unit_icon("warrior", 1, 0, 64)
        self.assertEqual(icon1, icon2)
        mock_load.assert_called_once() # Call count shouldn't increase
        
        # 3. Request rotated icon (should use same base image, but generate new rotation)
        icon3 = self.asset_manager.get_unit_icon("warrior", 1, 90, 64)
        self.assertNotEqual(icon1, icon3) # Different surface
        mock_load.assert_called_once() # Still only one disk load for base image
        
    @patch('pygame.image.load')
    def test_get_unit_icon_sizing(self, mock_load):
        """Test sizing"""
        mock_surface = pygame.Surface((100, 100))
        mock_load.return_value = mock_surface
        
        icon = self.asset_manager.get_unit_icon("warrior", 1, 0, 32)
        self.assertEqual(icon.get_width(), 32)
        self.assertEqual(icon.get_height(), 32)

if __name__ == '__main__':
    unittest.main()
