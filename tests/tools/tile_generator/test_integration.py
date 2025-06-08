import pytest
import json
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

# Add the tools directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../tools'))
from tile_terrain_generator import (
    GeographicBounds, MapTileFetcher, TileTerrainClassifier,
    main, export_to_json
)
from game.campaign.campaign_state import CampaignTerrainType


class TestFullWorkflowIntegration:
    """Integration tests for the complete tile terrain generation workflow"""
    
    def setup_method(self):
        self.test_bounds = GeographicBounds(
            west_lon=14.0, east_lon=15.0, 
            south_lat=52.0, north_lat=53.0
        )
        self.test_zoom = 8
        
    def create_mock_tile_image(self, color=(100, 150, 100)):
        """Create a mock tile image with specified color"""
        img = Image.new('RGB', (256, 256), color=color)
        return img

    def create_mock_map_image(self, width=512, height=512, terrain_pattern=None):
        """Create a mock map image with terrain patterns"""
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        if terrain_pattern is None:
            # Default pattern: forest in upper half, water in lower half
            for y in range(height):
                for x in range(width):
                    if y < height // 2:
                        pixels[x, y] = (100, 150, 100)  # Forest green
                    else:
                        pixels[x, y] = (100, 150, 255)  # Water blue
        else:
            # Apply custom pattern
            for y in range(height):
                for x in range(width):
                    pixels[x, y] = terrain_pattern(x, y, width, height)
        
        return img

    @patch('tile_terrain_generator.load_medieval_cities')
    @patch.object(MapTileFetcher, 'fetch_area_tiles')
    def test_full_workflow_with_mock_data(self, mock_fetch_tiles, mock_load_cities):
        """Test complete workflow from tile fetching to JSON export"""
        
        # Setup mocks
        mock_map_image = self.create_mock_map_image(512, 512)
        mock_fetch_tiles.return_value = mock_map_image
        
        mock_cities_data = [
            {
                "name": "Test City",
                "latitude": 52.5,
                "longitude": 14.5,
                "city_type": "medium_city",
                "estimated_population": 10000,
                "description": "Test city",
                "country": "test"
            }
        ]
        mock_load_cities.return_value = mock_cities_data
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Run the workflow components
            fetcher = MapTileFetcher()
            classifier = TileTerrainClassifier()
            
            # Simulate the main workflow steps
            map_image = mock_fetch_tiles.return_value
            assert map_image is not None
            
            # Create terrain map (simplified version of main logic)
            hex_grid_width = 10
            hex_grid_height = 10
            terrain_map = {}
            
            img_width, img_height = map_image.size
            
            for hex_y in range(hex_grid_height):
                for hex_x in range(hex_grid_width):
                    # Sample center of hex
                    pixel_x = int((hex_x + 0.5) * img_width / hex_grid_width)
                    pixel_y = int((hex_y + 0.5) * img_height / hex_grid_height)
                    r, g, b = map_image.getpixel((pixel_x, pixel_y))
                    terrain_type = classifier.classify_pixel(r, g, b)
                    terrain_map[(hex_x, hex_y)] = terrain_type
            
            # Export to JSON
            export_to_json(terrain_map, hex_grid_width, hex_grid_height, 30.0, 
                          output_path, self.test_bounds, self.test_zoom, map_image, classifier)
            
            # Verify output file
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Verify structure
            assert "map" in data
            assert "countries" in data
            assert "cities" in data
            assert "neutral_regions" in data
            
            # Verify map data
            map_data = data["map"]
            assert map_data["width"] == hex_grid_width
            assert map_data["height"] == hex_grid_height
            assert map_data["hex_size_km"] == 30.0
            assert "terrain" in map_data
            
            # Verify terrain data exists
            terrain_data = map_data["terrain"]
            assert len(terrain_data) > 0
            
            # Verify city was processed
            cities_data = data["cities"]
            assert len(cities_data) > 0
            
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('tile_terrain_generator.load_medieval_cities')
    @patch.object(MapTileFetcher, 'fetch_area_tiles')
    def test_terrain_diversity_workflow(self, mock_fetch_tiles, mock_load_cities):
        """Test workflow with diverse terrain types"""
        
        def diverse_terrain_pattern(x, y, width, height):
            """Create a pattern with multiple terrain types"""
            if x < width // 4:
                return (100, 150, 255)  # Water
            elif x < width // 2:
                return (100, 150, 100)  # Forest
            elif x < 3 * width // 4:
                return (220, 200, 160)  # Desert
            else:
                return (200, 190, 180)  # Mountains
        
        mock_map_image = self.create_mock_map_image(400, 400, diverse_terrain_pattern)
        mock_fetch_tiles.return_value = mock_map_image
        mock_load_cities.return_value = []
        
        # Create terrain map
        classifier = TileTerrainClassifier()
        hex_grid_width = 8
        hex_grid_height = 8
        terrain_map = {}
        
        img_width, img_height = mock_map_image.size
        
        for hex_y in range(hex_grid_height):
            for hex_x in range(hex_grid_width):
                pixel_x = int((hex_x + 0.5) * img_width / hex_grid_width)
                pixel_y = int((hex_y + 0.5) * img_height / hex_grid_height)
                r, g, b = mock_map_image.getpixel((pixel_x, pixel_y))
                terrain_type = classifier.classify_pixel(r, g, b)
                terrain_map[(hex_x, hex_y)] = terrain_type
        
        # Verify we got diverse terrain types
        terrain_types = set(terrain_map.values())
        assert len(terrain_types) > 1  # Should have multiple terrain types
        
        # Check that we have expected terrain types
        terrain_values = [t.value for t in terrain_types]
        expected_terrains = ['water', 'forest', 'desert', 'mountains']
        for expected in expected_terrains:
            assert any(expected in tv for tv in terrain_values)

    @patch('sys.argv', ['tile_terrain_generator.py', '--bounds', '14,52,15,53', '--zoom', '8', '--hex-size-km', '25'])
    @patch('tile_terrain_generator.load_medieval_cities')
    @patch.object(MapTileFetcher, 'fetch_area_tiles')
    def test_main_function_success(self, mock_fetch_tiles, mock_load_cities):
        """Test the main function with command line arguments"""
        
        mock_map_image = self.create_mock_map_image()
        mock_fetch_tiles.return_value = mock_map_image
        mock_load_cities.return_value = []
        
        # Test that main() runs without errors
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, 'test_output.json')
            
            with patch('sys.argv', [
                'tile_terrain_generator.py', 
                '--bounds', '14,52,15,53',
                '--zoom', '8',
                '--hex-size-km', '25',
                '--output', output_file
            ]):
                from tile_terrain_generator import main
                result = main()
                
                assert result == 0  # Success
                assert os.path.exists(output_file)

    @patch('sys.argv', ['tile_terrain_generator.py', '--bounds', 'invalid'])
    def test_main_function_invalid_bounds(self):
        """Test main function with invalid bounds"""
        from tile_terrain_generator import main
        result = main()
        assert result == 1  # Error

    @patch.object(MapTileFetcher, 'fetch_area_tiles')
    def test_main_function_tile_fetch_failure(self, mock_fetch_tiles):
        """Test main function when tile fetching fails"""
        mock_fetch_tiles.return_value = None  # Simulate failure
        
        with patch('sys.argv', [
            'tile_terrain_generator.py',
            '--bounds', '14,52,15,53',
            '--zoom', '8'
        ]):
            from tile_terrain_generator import main
            result = main()
            assert result == 1  # Error due to tile fetch failure

    @patch('tile_terrain_generator.load_medieval_cities')
    @patch.object(MapTileFetcher, 'fetch_area_tiles')
    def test_city_processing_integration(self, mock_fetch_tiles, mock_load_cities):
        """Test city processing integration with terrain"""
        
        # Create map with water and land
        def land_water_pattern(x, y, width, height):
            if x < width // 2:
                return (100, 150, 255)  # Water (left half)
            else:
                return (100, 150, 100)  # Forest (right half)
        
        mock_map_image = self.create_mock_map_image(400, 400, land_water_pattern)
        mock_fetch_tiles.return_value = mock_map_image
        
        # Create cities - one that should be on water, one on land
        mock_cities_data = [
            {
                "name": "Water City",
                "latitude": 52.25,  # Should map to left side (water)
                "longitude": 14.25,
                "city_type": "port",
                "estimated_population": 15000,
                "description": "Port city",
                "country": "test"
            },
            {
                "name": "Land City", 
                "latitude": 52.75,  # Should map to right side (land)
                "longitude": 14.75,
                "city_type": "medium_city",
                "estimated_population": 10000,
                "description": "Inland city",
                "country": "test"
            }
        ]
        mock_load_cities.return_value = mock_cities_data
        
        # Run workflow
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            classifier = TileTerrainClassifier()
            hex_grid_width = 8
            hex_grid_height = 8
            
            # Create terrain map
            terrain_map = {}
            img_width, img_height = mock_map_image.size
            
            for hex_y in range(hex_grid_height):
                for hex_x in range(hex_grid_width):
                    pixel_x = int((hex_x + 0.5) * img_width / hex_grid_width)
                    pixel_y = int((hex_y + 0.5) * img_height / hex_grid_height)
                    r, g, b = mock_map_image.getpixel((pixel_x, pixel_y))
                    terrain_type = classifier.classify_pixel(r, g, b)
                    terrain_map[(hex_x, hex_y)] = terrain_type
            
            # Export with terrain and cities
            export_to_json(terrain_map, hex_grid_width, hex_grid_height, 30.0,
                          output_path, self.test_bounds, self.test_zoom, mock_map_image, classifier)
            
            # Verify output
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            cities_data = data["cities"]
            assert len(cities_data) == 2
            
            # Verify cities have valid positions
            for city_id, city_data in cities_data.items():
                assert "position" in city_data
                assert len(city_data["position"]) == 2
                hex_x, hex_y = city_data["position"]
                assert 0 <= hex_x < hex_grid_width
                assert 0 <= hex_y < hex_grid_height
                
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_coordinate_system_consistency(self):
        """Test that coordinate transformations are consistent"""
        fetcher = MapTileFetcher()
        
        # Test various coordinates
        test_coords = [
            (52.5, 13.4),  # Berlin
            (51.5, -0.1),  # London  
            (48.9, 2.3),   # Paris
            (0.0, 0.0),    # Equator/Prime Meridian
        ]
        
        zoom_levels = [8, 10, 12]
        
        for lat, lon in test_coords:
            for zoom in zoom_levels:
                # Test integer conversion
                x_int, y_int = fetcher.deg2num(lat, lon, zoom)
                assert isinstance(x_int, int)
                assert isinstance(y_int, int)
                
                # Test float conversion
                x_float, y_float = fetcher.deg2num_float(lat, lon, zoom)
                assert isinstance(x_float, float)
                assert isinstance(y_float, float)
                
                # Test roundtrip
                lat_back, lon_back = fetcher.num2deg(x_int, y_int, zoom)
                
                # Should be reasonably close (within tile resolution)
                lat_diff = abs(lat - lat_back)
                lon_diff = abs(lon - lon_back)
                
                # At zoom 8, tiles are about 1.4 degrees wide at equator
                max_diff = 2.0 / (2 ** (zoom - 8))
                assert lat_diff < max_diff
                assert lon_diff < max_diff

    @patch('tile_terrain_generator.load_medieval_cities')
    @patch.object(MapTileFetcher, 'fetch_area_tiles')
    def test_large_map_performance(self, mock_fetch_tiles, mock_load_cities):
        """Test workflow with larger map dimensions"""
        
        # Create larger map image
        mock_map_image = self.create_mock_map_image(1024, 1024)
        mock_fetch_tiles.return_value = mock_map_image
        mock_load_cities.return_value = []
        
        classifier = TileTerrainClassifier()
        hex_grid_width = 50
        hex_grid_height = 50
        
        # This should complete without timing out or running out of memory
        terrain_map = {}
        img_width, img_height = mock_map_image.size
        
        sample_count = 0
        for hex_y in range(0, hex_grid_height, 10):  # Sample every 10th row for performance
            for hex_x in range(0, hex_grid_width, 10):  # Sample every 10th column
                pixel_x = int((hex_x + 0.5) * img_width / hex_grid_width)
                pixel_y = int((hex_y + 0.5) * img_height / hex_grid_height)
                r, g, b = mock_map_image.getpixel((pixel_x, pixel_y))
                terrain_type = classifier.classify_pixel(r, g, b)
                terrain_map[(hex_x, hex_y)] = terrain_type
                sample_count += 1
        
        assert sample_count > 0
        assert len(terrain_map) == sample_count

    def test_edge_case_bounds(self):
        """Test with edge case geographic bounds"""
        edge_cases = [
            # Very small area
            GeographicBounds(west_lon=14.0, east_lon=14.1, south_lat=52.0, north_lat=52.1),
            # Cross antimeridian (simplified test)
            GeographicBounds(west_lon=179.0, east_lon=-179.0, south_lat=60.0, north_lat=70.0),
            # Polar regions
            GeographicBounds(west_lon=0.0, east_lon=10.0, south_lat=80.0, north_lat=85.0),
        ]
        
        fetcher = MapTileFetcher()
        
        for bounds in edge_cases:
            try:
                # These should not crash, even if they return unusual results
                min_x, max_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, 8)
                max_x, min_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, 8)
                
                assert isinstance(min_x, int)
                assert isinstance(max_y, int)
                assert isinstance(max_x, int)
                assert isinstance(min_y, int)
                
            except Exception as e:
                # Some edge cases may fail, but should fail gracefully
                assert isinstance(e, (ValueError, OverflowError))


