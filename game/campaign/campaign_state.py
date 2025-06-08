import pygame
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from game.hex_utils import HexCoord, HexGrid
from game.hex_layout import HexLayout
# Campaign module has its own terrain system


class CampaignTerrainType(Enum):
    """Campaign-specific terrain types with elevation-based classification"""
    # Plains and lowlands (0-200m elevation)
    PLAINS = "plains"
    
    # Forest types
    FOREST = "forest"           # Regular forest
    DEEP_FOREST = "deep_forest" # Dense/deep forest
    
    # Elevation-based terrain
    HILLS = "hills"                   # 200-600m elevation
    MOUNTAINS = "mountains"           # 600-2500m elevation  
    HIGH_MOUNTAINS = "high_mountains" # 2500m+ elevation
    
    # Water bodies
    WATER = "water"
    DEEP_WATER = "deep_water"
    
    # Wetlands
    SWAMP = "swamps"  # Note: using plural to match existing JSON structure
    
    # Arid regions
    DESERT = "desert"
    
    # Cold regions
    SNOW = "snow"
    GLACIAL = "glacial"


@dataclass
class City:
    """Represents a city on the campaign map"""
    name: str
    country: str
    position: HexCoord
    city_type: str  # capital, city, port, etc.
    income: int
    castle_level: int
    population: int
    specialization: str  # military, trade, religious, etc.
    description: str
    
    
@dataclass
class Country:
    """Represents a country/faction"""
    id: str
    name: str
    color: tuple
    capital: str
    description: str
    starting_resources: Dict
    bonuses: Dict
    
    
@dataclass
class Army:
    """Represents an army on the campaign map"""
    id: str
    country: str
    position: HexCoord  # Hex coordinates
    knights: int
    archers: int
    cavalry: int
    movement_points: int
    max_movement_points: int = 3
    

