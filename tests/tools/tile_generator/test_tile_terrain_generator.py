import pytest
import json
import os
import sys
import math
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image

# Add the tools directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../tools'))
from tile_terrain_generator import (
    GeographicBounds, MapTileFetcher, TileTerrainClassifier, 
    load_medieval_cities, filter_cities_in_bounds, 
    convert_cities_to_hex_coordinates, merge_adjacent_rectangles,
    merge_horizontal_rectangles, export_to_json
)
from game.campaign.campaign_state import CampaignTerrainType


class TestGeographicBounds:
    def test_geographic_bounds_creation(self):
        bounds = GeographicBounds(west_lon=10.0, east_lon=20.0, south_lat=50.0, north_lat=60.0)
        assert bounds.west_lon == 10.0
        assert bounds.east_lon == 20.0
        assert bounds.south_lat == 50.0
        assert bounds.north_lat == 60.0

    def test_geographic_bounds_validation(self):
        # Test that bounds can be created with edge values
        bounds = GeographicBounds(west_lon=-180.0, east_lon=180.0, south_lat=-90.0, north_lat=90.0)
        assert bounds.west_lon == -180.0
        assert bounds.east_lon == 180.0


class TestMapTileFetcher:
    def setup_method(self):
        self.fetcher = MapTileFetcher()

    def test_deg2num_basic(self):
        # Test known coordinate conversion
        x, y = self.fetcher.deg2num(0.0, 0.0, 1)
        assert x == 1
        assert y == 1

    def test_deg2num_float_basic(self):
        # Test fractional coordinate conversion
        x, y = self.fetcher.deg2num_float(0.0, 0.0, 1)
        assert x == 1.0
        assert y == 1.0

    def test_num2deg_roundtrip(self):
        # Test coordinate conversion roundtrip
        lat, lon = 52.5, 13.4  # Berlin coordinates
        zoom = 10
        x, y = self.fetcher.deg2num(lat, lon, zoom)
        lat_back, lon_back = self.fetcher.num2deg(x, y, zoom)
        
        # Should be close due to rounding in tile numbers
        assert abs(lat - lat_back) < 1.0
        assert abs(lon - lon_back) < 1.0

    def test_deg2num_float_precision(self):
        # Test that float version gives more precision
        lat, lon = 52.5, 13.4
        zoom = 10
        x_int, y_int = self.fetcher.deg2num(lat, lon, zoom)
        x_float, y_float = self.fetcher.deg2num_float(lat, lon, zoom)
        
        # Float version should have fractional parts
        assert x_float != float(x_int) or y_float != float(y_int)

    @patch('urllib.request.urlopen')
    def test_fetch_tile_success(self, mock_urlopen):
        # Create a mock image
        img = Image.new('RGB', (256, 256), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.read.return_value = img_bytes.getvalue()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.fetcher.fetch_tile(100, 100, 10)
        assert result is not None
        assert isinstance(result, Image.Image)

    @patch('urllib.request.urlopen')
    def test_fetch_tile_failure_retry(self, mock_urlopen):
        # Mock all servers failing
        mock_urlopen.side_effect = Exception("Network error")
        
        result = self.fetcher.fetch_tile(100, 100, 10)
        assert result is None
        # Should try all servers
        assert mock_urlopen.call_count == len(self.fetcher.tile_servers)

    @patch.object(MapTileFetcher, 'fetch_tile')
    def test_fetch_area_tiles_success(self, mock_fetch_tile):
        # Mock successful tile fetching
        mock_tile = Image.new('RGB', (256, 256), color='green')
        mock_fetch_tile.return_value = mock_tile
        
        bounds = GeographicBounds(west_lon=10.0, east_lon=11.0, south_lat=50.0, north_lat=51.0)
        result = self.fetcher.fetch_area_tiles(bounds, zoom=8)
        
        assert result is not None
        assert isinstance(result, Image.Image)
        assert mock_fetch_tile.call_count > 0

    @patch.object(MapTileFetcher, 'fetch_tile')
    def test_fetch_area_tiles_insufficient_success(self, mock_fetch_tile):
        # Mock mostly failing tile fetches (less than 80% success)
        call_count = [0]
        def side_effect(*args):
            call_count[0] += 1
            return mock_tile if call_count[0] <= 2 else None  # Only first 2 succeed
        
        mock_tile = Image.new('RGB', (256, 256), color='green')
        mock_fetch_tile.side_effect = side_effect
        
        bounds = GeographicBounds(west_lon=10.0, east_lon=12.0, south_lat=50.0, north_lat=52.0)  # Large area
        result = self.fetcher.fetch_area_tiles(bounds, zoom=8)
        
        assert result is None  # Should fail due to insufficient tiles


class TestTileTerrainClassifier:
    def setup_method(self):
        self.classifier = TileTerrainClassifier()

    def test_color_distance(self):
        # Test color distance calculation
        distance = self.classifier.color_distance((255, 0, 0), (255, 0, 0))
        assert distance == 0.0
        
        distance = self.classifier.color_distance((255, 0, 0), (0, 255, 0))
        assert distance > 0

    def test_classify_pixel_water(self):
        # Test water classification
        terrain = self.classifier.classify_pixel(100, 150, 255)  # Blue dominant
        assert terrain == CampaignTerrainType.WATER

    def test_classify_pixel_forest(self):
        # Test forest classification
        terrain = self.classifier.classify_pixel(100, 180, 100)  # Green dominant, not too bright
        assert terrain == CampaignTerrainType.FOREST

    def test_classify_pixel_snow(self):
        # Test snow classification
        terrain = self.classifier.classify_pixel(250, 250, 250)  # Very bright white
        assert terrain == CampaignTerrainType.SNOW

    def test_classify_pixel_desert(self):
        # Test desert classification  
        terrain = self.classifier.classify_pixel(220, 200, 160)  # Yellow-ish bright
        assert terrain == CampaignTerrainType.DESERT

    def test_classify_pixel_mountains(self):
        # Test mountain classification
        terrain = self.classifier.classify_pixel(150, 130, 110)  # Brown-ish, medium dark
        assert terrain == CampaignTerrainType.MOUNTAINS

    def test_classify_pixel_hills(self):
        # Test hills classification - using colors that fall into hills range
        # Need color that doesn't match any predefined colors and falls into hills logic
        terrain = self.classifier.classify_pixel(125, 125, 125)  # Medium brightness, balanced, no match to predefined
        assert terrain == CampaignTerrainType.HILLS

    def test_classify_pixel_plains_default(self):
        # Test plains as default
        terrain = self.classifier.classify_pixel(100, 100, 100)  # Low brightness
        assert terrain == CampaignTerrainType.PLAINS

    def test_terrain_colors_exist(self):
        # Test that terrain color definitions exist
        assert CampaignTerrainType.WATER in self.classifier.terrain_colors
        assert CampaignTerrainType.FOREST in self.classifier.terrain_colors
        assert len(self.classifier.terrain_colors[CampaignTerrainType.WATER]) > 0


class TestMedievalCityFunctions:
    def test_load_medieval_cities_success(self, tmp_path):
        # Create a temporary cities file
        cities_data = {
            "cities": [
                {"name": "Test City", "latitude": 52.5, "longitude": 13.4, "country": "test"}
            ]
        }
        cities_file = tmp_path / "cities.json"
        cities_file.write_text(json.dumps(cities_data))
        
        result = load_medieval_cities(str(cities_file))
        assert len(result) == 1
        assert result[0]["name"] == "Test City"

    def test_load_medieval_cities_file_not_found(self):
        result = load_medieval_cities("nonexistent_file.json")
        assert result == []

    def test_load_medieval_cities_invalid_json(self, tmp_path):
        # Create a file with invalid JSON
        cities_file = tmp_path / "invalid.json"
        cities_file.write_text("invalid json content")
        
        result = load_medieval_cities(str(cities_file))
        assert result == []

    def test_filter_cities_in_bounds(self):
        cities = [
            {"name": "Inside", "latitude": 52.0, "longitude": 13.0},
            {"name": "Outside", "latitude": 60.0, "longitude": 20.0},
            {"name": "No coords", "name": "NoCoords"}
        ]
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        result = filter_cities_in_bounds(cities, bounds)
        assert len(result) == 1
        assert result[0]["name"] == "Inside"

    def test_filter_cities_edge_cases(self):
        cities = [
            {"name": "Edge West", "latitude": 52.0, "longitude": 10.0},  # On boundary
            {"name": "Edge North", "latitude": 55.0, "longitude": 13.0},  # On boundary
            {"name": "Missing lat", "longitude": 13.0},
            {"name": "Missing lon", "latitude": 52.0}
        ]
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        result = filter_cities_in_bounds(cities, bounds)
        assert len(result) == 2  # Only the edge cases with complete coords


class TestRectangleMerging:
    def test_merge_horizontal_rectangles_adjacent(self):
        # Test merging horizontally adjacent rectangles
        rectangles = [
            [0, 1, 0, 1],  # First rectangle
            [1, 2, 0, 1],  # Adjacent rectangle
        ]
        result = merge_horizontal_rectangles(rectangles)
        assert len(result) == 1
        assert result[0] == [0, 2, 0, 1]  # Merged rectangle

    def test_merge_horizontal_rectangles_non_adjacent(self):
        # Test non-adjacent rectangles don't merge
        rectangles = [
            [0, 1, 0, 1],
            [2, 3, 0, 1],  # Gap between rectangles
        ]
        result = merge_horizontal_rectangles(rectangles)
        assert len(result) == 2

    def test_merge_horizontal_rectangles_different_heights(self):
        # Test rectangles with different heights don't merge
        rectangles = [
            [0, 1, 0, 1],
            [1, 2, 0, 2],  # Different height
        ]
        result = merge_horizontal_rectangles(rectangles)
        assert len(result) == 2

    def test_merge_adjacent_rectangles_complex(self):
        # Test complex merging scenario
        rectangles = [
            [0, 1, 0, 1],  # Row 0
            [1, 2, 0, 1],  # Row 0, adjacent
            [0, 1, 1, 2],  # Row 1
            [2, 3, 1, 2],  # Row 1, non-adjacent
        ]
        result = merge_adjacent_rectangles(rectangles)
        # Should merge the first two rectangles in row 0
        assert any(rect == [0, 2, 0, 1] for rect in result)

    def test_merge_adjacent_rectangles_empty(self):
        result = merge_adjacent_rectangles([])
        assert result == []

    def test_merge_horizontal_rectangles_empty(self):
        result = merge_horizontal_rectangles([])
        assert result == []


class TestExportToJson:
    def test_export_to_json_basic(self, tmp_path):
        # Create basic terrain map
        terrain_map = {
            (0, 0): CampaignTerrainType.PLAINS,
            (1, 0): CampaignTerrainType.FOREST,
            (0, 1): CampaignTerrainType.WATER,
        }
        
        output_file = tmp_path / "test_export.json"
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        # Mock the cities file loading
        with patch('tile_terrain_generator.load_medieval_cities') as mock_load:
            mock_load.return_value = []
            
            export_to_json(terrain_map, 2, 2, 30.0, str(output_file), bounds)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert "map" in data
        assert "countries" in data
        assert "cities" in data
        assert data["map"]["width"] == 2
        assert data["map"]["height"] == 2
        assert data["map"]["hex_size_km"] == 30.0

    def test_export_to_json_terrain_groups(self, tmp_path):
        # Test that terrain is properly grouped
        terrain_map = {
            (0, 0): CampaignTerrainType.FOREST,
            (1, 0): CampaignTerrainType.FOREST,
            (0, 1): CampaignTerrainType.WATER,
        }
        
        output_file = tmp_path / "test_terrain_groups.json"
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        with patch('tile_terrain_generator.load_medieval_cities') as mock_load:
            mock_load.return_value = []
            
            export_to_json(terrain_map, 2, 2, 30.0, str(output_file), bounds)
        
        with open(output_file) as f:
            data = json.load(f)
        
        terrain_groups = data["map"]["terrain"]
        assert "forest" in terrain_groups
        assert "water" in terrain_groups
        assert len(terrain_groups["forest"]) >= 1  # Should have forest rectangles
        assert len(terrain_groups["water"]) >= 1   # Should have water rectangles


class TestCoordinateConversions:
    def setup_method(self):
        self.bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        self.cities = [
            {
                "name": "Test City",
                "latitude": 52.5,
                "longitude": 12.5,
                "city_type": "medium_city",
                "estimated_population": 10000,
                "description": "Test city description",
                "country": "test_country"
            }
        ]

    @patch('tile_terrain_generator.MapTileFetcher')
    def test_convert_cities_to_hex_coordinates_basic(self, mock_fetcher_class):
        # Mock the fetcher methods
        mock_fetcher = Mock()
        # Mock all the calls that advanced_coordinate_mapping will make
        mock_fetcher.deg2num_float.side_effect = [
            (100.5, 200.5),  # city coordinates
            (10.0, 50.0),    # bounds.south_lat, bounds.west_lon
            (15.0, 55.0),    # bounds.north_lat, bounds.east_lon
        ]
        mock_fetcher.deg2num.side_effect = [
            (10, 50),  # bounds.south_lat, bounds.west_lon
            (15, 55),  # bounds.north_lat, bounds.east_lon
        ]
        mock_fetcher_class.return_value = mock_fetcher
        
        result, collisions, unique_pos = convert_cities_to_hex_coordinates(
            self.cities, self.bounds, 10, 10, 10
        )
        
        assert len(result) == 1
        assert "test_city" in result
        assert isinstance(result["test_city"]["position"], list)
        assert len(result["test_city"]["position"]) == 2

    def test_convert_cities_collision_detection(self):
        # Create cities that would map to same hex
        cities_with_collision = [
            {
                "name": "City A",
                "latitude": 52.5,
                "longitude": 12.5,
                "city_type": "capital",
                "estimated_population": 50000,
                "description": "Capital city",
                "country": "test"
            },
            {
                "name": "City B", 
                "latitude": 52.5,
                "longitude": 12.5,  # Same coordinates
                "city_type": "medium_city",
                "estimated_population": 10000,
                "description": "Medium city",
                "country": "test"
            }
        ]
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            # Make both cities map to same hex - need to provide enough mock responses
            mock_fetcher.deg2num_float.side_effect = [
                (5.0, 5.0),    # first city
                (10.0, 50.0),  # bounds for first city
                (15.0, 55.0),  # bounds for first city
                (5.0, 5.0),    # second city (same position)
                (10.0, 50.0),  # bounds for second city
                (15.0, 55.0),  # bounds for second city
            ]
            mock_fetcher.deg2num.side_effect = [
                (10, 50), (15, 55),  # bounds for first city
                (10, 50), (15, 55),  # bounds for second city
            ]
            mock_fetcher_class.return_value = mock_fetcher
            
            result, collisions, unique_pos = convert_cities_to_hex_coordinates(
                cities_with_collision, self.bounds, 10, 10, 10
            )
            
            assert len(result) == 2  # Both cities should be placed
            assert collisions >= 1    # Should detect collision
            assert unique_pos == 2    # Should resolve to different positions

    def test_city_income_calculation(self):
        # Test different city types generate appropriate income
        test_cities = [
            {"name": "Capital", "latitude": 52.0, "longitude": 12.0, "city_type": "capital", "estimated_population": 100000, "description": "", "country": "test"},
            {"name": "Small", "latitude": 52.1, "longitude": 12.1, "city_type": "small_city", "estimated_population": 5000, "description": "", "country": "test"}
        ]
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.deg2num_float.side_effect = [
                (5.0, 5.0),    # first city
                (10.0, 50.0),  # bounds
                (15.0, 55.0),  # bounds
                (6.0, 6.0),    # second city
                (10.0, 50.0),  # bounds
                (15.0, 55.0),  # bounds
            ]
            mock_fetcher.deg2num.side_effect = [
                (10, 50), (15, 55),  # bounds for first city
                (10, 50), (15, 55),  # bounds for second city
            ]
            mock_fetcher_class.return_value = mock_fetcher
            
            result, _, _ = convert_cities_to_hex_coordinates(test_cities, self.bounds, 10, 10, 10)
            
            capital_income = result["capital"]["income"]
            small_income = result["small"]["income"]
            
            assert capital_income > small_income  # Capital should have higher income

    def test_city_specialization_detection(self):
        # Test specialization based on description
        test_cities = [
            {"name": "Port", "latitude": 52.0, "longitude": 12.0, "city_type": "port", "estimated_population": 20000, "description": "Major trading port", "country": "test"},
            {"name": "University", "latitude": 52.1, "longitude": 12.1, "city_type": "medium_city", "estimated_population": 15000, "description": "University town", "country": "test"}
        ]
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.deg2num_float.side_effect = [
                (5.0, 5.0),    # first city
                (10.0, 50.0),  # bounds
                (15.0, 55.0),  # bounds
                (6.0, 6.0),    # second city
                (10.0, 50.0),  # bounds
                (15.0, 55.0),  # bounds
            ]
            mock_fetcher.deg2num.side_effect = [
                (10, 50), (15, 55),  # bounds for first city
                (10, 50), (15, 55),  # bounds for second city
            ]
            mock_fetcher_class.return_value = mock_fetcher
            
            result, _, _ = convert_cities_to_hex_coordinates(test_cities, self.bounds, 10, 10, 10)
            
            assert result["port"]["specialization"] == "trade"
            assert result["university"]["specialization"] == "education"


class TestIntegrationScenarios:
    def test_water_city_relocation(self):
        # Test that cities on water get relocated to nearby land
        terrain_map = {
            (5, 5): CampaignTerrainType.WATER,   # City would be placed here
            (5, 6): CampaignTerrainType.PLAINS,  # Nearby land
        }
        
        cities = [{
            "name": "Coastal City",
            "latitude": 52.0,
            "longitude": 12.0,
            "city_type": "port",
            "estimated_population": 15000,
            "description": "Port city",
            "country": "test"
        }]
        
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        with patch('tile_terrain_generator.MapTileFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.deg2num_float.return_value = (5.0, 5.0)
            mock_fetcher.deg2num.return_value = (5, 5)
            mock_fetcher_class.return_value = mock_fetcher
            
            result, _, _ = convert_cities_to_hex_coordinates(
                cities, bounds, 10, 10, 10, terrain_map
            )
            
            # City should be moved to land
            city_pos = result["coastal_city"]["position"]
            assert terrain_map.get((city_pos[0], city_pos[1])) != CampaignTerrainType.WATER

    def test_full_workflow_mock(self):
        # Test a complete workflow with mocked external dependencies
        bounds = GeographicBounds(west_lon=10.0, east_lon=15.0, south_lat=50.0, north_lat=55.0)
        
        # Mock image
        with patch('PIL.Image.open') as mock_image_open:
            mock_image = Mock()
            mock_image.size = (512, 512)
            mock_image.getpixel.return_value = (100, 150, 100)  # Forest-like color
            mock_image_open.return_value = mock_image
            
            # Mock fetcher
            fetcher = MapTileFetcher()
            classifier = TileTerrainClassifier()
            
            # Test coordinate conversions work end-to-end
            x, y = fetcher.deg2num(52.5, 13.4, 10)
            assert isinstance(x, int)
            assert isinstance(y, int)
            
            # Test classification
            terrain = classifier.classify_pixel(100, 150, 100)
            assert isinstance(terrain, CampaignTerrainType)