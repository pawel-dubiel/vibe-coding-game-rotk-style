"""Combat configuration with meaningful variable names for magic numbers"""

class CombatConfig:
    """Configuration class for all combat-related constants"""
    
    # Unit weight classifications
    HEAVY_UNITS = ["Warrior", "Cavalry"]  # Units that are considered heavy
    LIGHT_UNITS = ["Archer", "Mage"]      # Units that are considered light
    
    # Breakaway chances (as percentages)
    LIGHT_VS_HEAVY_BREAKAWAY_CHANCE = 100  # Light units can always break from heavy units
    LIGHT_VS_LIGHT_BREAKAWAY_CHANCE = 50   # 50% chance for light vs light
    HEAVY_VS_HEAVY_BREAKAWAY_CHANCE = 0    # Heavy units cannot break from each other
    HEAVY_VS_LIGHT_BREAKAWAY_CHANCE = 0    # Heavy units don't break from light units
    
    # Action point costs for breakaway attempts
    BREAKAWAY_AP_COST = 2
    
    # Minimum action points required to attempt breakaway
    MIN_AP_FOR_BREAKAWAY = 2
    
    # Morale loss from failed breakaway attempt
    FAILED_BREAKAWAY_MORALE_LOSS = 10
    
    # Damage reduction when successfully breaking away
    BREAKAWAY_DAMAGE_REDUCTION = 0.5  # Take 50% less damage when breaking away
    
    # Opportunity attack damage multiplier when enemy breaks away
    OPPORTUNITY_ATTACK_MULTIPLIER = 0.7  # 70% of normal attack damage
    
    @classmethod
    def is_heavy_unit(cls, unit_class_name: str) -> bool:
        """Check if a unit class is considered heavy"""
        return unit_class_name in cls.HEAVY_UNITS
    
    @classmethod
    def is_light_unit(cls, unit_class_name: str) -> bool:
        """Check if a unit class is considered light"""
        return unit_class_name in cls.LIGHT_UNITS
    
    @classmethod
    def get_breakaway_chance(cls, attacker_class: str, defender_class: str) -> int:
        """Get the breakaway chance percentage for defender against attacker"""
        defender_is_heavy = cls.is_heavy_unit(defender_class)
        attacker_is_heavy = cls.is_heavy_unit(attacker_class)
        
        if not defender_is_heavy and attacker_is_heavy:
            # Light vs Heavy
            return cls.LIGHT_VS_HEAVY_BREAKAWAY_CHANCE
        elif not defender_is_heavy and not attacker_is_heavy:
            # Light vs Light
            return cls.LIGHT_VS_LIGHT_BREAKAWAY_CHANCE
        elif defender_is_heavy and attacker_is_heavy:
            # Heavy vs Heavy
            return cls.HEAVY_VS_HEAVY_BREAKAWAY_CHANCE
        else:
            # Heavy vs Light
            return cls.HEAVY_VS_LIGHT_BREAKAWAY_CHANCE