class CampaignState:
    """Manages the campaign game state"""
    
    def __init__(self, player_country: str = None, country_data: Dict = None, map_file: str = None):
        self.player_country = player_country
        self.current_country = player_country
        self.turn_number = 1
        self.map_file = map_file
        
        # Data containers
        self.countries: Dict[str, Country] = {}
        self.cities: Dict[str, City] = {}
        self.armies: Dict[str, Army] = {}
        self.country_treasury: Dict[str, int] = {}
        self.neutral_regions: List[Dict] = []
        
        # Map data
        self.map_data: Dict = {}
        self.terrain_map: Dict[tuple, CampaignTerrainType] = {}
        
        # UI state
        self.selected_army: Optional[str] = None
        self.selected_city: Optional[str] = None
        
        # Map configuration (loaded from campaign data)
        self.map_width = 180  # Default - will be overridden by campaign data
        self.map_height = 192  # Default - will be overridden by campaign data
        self.hex_size_km = 30  # Default - will be overridden by campaign data
        self.hex_layout = HexLayout(hex_size=24)  # UI display size, not map scale
        
        # Load campaign data
        self._load_campaign_data()
        
        # Initialize campaign
        if player_country and country_data:
            self._init_campaign(player_country, country_data)
        else:
            # Default initialization for testing
            self._init_default_campaign()
    
    def _load_campaign_data(self):
        """Load campaign data from JSON file"""
        try:
            # Use specified map file or default
            if self.map_file:
                data_path = self.map_file
            else:
                # Try new data directory first, then fallback to old location
                data_dir_path = os.path.join(os.path.dirname(__file__), 'data', 'medieval_europe.json')
                old_path = os.path.join(os.path.dirname(__file__), 'medieval_europe.json')
                
                if os.path.exists(data_dir_path):
                    data_path = data_dir_path
                else:
                    data_path = old_path
            
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load map configuration
            self.map_data = data['map']
            self.map_width = self.map_data['width']
            self.map_height = self.map_data['height']
            self.hex_size_km = self.map_data.get('hex_size_km', 30)  # Default to 30km if not specified
            
            # Load terrain
            self._load_terrain_from_data(self.map_data['terrain'])
            
            # Load countries
            for country_id, country_info in data['countries'].items():
                self.countries[country_id] = Country(
                    id=country_id,
                    name=country_info['name'],
                    color=tuple(country_info['color']),
                    capital=country_info['capital'],
                    description=country_info['description'],
                    starting_resources=country_info['starting_resources'],
                    bonuses=country_info.get('bonuses', {})
                )
                
            # Load cities
            for city_id, city_info in data['cities'].items():
                self.cities[city_id] = City(
                    name=city_info['name'],
                    country=city_info['country'],
                    position=HexCoord(*city_info['position']),
                    city_type=city_info['type'],
                    income=city_info['income'],
                    castle_level=city_info['castle_level'],
                    population=city_info['population'],
                    specialization=city_info['specialization'],
                    description=city_info['description']
                )
                
            # Load neutral regions
            self.neutral_regions = data.get('neutral_regions', [])
            
            # If no cities loaded, create minimal data
            if not self.cities:
                print("Warning: No cities found in campaign data, creating minimal city data")
                self._create_minimal_cities()
            
        except FileNotFoundError:
            print("Warning: medieval_europe.json not found, using minimal data")
            self._create_minimal_data()
            
    def _load_terrain_from_data(self, terrain_data: Dict):
        """Load terrain from JSON data"""
        terrain_mapping = {
            'plains': CampaignTerrainType.PLAINS,
            'forest': CampaignTerrainType.FOREST,
            'forests': CampaignTerrainType.FOREST,  # Legacy support
            'deep_forest': CampaignTerrainType.DEEP_FOREST,
            'hills': CampaignTerrainType.HILLS,
            'mountains': CampaignTerrainType.MOUNTAINS,
            'high_mountains': CampaignTerrainType.HIGH_MOUNTAINS,
            'water': CampaignTerrainType.WATER,
            'deep_water': CampaignTerrainType.DEEP_WATER,
            'swamps': CampaignTerrainType.SWAMP,
            'desert': CampaignTerrainType.DESERT,
            'snow': CampaignTerrainType.SNOW,
            'glacial': CampaignTerrainType.GLACIAL
        }
        
        for terrain_name, regions in terrain_data.items():
            terrain_type = terrain_mapping.get(terrain_name, CampaignTerrainType.PLAINS)
            
            for region in regions:
                # Each region is [min_x, max_x, min_y, max_y]
                min_x, max_x, min_y, max_y = region
                for x in range(min_x, max_x):
                    for y in range(min_y, max_y):
                        if 0 <= x < self.map_width and 0 <= y < self.map_height:
                            self.terrain_map[(x, y)] = terrain_type
                            
    def _create_minimal_data(self):
        """Create minimal data for testing"""
        # Keep defaults already set in __init__
        # self.map_width = 180 (already set)
        # self.map_height = 192 (already set)
        # self.hex_size_km = 30 (already set)
        
        # Create a basic Poland entry
        self.countries['poland'] = Country(
            id='poland',
            name='Kingdom of Poland',
            color=(220, 20, 60),
            capital='krakow',
            description='A rising power in Eastern Europe',
            starting_resources={'gold': 1500, 'army_units': {'knights': 10, 'archers': 5, 'cavalry': 3}},
            bonuses={}
        )
        
        # Create basic Krakow (positioned in Central Europe)
        self._create_minimal_cities()
    
    def _create_minimal_cities(self):
        """Create minimal city data for testing"""
        # Create basic cities for each country if they don't exist
        for country_id, country in self.countries.items():
            if country.capital not in self.cities:
                # Position cities roughly in the center of the map
                center_x = self.map_width // 2
                center_y = self.map_height // 2
                
                # Offset each capital slightly to avoid overlap
                offset_x = hash(country_id) % 10 - 5
                offset_y = (hash(country_id) // 10) % 10 - 5
                
                self.cities[country.capital] = City(
                    name=country.capital.replace('_', ' ').title(),
                    country=country_id,
                    position=HexCoord(center_x + offset_x, center_y + offset_y),
                    city_type='capital',
                    income=200,
                    castle_level=3,
                    population=25000,
                    specialization='military',
                    description=f'Capital of {country.name}'
                )
            
    def _init_campaign(self, player_country: str, country_data: Dict):
        """Initialize campaign with selected country"""
        self.player_country = player_country
        self.current_country = player_country
        
        # Initialize treasury for all countries
        for country_id in self.countries.keys():
            country = self.countries[country_id]
            self.country_treasury[country_id] = country.starting_resources.get('gold', 1000)
            
        # Create starting armies for player and some AI countries
        self._create_starting_armies()
        
    def _init_default_campaign(self):
        """Initialize with default settings for testing"""
        if 'poland' in self.countries:
            self._init_campaign('poland', self.countries['poland'])
        
    def _create_starting_armies(self):
        """Create starting armies for countries"""
        for country_id, country in self.countries.items():
            if country.capital in self.cities:
                capital_city = self.cities[country.capital]
                army_units = country.starting_resources.get('army_units', {})
                
                # Create main army at capital
                army_id = f"{country_id}_main"
                self.armies[army_id] = Army(
                    id=army_id,
                    country=country_id,
                    position=capital_city.position,
                    knights=army_units.get('knights', 5),
                    archers=army_units.get('archers', 3),
                    cavalry=army_units.get('cavalry', 2),
                    movement_points=3
                )
        
    def get_country_cities(self, country: str) -> List[City]:
        """Get all cities owned by a country"""
        return [c for c in self.cities.values() if c.country == country]
        
    def get_country_armies(self, country: str) -> List[Army]:
        """Get all armies belonging to a country"""
        return [a for a in self.armies.values() if a.country == country]
        
    def end_turn(self):
        """Process end of turn"""
        # Collect income from cities for current country
        current_country_cities = self.get_country_cities(self.current_country)
        for city in current_country_cities:
            self.country_treasury[self.current_country] += city.income
                
        # Reset movement for current country's armies
        for army in self.armies.values():
            if army.country == self.current_country:
                army.movement_points = army.max_movement_points
            
        # Next country's turn (cycle through all countries)
        countries = list(self.countries.keys())
        current_index = countries.index(self.current_country)
        self.current_country = countries[(current_index + 1) % len(countries)]
        
        if current_index == len(countries) - 1:
            self.turn_number += 1
            
    def move_army(self, army_id: str, target_hex: HexCoord) -> bool:
        """Move an army to a new hex position"""
        if army_id not in self.armies:
            return False
            
        army = self.armies[army_id]
        
        # Calculate hex distance
        distance = army.position.distance_to(target_hex)
        
        if distance > army.movement_points:
            return False
            
        army.position = target_hex
        army.movement_points -= distance
        
        # Check if we're entering enemy city or meeting enemy army
        for city in self.cities.values():
            if city.position == target_hex:
                if city.country != army.country:
                    # Enemy city - trigger battle
                    return True
                    
        # Check for enemy armies at this position
        for other_army in self.armies.values():
            if (other_army.id != army_id and 
                other_army.position == target_hex and
                other_army.country != army.country):
                # Enemy army - trigger battle
                return True
                    
        return True
        
    def can_recruit(self, country: str, city_name: str) -> bool:
        """Check if country can recruit in a city"""
        if city_name not in self.cities:
            return False
            
        city = self.cities[city_name]
        return (city.country == country and 
                self.country_treasury[country] >= 100)  # Basic unit cost
                
    def recruit_units(self, country: str, city_name: str, 
                     knights: int = 0, archers: int = 0, cavalry: int = 0) -> bool:
        """Recruit new units in a city"""
        if not self.can_recruit(country, city_name):
            return False
            
        total_cost = knights * 100 + archers * 80 + cavalry * 150
        
        if self.country_treasury[country] < total_cost:
            return False
            
        city = self.cities[city_name]
        
        # Find existing army or create new one
        army_at_location = None
        for army in self.armies.values():
            if (army.country == country and 
                army.position == city.position):
                army_at_location = army
                break
                
        if army_at_location:
            army_at_location.knights += knights
            army_at_location.archers += archers
            army_at_location.cavalry += cavalry
        else:
            # Create new army
            army_id = f"{country}_army_{len(self.armies)}"
            self.armies[army_id] = Army(
                id=army_id,
                country=country,
                position=city.position,
                knights=knights,
                archers=archers,
                cavalry=cavalry,
                movement_points=3
            )
            
        self.country_treasury[country] -= total_cost
        return True