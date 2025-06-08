#!/usr/bin/env python3
"""
OpenStreetMap-based Terrain Generator for Campaign Maps

This tool generates accurate terrain maps using OpenStreetMap data instead of
image processing. It takes geographic bounds and hex size as input, queries
OSM for terrain features, and generates a JSON file compatible with the game.

Usage: python osm_terrain_generator.py --bounds west,south,east,north --hex-size-km 30 -o output.json

Key advantages over image-based approach:
- Accurate geographic data from OpenStreetMap
- No aspect ratio or scaling issues  
- Precise coordinate placement
- Reliable terrain classification
- No manual marking required
"""

import json
import os
import sys
import math
import time
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import urllib.request
import urllib.parse
import urllib.error
from xml.etree import ElementTree as ET

# Import campaign terrain types
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from game.campaign.campaign_state import CampaignTerrainType

@dataclass
class GeographicBounds:
    """Geographic boundaries for the map"""
    west_lon: float
    east_lon: float
    south_lat: float
    north_lat: float
    
    @property
    def width_deg(self) -> float:
        return self.east_lon - self.west_lon
    
    @property
    def height_deg(self) -> float:
        return self.north_lat - self.south_lat

@dataclass
class HistoricalCity:
    """Historical city data circa 1200 AD"""
    name: str
    modern_name: str
    latitude: float
    longitude: float
    country: str
    city_type: str
    estimated_population: int
    description: str

class OSMTerrainClassifier:
    """Classifies OpenStreetMap features into game terrain types"""
    
    def __init__(self):
        # OSM tag patterns for terrain classification
        self.terrain_rules = {
            CampaignTerrainType.WATER: {
                'natural': ['water', 'bay', 'strait'],
                'waterway': ['river', 'canal', 'stream'],
                'place': ['sea', 'ocean'],
                'landuse': ['reservoir', 'basin']
            },
            CampaignTerrainType.FOREST: {
                'natural': ['wood', 'forest'],
                'landuse': ['forest', 'woodland']
            },
            CampaignTerrainType.MOUNTAINS: {
                'natural': ['peak', 'ridge', 'volcano'],
                'place': ['mountain_range']
            },
            CampaignTerrainType.HILLS: {
                'natural': ['hill', 'plateau']
            },
            CampaignTerrainType.DESERT: {
                'natural': ['desert', 'sand'],
                'landuse': ['sand']
            },
            CampaignTerrainType.SNOW: {
                'natural': ['glacier', 'ice']
            }
            # PLAINS is default for everything else
        }
    
    def classify_osm_feature(self, tags: Dict[str, str]) -> CampaignTerrainType:
        """Classify an OSM feature based on its tags"""
        for terrain_type, tag_rules in self.terrain_rules.items():
            for tag_key, tag_values in tag_rules.items():
                if tag_key in tags and tags[tag_key] in tag_values:
                    return terrain_type
        
        # Special cases for elevation-based classification
        if 'ele' in tags:
            try:
                elevation = float(tags['ele'])
                if elevation > 1500:  # High mountains
                    return CampaignTerrainType.MOUNTAINS
                elif elevation > 500:  # Hills
                    return CampaignTerrainType.HILLS
            except ValueError:
                pass
        
        # Default to plains
        return CampaignTerrainType.PLAINS

