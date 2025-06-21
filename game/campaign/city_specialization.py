from enum import Enum
from typing import Dict

class CitySpecialization(Enum):
    """City specialization types that affect various game mechanics."""
    
    TRADE = "trade"
    RELIGIOUS = "religious"
    MILITARY = "military"
    AGRICULTURAL = "agricultural"
    INDUSTRIAL = "industrial"
    PORT = "port"
    CAPITAL = "capital"
    
    # Alias for existing data compatibility
    AGRICULTURE = "agriculture"  # Maps to AGRICULTURAL
    
    @classmethod
    def get_growth_rate(cls, specialization: 'CitySpecialization') -> float:
        """Get base population growth rate for a specialization."""
        growth_rates = {
            cls.TRADE: 0.015,           # 1.5% growth (trade cities attract immigrants)
            cls.RELIGIOUS: 0.008,       # 0.8% growth (moderate growth)
            cls.MILITARY: 0.003,        # 0.3% growth (military cities have slower growth)
            cls.AGRICULTURAL: 0.012,    # 1.2% growth (food production supports growth)
            cls.AGRICULTURE: 0.012,     # Same as AGRICULTURAL for compatibility
            cls.INDUSTRIAL: 0.010,      # 1.0% growth (steady growth)
            cls.PORT: 0.013,           # 1.3% growth (ports attract trade and people)
            cls.CAPITAL: 0.009,        # 0.9% growth (balanced growth)
        }
        return growth_rates.get(specialization, 0.005)  # Default 0.5% growth
    
    @classmethod
    def from_string(cls, value: str) -> 'CitySpecialization':
        """Convert string to CitySpecialization enum, handling legacy values."""
        # Direct enum value mapping
        for spec in cls:
            if spec.value == value:
                return spec
        
        # Fallback for unknown values - return a default
        return cls.TRADE  # Default fallback
    
    @classmethod
    def get_income_modifier(cls, specialization: 'CitySpecialization') -> float:
        """Get income modifier for a specialization (for future use)."""
        income_modifiers = {
            cls.TRADE: 1.2,        # +20% income
            cls.PORT: 1.15,        # +15% income
            cls.CAPITAL: 1.1,      # +10% income
            cls.INDUSTRIAL: 1.05,  # +5% income
            cls.AGRICULTURAL: 0.9, # -10% income (focus on food, not gold)
            cls.AGRICULTURE: 0.9,  # Same as AGRICULTURAL
            cls.RELIGIOUS: 0.95,   # -5% income
            cls.MILITARY: 0.85,    # -15% income (military expenses)
        }
        return income_modifiers.get(specialization, 1.0)  # Default no modifier