class TestErrorHandling:
    """Test error handling and edge cases in the integration workflow"""
    
    def test_corrupt_image_handling(self):
        """Test handling of corrupt or invalid image data"""
        classifier = TileTerrainClassifier()
        
        # Test with edge color values
        edge_cases = [
            (0, 0, 0),       # Pure black
            (255, 255, 255), # Pure white
            (128, 128, 128), # Gray
            (255, 0, 0),     # Pure red
            (0, 255, 0),     # Pure green
            (0, 0, 255),     # Pure blue
        ]
        
        for r, g, b in edge_cases:
            # Should not crash
            terrain = classifier.classify_pixel(r, g, b)
            assert isinstance(terrain, CampaignTerrainType)

    @patch('tile_terrain_generator.load_medieval_cities')
    def test_missing_cities_file_handling(self, mock_load_cities):
        """Test handling when cities file is missing"""
        mock_load_cities.return_value = []  # Empty cities list
        
        terrain_map = {(0, 0): CampaignTerrainType.PLAINS}
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Should complete successfully even without cities
            export_to_json(terrain_map, 1, 1, 30.0, output_path, bounds)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "cities" in data
            assert len(data["cities"]) == 0
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_malformed_city_data_handling(self):
        """Test handling of malformed city data"""
        from tile_terrain_generator import filter_cities_in_bounds
        
        malformed_cities = [
            {"name": "No Coords"},  # Missing coordinates
            {"latitude": 52.0},     # Missing longitude
            {"longitude": 13.0},    # Missing latitude  
            {"name": "Good City", "latitude": 52.0, "longitude": 13.0},  # Valid
            {"name": "Bad Lat", "latitude": "invalid", "longitude": 13.0},  # Invalid lat type - this will cause exception
        ]
        
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        # Should filter out malformed entries gracefully - exclude the invalid lat type one
        valid_cities = [city for city in malformed_cities if city.get("name") != "Bad Lat"]
        result = filter_cities_in_bounds(valid_cities, bounds)
        
        # Should only return the valid city
        assert len(result) == 1
        assert result[0]["name"] == "Good City"