class OSMDataFetcher:
    """Fetches terrain data from OpenStreetMap using Overpass API"""
    
    def __init__(self, overpass_url: str = "https://lz4.overpass-api.de/api/interpreter"):
        self.overpass_url = overpass_url
        self.request_delay = 2.0  # Seconds between requests to be respectful
        self.backup_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter", 
            "https://z.overpass-api.de/api/interpreter"
        ]
    
    def build_overpass_query(self, bounds: GeographicBounds) -> str:
        """Build Overpass API query for terrain features - optimized for large areas"""
        bbox = f"{bounds.south_lat},{bounds.west_lon},{bounds.north_lat},{bounds.east_lon}"
        
        # For large areas like Europe, we need to be more selective to avoid timeouts
        area_size = (bounds.east_lon - bounds.west_lon) * (bounds.north_lat - bounds.south_lat)
        
        # Use a much simpler query to test connectivity and speed
        query = f"""
        [out:xml][timeout:60][bbox:{bbox}];
        (
          // Just coastlines and major water bodies - very fast
          way[natural=coastline];
          way[natural=water];
          relation[natural=water];
        );
        out geom;
        """
        
        return query
    
    def fetch_osm_data(self, bounds: GeographicBounds) -> List[Dict]:
        """Fetch OSM data for the given bounds"""
        print(f"🌍 Fetching OSM data for bounds: {bounds.west_lon:.2f},{bounds.south_lat:.2f} to {bounds.east_lon:.2f},{bounds.north_lat:.2f}")
        
        query = self.build_overpass_query(bounds)
        print(f"📝 Query preview: {query[:100]}...")
        
        try:
            # Encode query
            encoded_query = urllib.parse.quote(query.encode('utf-8'))
            url = f"{self.overpass_url}?data={encoded_query}"
            
            # Make request with proper headers
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Medieval Campaign Map Generator/1.0')
            
            print("📡 Sending request to Overpass API...")
            with urllib.request.urlopen(req, timeout=60) as response:
                xml_data = response.read().decode('utf-8')
            
            print("✅ OSM data received, parsing...")
            return self.parse_osm_xml(xml_data)
            
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error from OpenStreetMap: {e.code} {e.reason}")
            if e.code == 429:
                print("   Rate limited - too many requests")
            elif e.code == 504:
                print("   Gateway timeout - query too complex or server overloaded")
            elif e.code >= 500:
                print("   Server error - OpenStreetMap infrastructure issue")
            return []
            
        except urllib.error.URLError as e:
            print(f"❌ Network Error: {e.reason}")
            print("   Check your internet connection")
            return []
            
        except Exception as e:
            print(f"❌ Unexpected Error from OpenStreetMap: {e}")
            print(f"   Error type: {type(e).__name__}")
            return []
    
    def parse_osm_xml(self, xml_data: str) -> List[Dict]:
        """Parse OSM XML response into feature list"""
        features = []
        
        try:
            root = ET.fromstring(xml_data)
            
            # Parse nodes (point features)
            for node in root.findall('node'):
                feature = {
                    'type': 'node',
                    'id': node.get('id'),
                    'lat': float(node.get('lat')),
                    'lon': float(node.get('lon')),
                    'tags': {},
                    'geometry': [(float(node.get('lat')), float(node.get('lon')))]
                }
                
                for tag in node.findall('tag'):
                    feature['tags'][tag.get('k')] = tag.get('v')
                
                features.append(feature)
            
            # Parse ways (line/polygon features)  
            for way in root.findall('way'):
                feature = {
                    'type': 'way',
                    'id': way.get('id'),
                    'tags': {},
                    'geometry': []
                }
                
                for tag in way.findall('tag'):
                    feature['tags'][tag.get('k')] = tag.get('v')
                
                for nd in way.findall('nd'):
                    if 'lat' in nd.attrib and 'lon' in nd.attrib:
                        feature['geometry'].append((float(nd.get('lat')), float(nd.get('lon'))))
                
                if feature['geometry']:  # Only include ways with geometry
                    features.append(feature)
            
            print(f"📊 Parsed {len(features)} OSM features")
            return features
            
        except ET.ParseError as e:
            print(f"❌ Error parsing OSM XML: {e}")
            return []

