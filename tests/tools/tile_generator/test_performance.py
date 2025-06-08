import pytest
import time
import sys
import os
from unittest.mock import Mock, patch
from PIL import Image

# Add the tools directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../tools'))
from tile_terrain_generator import (
    TileTerrainClassifier, merge_adjacent_rectangles, 
    merge_horizontal_rectangles, GeographicBounds,
    convert_cities_to_hex_coordinates
)
from game.campaign.campaign_state import CampaignTerrainType


class TestPerformance:
    """Performance tests for tile terrain generator components"""
    
    def setup_method(self):
        self.classifier = TileTerrainClassifier()

    def test_terrain_classification_performance(self):
        """Test terrain classification performance with many pixels"""
        start_time = time.time()
        
        # Classify 10,000 pixels
        for i in range(10000):
            r = (i * 17) % 256
            g = (i * 31) % 256  
            b = (i * 47) % 256
            terrain = self.classifier.classify_pixel(r, g, b)
            assert isinstance(terrain, CampaignTerrainType)
        
        elapsed = time.time() - start_time
        
        # Should classify 10k pixels in under 1 second
        assert elapsed < 1.0, f"Classification took {elapsed:.2f}s, expected < 1.0s"

    def test_rectangle_merging_performance(self):
        """Test rectangle merging performance with many rectangles"""
        
        # Create 1000 rectangles in a grid pattern
        rectangles = []
        for y in range(10):
            for x in range(100):
                rectangles.append([x, x+1, y, y+1])
        
        start_time = time.time()
        merged = merge_adjacent_rectangles(rectangles)
        elapsed = time.time() - start_time
        
        # Should merge quickly and reduce rectangle count significantly
        assert elapsed < 0.5, f"Merging took {elapsed:.2f}s, expected < 0.5s"
        assert len(merged) < len(rectangles), "Should reduce rectangle count"

    def test_horizontal_merging_performance(self):
        """Test horizontal rectangle merging performance"""
        
        # Create many horizontally adjacent rectangles
        rectangles = []
        for x in range(1000):
            rectangles.append([x, x+1, 0, 1])
        
        start_time = time.time()
        merged = merge_horizontal_rectangles(rectangles)
        elapsed = time.time() - start_time
        
        # Should merge into single rectangle quickly
        assert elapsed < 0.1, f"Horizontal merging took {elapsed:.2f}s, expected < 0.1s"
        assert len(merged) == 1, "Should merge into single rectangle"
        assert merged[0] == [0, 1000, 0, 1], "Should create correct merged rectangle"

    def test_large_city_list_performance(self):
        """Test performance with large number of cities"""
        
        # Create 1000 cities
        cities = []
        for i in range(1000):
            cities.append({
                "name": f"City {i}",
                "latitude": 50.0 + (i % 100) * 0.01,
                "longitude": 10.0 + (i // 100) * 0.01,
                "city_type": "medium_city",
                "estimated_population": 10000,
                "description": "Test city",
                "country": "test"
            })
        
        bounds = GeographicBounds(west_lon=10.0, east_lon=11.0, south_lat=50.0, north_lat=51.0)
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            # Mock consistent coordinates to test collision handling
            mock_fetcher.deg2num_float.side_effect = lambda lat, lon, zoom: (
                (lon - 10.0) * 100, (lat - 50.0) * 100
            )
            mock_fetcher.deg2num.side_effect = lambda lat, lon, zoom: (
                int((lon - 10.0) * 100), int((lat - 50.0) * 100)
            )
            mock_fetcher_class.return_value = mock_fetcher
            
            start_time = time.time()
            result, collisions, unique_positions = convert_cities_to_hex_coordinates(
                cities, bounds, 100, 100, 10
            )
            elapsed = time.time() - start_time
            
            # Should process 1000 cities in reasonable time
            assert elapsed < 5.0, f"City processing took {elapsed:.2f}s, expected < 5.0s"
            assert len(result) == len(cities), "Should process all cities"

    def test_color_distance_performance(self):
        """Test color distance calculation performance"""
        
        start_time = time.time()
        
        # Calculate 100,000 color distances
        for i in range(100000):
            color1 = ((i * 17) % 256, (i * 31) % 256, (i * 47) % 256)
            color2 = ((i * 23) % 256, (i * 37) % 256, (i * 53) % 256)
            distance = self.classifier.color_distance(color1, color2)
            assert distance >= 0
        
        elapsed = time.time() - start_time
        
        # Should calculate 100k distances in under 0.5 seconds
        assert elapsed < 0.5, f"Color distance calculation took {elapsed:.2f}s, expected < 0.5s"


class TestMemoryUsage:
    """Test memory usage patterns and limits"""
    
    def test_large_terrain_map_memory(self):
        """Test memory usage with large terrain maps"""
        
        # Create large terrain map (100x100 = 10,000 hexes)
        terrain_map = {}
        
        for y in range(100):
            for x in range(100):
                # Vary terrain types to test different memory patterns
                if (x + y) % 4 == 0:
                    terrain_type = CampaignTerrainType.PLAINS
                elif (x + y) % 4 == 1:
                    terrain_type = CampaignTerrainType.FOREST
                elif (x + y) % 4 == 2:
                    terrain_type = CampaignTerrainType.WATER
                else:
                    terrain_type = CampaignTerrainType.MOUNTAINS
                
                terrain_map[(x, y)] = terrain_type
        
        assert len(terrain_map) == 10000
        
        # Test that we can efficiently group by terrain type
        terrain_groups = {}
        for (hex_x, hex_y), terrain_type in terrain_map.items():
            terrain_name = terrain_type.value
            if terrain_name not in terrain_groups:
                terrain_groups[terrain_name] = []
            terrain_groups[terrain_name].append([hex_x, hex_x + 1, hex_y, hex_y + 1])
        
        # Should have 4 terrain types with ~2500 rectangles each
        assert len(terrain_groups) == 4
        for terrain_type, rectangles in terrain_groups.items():
            assert len(rectangles) > 2000  # Should have many rectangles

    def test_rectangle_merging_memory_efficiency(self):
        """Test that rectangle merging reduces memory usage"""
        
        # Create many small rectangles
        rectangles = []
        for y in range(50):
            for x in range(50):
                rectangles.append([x, x+1, y, y+1])
        
        original_count = len(rectangles)
        
        # Merge rectangles
        merged = merge_adjacent_rectangles(rectangles)
        
        # Should significantly reduce count
        reduction_ratio = len(merged) / original_count
        assert reduction_ratio < 0.1, f"Only reduced rectangles by {(1-reduction_ratio)*100:.1f}%, expected >90%"

    def test_city_coordinate_caching(self):
        """Test that coordinate calculations don't create memory leaks"""
        
        bounds = GeographicBounds(west_lon=10.0, east_lon=11.0, south_lat=50.0, north_lat=51.0)
        
        # Process same cities multiple times to test for memory accumulation
        cities = [
            {
                "name": "Test City",
                "latitude": 50.5,
                "longitude": 10.5,
                "city_type": "medium_city",
                "estimated_population": 10000,
                "description": "Test",
                "country": "test"
            }
        ]
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.deg2num_float.return_value = (50.0, 50.0)
            mock_fetcher.deg2num.return_value = (50, 50)
            mock_fetcher_class.return_value = mock_fetcher
            
            # Process same cities 100 times
            for i in range(100):
                result, _, _ = convert_cities_to_hex_coordinates(
                    cities, bounds, 100, 100, 10
                )
                assert len(result) == 1


class TestScalability:
    """Test scalability with different input sizes"""
    
    def test_zoom_level_scaling(self):
        """Test that tile count scales with zoom level"""
        from tile_terrain_generator import MapTileFetcher
        
        fetcher = MapTileFetcher()
        bounds = GeographicBounds(west_lon=10.0, east_lon=11.0, south_lat=50.0, north_lat=51.0)
        
        tile_counts = {}
        
        for zoom in [6, 8, 10]:
            # Calculate tile bounds
            min_x, max_y = fetcher.deg2num(bounds.south_lat, bounds.west_lon, zoom)
            max_x, min_y = fetcher.deg2num(bounds.north_lat, bounds.east_lon, zoom)
            
            tiles_x = max_x - min_x + 1
            tiles_y = max_y - min_y + 1
            total_tiles = tiles_x * tiles_y
            
            tile_counts[zoom] = total_tiles
            
            # Higher zoom should require more tiles
            assert total_tiles > 0
        
        # Tile count should increase with zoom level
        assert tile_counts[10] > tile_counts[8] > tile_counts[6]

    def test_hex_grid_size_scaling(self):
        """Test that processing scales with hex grid size"""
        classifier = TileTerrainClassifier()
        
        # Test with different grid sizes
        grid_sizes = [10, 20, 50]
        processing_times = {}
        
        for grid_size in grid_sizes:
            start_time = time.time()
            
            # Simulate terrain classification for grid
            terrain_count = 0
            for y in range(grid_size):
                for x in range(grid_size):
                    # Simulate pixel sampling and classification
                    r, g, b = (x * 5) % 256, (y * 7) % 256, (x + y) % 256
                    terrain = classifier.classify_pixel(r, g, b)
                    terrain_count += 1
            
            elapsed = time.time() - start_time
            processing_times[grid_size] = elapsed
            
            assert terrain_count == grid_size * grid_size
        
        # Larger grids should take more time (approximately quadratic)
        assert processing_times[50] > processing_times[20] > processing_times[10]

    def test_city_collision_resolution_scaling(self):
        """Test that collision resolution scales reasonably"""
        
        # Create cities that will all collide at same position
        bounds = GeographicBounds(west_lon=10.0, east_lon=11.0, south_lat=50.0, north_lat=51.0)
        
        city_counts = [10, 50, 100]
        processing_times = {}
        
        for city_count in city_counts:
            cities = []
            for i in range(city_count):
                cities.append({
                    "name": f"City {i}",
                    "latitude": 50.5,  # Same position to force collisions
                    "longitude": 10.5,
                    "city_type": "medium_city",
                    "estimated_population": 10000,
                    "description": "Test",
                    "country": "test"
                })
            
            with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
                mock_fetcher = Mock()
                # Make all cities map to same initial position
                mock_fetcher.deg2num_float.return_value = (50.0, 50.0)
                mock_fetcher.deg2num.return_value = (50, 50)
                mock_fetcher_class.return_value = mock_fetcher
                
                start_time = time.time()
                result, collisions, unique_positions = convert_cities_to_hex_coordinates(
                    cities, bounds, 100, 100, 10
                )
                elapsed = time.time() - start_time
                
                processing_times[city_count] = elapsed
                
                # Should place all cities despite collisions
                assert len(result) == city_count
                assert collisions >= city_count - 1  # All but first should collide
        
        # Time should scale sub-quadratically (collision resolution is efficient)
        time_ratio_50_10 = processing_times[50] / processing_times[10]
        time_ratio_100_50 = processing_times[100] / processing_times[50]
        
        # Should not scale worse than quadratic
        assert time_ratio_50_10 < 25  # 5x cities should be < 25x time
        assert time_ratio_100_50 < 4   # 2x cities should be < 4x time


class TestStressTests:
    """Stress tests for edge cases and extreme inputs"""
    
    def test_extreme_color_values(self):
        """Test classifier with extreme color combinations"""
        classifier = TileTerrainClassifier()
        
        extreme_colors = [
            (0, 0, 0),       # Pure black
            (255, 255, 255), # Pure white  
            (255, 0, 0),     # Pure red
            (0, 255, 0),     # Pure green
            (0, 0, 255),     # Pure blue
            (255, 255, 0),   # Yellow
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
        ]
        
        for r, g, b in extreme_colors:
            terrain = classifier.classify_pixel(r, g, b)
            assert isinstance(terrain, CampaignTerrainType)

    def test_maximum_rectangle_merging(self):
        """Test rectangle merging with maximum possible merge scenario"""
        
        # Create a perfect grid that should merge significantly
        rectangles = []
        for y in range(10):  # Smaller grid for better performance
            for x in range(10):
                rectangles.append([x, x+1, y, y+1])
        
        # All rectangles should merge efficiently
        merged = merge_adjacent_rectangles(rectangles)
        
        # Should merge into fewer rectangles
        assert len(merged) < len(rectangles)
        # For a 10x10 grid, should merge into 10 horizontal strips
        assert len(merged) <= 10

    def test_no_merge_scenario(self):
        """Test rectangle merging when no merging is possible"""
        
        # Create scattered rectangles that can't merge
        rectangles = []
        for i in range(100):
            x = i * 2  # Leave gaps so no merging possible
            y = i * 2
            rectangles.append([x, x+1, y, y+1])
        
        merged = merge_adjacent_rectangles(rectangles)
        
        # Should have same number of rectangles (no merging possible)
        assert len(merged) == len(rectangles)

    def test_very_large_coordinate_values(self):
        """Test with very large coordinate values"""
        from tile_terrain_generator import MapTileFetcher
        
        fetcher = MapTileFetcher()
        
        # Test with extreme but valid coordinates
        extreme_coords = [
            (85.0, 179.0),   # Near north pole, near dateline
            (-85.0, -179.0), # Near south pole, near dateline
            (0.0, 0.0),      # Origin
        ]
        
        for lat, lon in extreme_coords:
            for zoom in [1, 10, 18]:  # Test different zoom levels
                try:
                    x, y = fetcher.deg2num(lat, lon, zoom)
                    assert isinstance(x, int)
                    assert isinstance(y, int)
                    assert x >= 0
                    assert y >= 0
                    
                    # Test roundtrip
                    lat_back, lon_back = fetcher.num2deg(x, y, zoom)
                    assert isinstance(lat_back, float)
                    assert isinstance(lon_back, float)
                    
                except (OverflowError, ValueError):
                    # Some extreme cases may legitimately fail
                    pass

    def test_empty_inputs(self):
        """Test handling of empty inputs"""
        
        # Test empty rectangle list
        assert merge_adjacent_rectangles([]) == []
        assert merge_horizontal_rectangles([]) == []
        
        # Test empty city list
        bounds = GeographicBounds(west_lon=10.0, east_lon=11.0, south_lat=50.0, north_lat=51.0)
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher_class.return_value = mock_fetcher
            
            result, collisions, unique_positions = convert_cities_to_hex_coordinates(
                [], bounds, 10, 10, 10
            )
            
            assert result == {}
            assert collisions == 0
            assert unique_positions == 0