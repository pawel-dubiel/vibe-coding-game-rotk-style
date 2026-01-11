from enum import Enum

class UnitQuality(Enum):
    ELITE = "Elite"
    VETERAN = "Veteran"
    REGULAR = "Regular"
    MILITIA = "Militia"

    @property
    def max_rallies(self) -> int:
        """How many times can this unit rally from routing?"""
        if self == UnitQuality.ELITE:
            return 3
        elif self == UnitQuality.VETERAN:
            return 2
        elif self == UnitQuality.REGULAR:
            return 1
        return 0  # Militia never rally
        
    @property
    def rally_bonus(self) -> float:
        """Bonus probability to rally"""
        if self == UnitQuality.ELITE:
            return 0.3
        elif self == UnitQuality.VETERAN:
            return 0.15
        return 0.0

    @property
    def morale_modifier(self) -> float:
        """Base morale modifier"""
        if self == UnitQuality.ELITE:
            return 10.0
        elif self == UnitQuality.VETERAN:
            return 5.0
        elif self == UnitQuality.MILITIA:
            return -10.0
        return 0.0

    @property
    def cohesion_modifier(self) -> float:
        """Base cohesion modifier"""
        if self == UnitQuality.ELITE:
            return 10.0
        elif self == UnitQuality.VETERAN:
            return 5.0
        elif self == UnitQuality.MILITIA:
            return -10.0
        return 0.0
