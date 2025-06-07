import unittest
from tools.tile_terrain_generator import convert_cities_to_hex_coordinates, GeographicBounds

class TestTileTerrainGenerator(unittest.TestCase):
    def test_city_coordinate_mapping_matches_tile_bounds(self):
        """Cities should align with integer tile boundaries used for terrain."""
        bounds = GeographicBounds(-8, -4, 42, 45)
        cities = [
            {
                "name": "TestCity",
                "latitude": 43.5,
                "longitude": -6,
                "city_type": "city",
                "estimated_population": 1000,
                "description": "",
            }
        ]
        width = 30
        height = 30
        zoom = 8

        game_cities, collisions, unique = convert_cities_to_hex_coordinates(
            cities, bounds, width, height, zoom
        )

        self.assertEqual(game_cities["testcity"]["position"], [17, 15])
        self.assertEqual(collisions, 0)
        self.assertEqual(unique, 1)

if __name__ == "__main__":
    unittest.main()