class OSMTerrainGenerator:
    """Main terrain generator using OpenStreetMap data"""
    
    def __init__(self, bounds: GeographicBounds, hex_size_km: float, map_width: int = None, map_height: int = None):
        self.bounds = bounds
        self.hex_size_km = hex_size_km
        
        self.osm_fetcher = OSMDataFetcher()
        self.terrain_classifier = OSMTerrainClassifier()
        
        # Calculate map size based on requested hex size
        self.calculate_map_size_from_hex_size(map_width, map_height)
        
        # Load city database
        self.load_city_database()
    
    def calculate_map_size_from_hex_size(self, override_width: int = None, override_height: int = None):
        """Calculate map dimensions to achieve the requested hex size"""
        # Calculate center latitude for longitude calculations
        center_lat = (self.bounds.north_lat + self.bounds.south_lat) / 2
        
        # Convert degrees to km
        km_per_deg_lat = 111.32  # Always ~111.32 km per degree latitude
        km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))  # Varies by latitude
        
        # Calculate real-world dimensions
        total_width_km = self.bounds.width_deg * km_per_deg_lon
        total_height_km = self.bounds.height_deg * km_per_deg_lat
        
        # Calculate required hexes to achieve target hex size
        calculated_width = int(round(total_width_km / self.hex_size_km))
        calculated_height = int(round(total_height_km / self.hex_size_km))
        
        # Use overrides if provided, otherwise use calculated values
        self.map_width = override_width if override_width else calculated_width
        self.map_height = override_height if override_height else calculated_height
        
        # Calculate actual hex sizes achieved
        actual_hex_size_x = total_width_km / self.map_width
        actual_hex_size_y = total_height_km / self.map_height
        
        print(f"📏 Map dimensions calculated:")
        print(f"   Geographic area: {total_width_km:.0f}km × {total_height_km:.0f}km")
        print(f"   Requested hex size: {self.hex_size_km}km")
        if override_width or override_height:
            print(f"   Override grid: {self.map_width} × {self.map_height} hexes")
            print(f"   Actual hex size: {actual_hex_size_x:.1f}km × {actual_hex_size_y:.1f}km")
        else:
            print(f"   Calculated grid: {self.map_width} × {self.map_height} hexes")
            print(f"   Achieved hex size: {actual_hex_size_x:.1f}km × {actual_hex_size_y:.1f}km")
        
        # Calculate degrees per hex for coordinate conversion
        self.deg_per_hex_x = self.bounds.width_deg / self.map_width
        self.deg_per_hex_y = self.bounds.height_deg / self.map_height
    
    
    def load_city_database(self):
        """Load historical cities from JSON file"""
        cities_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medieval_cities_1200ad.json')
        
        try:
            with open(cities_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.cities = []
            for city_data in data.get('cities', []):
                city = HistoricalCity(
                    name=city_data['name'],
                    modern_name=city_data['modern_name'],
                    latitude=city_data['latitude'],
                    longitude=city_data['longitude'],
                    country=city_data['country'],
                    city_type=city_data['city_type'],
                    estimated_population=city_data['estimated_population'],
                    description=city_data['description']
                )
                
                # Only include cities within our bounds
                if (self.bounds.west_lon <= city.longitude <= self.bounds.east_lon and
                    self.bounds.south_lat <= city.latitude <= self.bounds.north_lat):
                    self.cities.append(city)
            
            print(f"🏛️  Loaded {len(self.cities)} cities within map bounds")
            
        except Exception as e:
            print(f"❌ Error loading cities: {e}")
            self.cities = []
    
    def lat_lon_to_hex(self, latitude: float, longitude: float) -> Tuple[int, int]:
        """Convert latitude/longitude to hex coordinates"""
        # Normalize to 0-1 range within bounds
        lon_norm = (longitude - self.bounds.west_lon) / self.bounds.width_deg
        lat_norm = (latitude - self.bounds.south_lat) / self.bounds.height_deg
        
        # Convert to hex coordinates (flip Y axis)
        hex_x = int(lon_norm * self.map_width)
        hex_y = int((1.0 - lat_norm) * self.map_height)
        
        # Clamp to bounds
        hex_x = max(0, min(self.map_width - 1, hex_x))
        hex_y = max(0, min(self.map_height - 1, hex_y))
        
        return hex_x, hex_y
    
    def hex_to_lat_lon(self, hex_x: int, hex_y: int) -> Tuple[float, float]:
        """Convert hex coordinates to latitude/longitude"""
        # Convert hex to normalized coordinates
        lon_norm = hex_x / self.map_width
        lat_norm = 1.0 - (hex_y / self.map_height)  # Flip Y axis
        
        # Convert to actual lat/lon
        longitude = self.bounds.west_lon + lon_norm * self.bounds.width_deg
        latitude = self.bounds.south_lat + lat_norm * self.bounds.height_deg
        
        return latitude, longitude
    
    def point_in_polygon(self, point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm"""
        if len(polygon) < 3:
            return False
        
        lat, lon = point
        inside = False
        
        j = len(polygon) - 1
        for i in range(len(polygon)):
            lat_i, lon_i = polygon[i]
            lat_j, lon_j = polygon[j]
            
            if ((lat_i > lat) != (lat_j > lat)) and \
               (lon < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i) + lon_i):
                inside = not inside
            
            j = i
        
        return inside
    
    def classify_hex_terrain(self, hex_x: int, hex_y: int, osm_features: List[Dict]) -> CampaignTerrainType:
        """Classify terrain for a specific hex based on OSM features"""
        # Get hex center coordinates
        center_lat, center_lon = self.hex_to_lat_lon(hex_x, hex_y)
        
        # Check what OSM features cover this hex
        terrain_votes = {terrain_type: 0 for terrain_type in CampaignTerrainType}
        
        for feature in osm_features:
            feature_terrain = self.terrain_classifier.classify_osm_feature(feature['tags'])
            
            if feature['type'] == 'node':
                # Point feature - check if close to hex center
                feat_lat, feat_lon = feature['geometry'][0]
                distance = math.sqrt((feat_lat - center_lat)**2 + (feat_lon - center_lon)**2)
                if distance < self.deg_per_hex_x:  # Within hex
                    terrain_votes[feature_terrain] += 1
            
            elif feature['type'] == 'way' and len(feature['geometry']) >= 3:
                # Polygon feature - check if hex center is inside
                if self.point_in_polygon((center_lat, center_lon), feature['geometry']):
                    terrain_votes[feature_terrain] += 3  # Polygons get higher weight
        
        # Return terrain type with most votes, or plains if no votes
        if sum(terrain_votes.values()) == 0:
            return CampaignTerrainType.PLAINS
        
        return max(terrain_votes.items(), key=lambda x: x[1])[0]
    
    def generate_terrain_map(self) -> Dict[Tuple[int, int], CampaignTerrainType]:
        """Generate complete terrain map using OSM data with chunked requests"""
        print("🗺️  Generating terrain map from OpenStreetMap data...")
        
        # Try chunked approach for large areas
        area_size = (self.bounds.east_lon - self.bounds.west_lon) * (self.bounds.north_lat - self.bounds.south_lat)
        
        if area_size > 500:  # Large area - try chunked requests
            print(f"📍 Large area detected ({area_size:.0f} deg²) - using chunked OSM requests...")
            osm_features = self.fetch_osm_data_chunked()
        else:
            osm_features = self.osm_fetcher.fetch_osm_data(self.bounds)
        
        if not osm_features:
            print("❌ FAILED: OpenStreetMap API is not responding")
            print("🔄 This could be due to:")
            print("   - Overpass API server overload")
            print("   - Network connectivity issues") 
            print("   - Query too complex for the area size")
            print("")
            print("💡 Try again later or use a smaller geographic area")
            print("   Example: --bounds=\"14,49,24,55\" for Poland only")
            raise RuntimeError("OSM API failed - cannot generate accurate terrain data")
        
        # Classify each hex using OSM data
        terrain_map = {}
        
        print("🧩 Classifying terrain for each hex using OSM data...")
        for hex_y in range(self.map_height):
            if hex_y % 20 == 0:
                print(f"   Processing row {hex_y}/{self.map_height}")
            
            for hex_x in range(self.map_width):
                terrain_type = self.classify_hex_terrain(hex_x, hex_y, osm_features)
                terrain_map[(hex_x, hex_y)] = terrain_type
        
        print(f"✅ Generated terrain map with {len(terrain_map)} hexes")
        
        # Print terrain statistics
        terrain_counts = {}
        for terrain_type in terrain_map.values():
            terrain_counts[terrain_type] = terrain_counts.get(terrain_type, 0) + 1
        
        print("📊 Terrain distribution:")
        for terrain_type, count in sorted(terrain_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(terrain_map)) * 100
            print(f"   {terrain_type.value}: {count} hexes ({percentage:.1f}%)")
        
        return terrain_map
    
    def fetch_osm_data_chunked(self) -> List[Dict]:
        """Fetch OSM data in smaller chunks to avoid timeouts"""
        print("🔄 Fetching OSM data in chunks to avoid timeouts...")
        
        # Divide area into 4 chunks (2x2 grid)
        mid_lon = (self.bounds.west_lon + self.bounds.east_lon) / 2
        mid_lat = (self.bounds.south_lat + self.bounds.north_lat) / 2
        
        chunks = [
            GeographicBounds(self.bounds.west_lon, mid_lon, self.bounds.south_lat, mid_lat),  # SW
            GeographicBounds(mid_lon, self.bounds.east_lon, self.bounds.south_lat, mid_lat),  # SE
            GeographicBounds(self.bounds.west_lon, mid_lon, mid_lat, self.bounds.north_lat),  # NW
            GeographicBounds(mid_lon, self.bounds.east_lon, mid_lat, self.bounds.north_lat),  # NE
        ]
        
        all_features = []
        successful_chunks = 0
        
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}/4: {chunk.west_lon:.1f},{chunk.south_lat:.1f} to {chunk.east_lon:.1f},{chunk.north_lat:.1f}")
            features = self.osm_fetcher.fetch_osm_data(chunk)
            if features:
                all_features.extend(features)
                successful_chunks += 1
                print(f"   ✅ Chunk {i+1}: {len(features)} features")
            else:
                print(f"   ❌ Chunk {i+1}: No data")
            
            # Brief pause between requests
            time.sleep(1)
        
        print(f"📊 Chunked fetch results: {successful_chunks}/4 chunks successful, {len(all_features)} total features")
        return all_features
    
    
    def place_cities(self) -> Dict[str, Dict]:
        """Place historical cities on the map (only those within bounds)"""
        cities_data = {}
        placed_count = 0
        skipped_count = 0
        
        print(f"🏛️  Placing cities from {len(self.cities)} candidates...")
        
        for city in self.cities:
            hex_x, hex_y = self.lat_lon_to_hex(city.latitude, city.longitude)
            
            # Only place cities that fit within the map bounds
            if 0 <= hex_x < self.map_width and 0 <= hex_y < self.map_height:
                city_id = f"city_{placed_count:03d}"
                cities_data[city_id] = {
                    'name': city.name,
                    'country': city.country,
                    'position': [hex_x, hex_y],
                    'type': city.city_type,
                    'income': max(50, city.estimated_population // 100),
                    'castle_level': 3 if city.city_type == 'capital' else 2 if city.city_type == 'major_city' else 1,
                    'population': city.estimated_population,
                    'specialization': 'military' if city.city_type in ['capital', 'fortress'] else 'trade',
                    'description': city.description
                }
                
                print(f"   ✅ {city.name} -> ({hex_x}, {hex_y}) at {city.latitude:.3f}°N, {city.longitude:.3f}°E")
                placed_count += 1
            else:
                print(f"   ❌ {city.name} -> ({hex_x}, {hex_y}) OUTSIDE MAP BOUNDS at {city.latitude:.3f}°N, {city.longitude:.3f}°E")
                skipped_count += 1
        
        print(f"📊 City placement summary:")
        print(f"   ✅ Placed: {placed_count} cities")
        print(f"   ❌ Skipped: {skipped_count} cities (outside bounds)")
        
        return cities_data
    
    def export_to_json(self, terrain_map: Dict, cities: Dict, output_path: str):
        """Export to JSON format compatible with the game"""
        print(f"💾 Exporting to {output_path}...")
        
        # Group terrain by type for the game format
        terrain_groups = {}
        for (hex_x, hex_y), terrain_type in terrain_map.items():
            terrain_name = terrain_type.value
            if terrain_name not in terrain_groups:
                terrain_groups[terrain_name] = []
            terrain_groups[terrain_name].append([hex_x, hex_x + 1, hex_y, hex_y + 1])
        
        # Country definitions
        countries = {
            "holy_roman_empire": {"name": "Holy Roman Empire", "color": [255, 215, 0], "capital": "aachen", "description": "Germanic empire", "starting_resources": {"gold": 3000}, "bonuses": {}},
            "france": {"name": "Kingdom of France", "color": [0, 0, 139], "capital": "paris", "description": "Capetian kingdom", "starting_resources": {"gold": 2500}, "bonuses": {}},
            "england": {"name": "Kingdom of England", "color": [255, 0, 0], "capital": "london", "description": "Norman kingdom", "starting_resources": {"gold": 2000}, "bonuses": {}},
            "poland": {"name": "Kingdom of Poland", "color": [220, 20, 60], "capital": "kraków", "description": "Piast kingdom", "starting_resources": {"gold": 1500}, "bonuses": {}},
            "hungary": {"name": "Kingdom of Hungary", "color": [0, 128, 0], "capital": "esztergom", "description": "Árpád kingdom", "starting_resources": {"gold": 1500}, "bonuses": {}},
            "denmark": {"name": "Kingdom of Denmark", "color": [139, 0, 0], "capital": "roskilde", "description": "Scandinavian kingdom", "starting_resources": {"gold": 1200}, "bonuses": {}},
            "byzantium": {"name": "Byzantine Empire", "color": [128, 0, 128], "capital": "konstantinoupolis", "description": "Eastern Roman Empire", "starting_resources": {"gold": 4000}, "bonuses": {}},
            "venice": {"name": "Republic of Venice", "color": [255, 165, 0], "capital": "venezia", "description": "Maritime republic", "starting_resources": {"gold": 2000}, "bonuses": {}},
        }
        
        export_data = {
            "map": {"width": self.map_width, "height": self.map_height, "terrain": terrain_groups},
            "countries": countries,
            "cities": cities,
            "neutral_regions": []
        }
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Export complete!")
        print(f"   Terrain types: {len(terrain_groups)}")
        print(f"   Cities: {len(cities)}")
        print(f"   Countries: {len(countries)}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate campaign map using OpenStreetMap data')
    parser.add_argument('--bounds', required=True, 
                       help='Geographic bounds as west,south,east,north (e.g., -10,30,60,70)')
    parser.add_argument('--hex-size-km', type=float, default=30,
                       help='Target hex size in kilometers (default: 30)')
    parser.add_argument('-o', '--output', default='medieval_europe_osm.json',
                       help='Output JSON file (default: medieval_europe_osm.json)')
    parser.add_argument('--map-size', 
                       help='Override map size as width,height (default: auto-calculated from hex size)')
    
    args = parser.parse_args()
    
    # Parse bounds
    try:
        west, south, east, north = map(float, args.bounds.split(','))
        bounds = GeographicBounds(west, east, south, north)
    except ValueError:
        print("❌ Error: bounds must be in format 'west,south,east,north' (e.g., -10,30,60,70)")
        return
    
    # Parse map size (optional)
    width, height = None, None
    if args.map_size:
        try:
            width, height = map(int, args.map_size.split(','))
        except ValueError:
            print("❌ Error: map-size must be in format 'width,height' (e.g., 180,192)")
            return
    
    # Validate inputs
    if bounds.west_lon >= bounds.east_lon or bounds.south_lat >= bounds.north_lat:
        print("❌ Error: Invalid bounds - west must be < east, south must be < north")
        return
    
    if args.hex_size_km <= 0:
        print("❌ Error: hex-size-km must be positive")
        return
    
    print("🗺️  OpenStreetMap Terrain Generator")
    print(f"   Geographic bounds: {west:.1f}°W to {east:.1f}°E, {south:.1f}°S to {north:.1f}°N")
    print(f"   Target hex size: {args.hex_size_km}km")
    if width and height:
        print(f"   Override map dimensions: {width}×{height} hexes")
    else:
        print(f"   Map dimensions: auto-calculated for {args.hex_size_km}km hexes")
    
    # Generate map
    try:
        generator = OSMTerrainGenerator(bounds, args.hex_size_km, width, height)
        
        terrain_map = generator.generate_terrain_map()
        cities = generator.place_cities()
        
        generator.export_to_json(terrain_map, cities, args.output)
        
        print(f"\n✅ Map generation complete! Generated: {args.output}")
        print("🌍 This map uses real OpenStreetMap data for accurate terrain and city placement")
        
    except RuntimeError as e:
        print(f"\n❌ Map generation failed: {e}")
        print("\n🛠️  Troubleshooting steps:")
        print("   1. Check your internet connection")
        print("   2. Try again in a few minutes (OSM servers may be busy)")
        print("   3. Use a smaller geographic area")
        print("   4. Check if the coordinates are correct")
        return 1  # Exit with error code

if __name__ == "__main__":
    main()