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

    # Two-track morale + cohesion system
    MORALE_CASUALTY_SCALE = 35.0
    MORALE_CASUALTY_RATIO_SCALE = 0.2
    COHESION_CASUALTY_SCALE = 50.0
    COHESION_CASUALTY_RATIO_SCALE = 0.15

    MORALE_SHOCK_MELEE = 2.0
    MORALE_SHOCK_RANGED = 1.0
    MORALE_SHOCK_SKIRMISH = 1.0
    MORALE_SHOCK_CHARGE = 8.0

    COHESION_SHOCK_MELEE = 6.0
    COHESION_SHOCK_RANGED = 1.0
    COHESION_SHOCK_SKIRMISH = 3.0
    COHESION_SHOCK_CHARGE = 12.0

    COHESION_FLANK_PENALTY = 12.0
    COHESION_REAR_PENALTY = 20.0

    ATTACK_FATIGUE_MORALE_PER_ATTACK = 2.0
    ATTACK_FATIGUE_COHESION_PER_ATTACK = 6.0

    MORALE_ATTACK_THRESHOLD = 50.0
    COHESION_ATTACK_THRESHOLD = 45.0

    MORALE_REGEN_BASE = 6.0
    MORALE_REGEN_ROUTING = 10.0
    COHESION_REGEN_BASE = 4.0
    COHESION_REGEN_ROUTING = 6.0
    REGEN_ENGAGED_MULTIPLIER = 0.3

    ROUTING_MORALE_THRESHOLD = 30.0
    ROUTING_COHESION_THRESHOLD = 35.0
    ROUTING_HARD_MORALE_THRESHOLD = 15.0
    ROUTING_HARD_COHESION_THRESHOLD = 20.0
    ROUTING_MORALE_WEIGHT = 2.0
    ROUTING_COHESION_WEIGHT = 2.5
    ROUTING_PRESSURE_BONUS = 10.0
    ROUTING_SHOCK_WEIGHT = 1.0
    ROUTING_MAX_CHANCE = 95.0

    RALLY_MORALE_THRESHOLD = 45.0
    RALLY_COHESION_THRESHOLD = 50.0
    RALLY_HIGH_MORALE_THRESHOLD = 60.0
    RALLY_HIGH_COHESION_THRESHOLD = 60.0
    RALLY_BASE_CHANCE = 0.6
    RALLY_HIGH_MORALE_CHANCE = 0.85
    RALLY_HIGH_COHESION_MULTIPLIER = 1.1
    RALLY_LOW_STRENGTH_MULTIPLIER = 0.6

    COHESION_DAMAGE_MIN_FACTOR = 0.5
    CHARGE_COHESION_MULTIPLIER = 1.5

    ZOC_MORALE_THRESHOLD = 25.0
    ZOC_COHESION_THRESHOLD = 40.0

    @classmethod
    def calculate_casualty_morale_loss(cls, casualty_ratio: float) -> float:
        """Calculate morale loss from casualty ratio."""
        if casualty_ratio < 0:
            raise ValueError("casualty_ratio must be non-negative")
        if cls.MORALE_CASUALTY_RATIO_SCALE <= 0:
            raise ValueError("MORALE_CASUALTY_RATIO_SCALE must be positive")
        import math
        return cls.MORALE_CASUALTY_SCALE * (1 - math.exp(-casualty_ratio / cls.MORALE_CASUALTY_RATIO_SCALE))

    @classmethod
    def calculate_casualty_cohesion_loss(cls, casualty_ratio: float) -> float:
        """Calculate cohesion loss from casualty ratio."""
        if casualty_ratio < 0:
            raise ValueError("casualty_ratio must be non-negative")
        if cls.COHESION_CASUALTY_RATIO_SCALE <= 0:
            raise ValueError("COHESION_CASUALTY_RATIO_SCALE must be positive")
        import math
        return cls.COHESION_CASUALTY_SCALE * (1 - math.exp(-casualty_ratio / cls.COHESION_CASUALTY_RATIO_SCALE))

    @classmethod
    def calculate_routing_chance(cls, morale: float, cohesion: float,
                                 pressure_bonus: float, shock_bonus: float) -> float:
        """Calculate routing chance from morale, cohesion, and battlefield pressure."""
        if morale is None or cohesion is None:
            raise ValueError("morale and cohesion are required for routing checks")
        if pressure_bonus is None or shock_bonus is None:
            raise ValueError("pressure_bonus and shock_bonus are required for routing checks")

        morale_deficit = max(0.0, cls.ROUTING_MORALE_THRESHOLD - morale)
        cohesion_deficit = max(0.0, cls.ROUTING_COHESION_THRESHOLD - cohesion)

        route_score = (
            morale_deficit * cls.ROUTING_MORALE_WEIGHT +
            cohesion_deficit * cls.ROUTING_COHESION_WEIGHT +
            pressure_bonus +
            shock_bonus * cls.ROUTING_SHOCK_WEIGHT
        )
        return min(cls.ROUTING_MAX_CHANCE, max(0.0, route_score))
    
    # Damage reduction when successfully breaking away
    BREAKAWAY_DAMAGE_REDUCTION = 0.5  # Take 50% less damage when breaking away
    
    # Opportunity attack damage multiplier when enemy breaks away
    OPPORTUNITY_ATTACK_MULTIPLIER = 0.7  # 70% of normal attack damage

    # Action point costs for standard attacks by unit class
    ATTACK_AP_COSTS = {
        "Warrior": 4,
        "Archer": 2,
        "Cavalry": 3,
        "Mage": 2,
    }

    @classmethod
    def get_attack_ap_cost(cls, unit_class_name: str) -> int:
        """Get the base AP cost for a standard attack"""
        return cls.ATTACK_AP_COSTS.get(unit_class_name, 3)
    
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
