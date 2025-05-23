"""Factory for creating generals with various ability combinations"""
import random
from typing import List
from game.components.generals import (
    General, GeneralAbility,
    # Passive abilities
    InspireAbility, TacticianAbility, VeteranAbility, AggressiveAbility,
    # Active abilities
    RallyAbility, BerserkAbility,
    # Triggered abilities
    LastStandAbility, CounterchargeAbility
)

class GeneralTemplate:
    """Template for creating generals of specific types"""
    
    def __init__(self, archetype: str, ability_pool: List[GeneralAbility]):
        self.archetype = archetype
        self.ability_pool = ability_pool

# Define general archetypes
GENERAL_ARCHETYPES = {
    "Inspiring Leader": GeneralTemplate(
        "Inspiring Leader",
        [InspireAbility(), RallyAbility(), VeteranAbility()]
    ),
    "Tactical Genius": GeneralTemplate(
        "Tactical Genius", 
        [TacticianAbility(), VeteranAbility(), LastStandAbility()]
    ),
    "Aggressive Commander": GeneralTemplate(
        "Aggressive Commander",
        [AggressiveAbility(), BerserkAbility(), CounterchargeAbility()]
    ),
    "Defensive Master": GeneralTemplate(
        "Defensive Master",
        [VeteranAbility(), LastStandAbility(), CounterchargeAbility()]
    ),
    "Veteran Officer": GeneralTemplate(
        "Veteran Officer",
        [VeteranAbility(), InspireAbility(), LastStandAbility()]
    ),
    "Cavalry Expert": GeneralTemplate(
        "Cavalry Expert",
        [TacticianAbility(), AggressiveAbility(), CounterchargeAbility()]
    ),
    "Berserker Lord": GeneralTemplate(
        "Berserker Lord",
        [BerserkAbility(), AggressiveAbility(), LastStandAbility()]
    )
}

# Name pools for generating general names
FIRST_NAMES = [
    "Marcus", "Julius", "Gaius", "Alexander", "Leonidas", "Hannibal",
    "Scipio", "Augustus", "Trajan", "Constantine", "Belisarius", "Arthur",
    "Roland", "Charlemagne", "William", "Richard", "Edward", "Henry",
    "Frederick", "Gustav", "Napoleon", "Wellington", "Grant", "Lee"
]

EPITHETS = [
    "the Bold", "the Wise", "the Fierce", "the Unyielding", "the Swift",
    "the Hammer", "the Shield", "the Strategist", "the Brave", "the Just",
    "Ironside", "Lionheart", "the Great", "the Conqueror", "the Defender",
    "the Steady", "the Cunning", "the Fearless", "the Veteran", "the Young"
]

class GeneralFactory:
    """Factory for creating generals"""
    
    @staticmethod
    def create_general(archetype: str = None, name: str = None, level: int = 1) -> General:
        """Create a general of the specified archetype"""
        
        # Choose random archetype if not specified
        if archetype is None:
            archetype = random.choice(list(GENERAL_ARCHETYPES.keys()))
            
        # Generate name if not specified
        if name is None:
            name = GeneralFactory.generate_name()
            
        # Get template
        template = GENERAL_ARCHETYPES.get(archetype)
        if template is None:
            # Fallback to basic general
            template = GeneralTemplate("Basic", [InspireAbility()])
            
        # Create general with abilities from template
        general = General(
            name=name,
            title=archetype,
            abilities=template.ability_pool.copy(),
            level=level
        )
        
        return general
        
    @staticmethod
    def generate_name() -> str:
        """Generate a random general name"""
        first_name = random.choice(FIRST_NAMES)
        if random.random() < 0.5:  # 50% chance of epithet
            epithet = random.choice(EPITHETS)
            return f"{first_name} {epithet}"
        return first_name
        
    @staticmethod
    def create_custom_general(name: str, title: str, abilities: List[GeneralAbility], level: int = 1) -> General:
        """Create a custom general with specific abilities"""
        return General(
            name=name,
            title=title,
            abilities=abilities,
            level=level
        )
        
    @staticmethod
    def create_random_general(level: int = 1) -> General:
        """Create a completely random general"""
        name = GeneralFactory.generate_name()
        
        # Pick 2-3 random abilities
        all_abilities = [
            InspireAbility(), TacticianAbility(), VeteranAbility(), AggressiveAbility(),
            RallyAbility(), BerserkAbility(), LastStandAbility(), CounterchargeAbility()
        ]
        
        num_abilities = random.randint(2, 3)
        abilities = random.sample(all_abilities, num_abilities)
        
        # Generate title based on abilities
        title = GeneralFactory._generate_title_from_abilities(abilities)
        
        return General(
            name=name,
            title=title,
            abilities=abilities,
            level=level
        )
        
    @staticmethod
    def _generate_title_from_abilities(abilities: List[GeneralAbility]) -> str:
        """Generate a title based on abilities"""
        ability_names = [a.name for a in abilities]
        
        if "Inspire" in ability_names and "Rally" in ability_names:
            return "Inspiring Leader"
        elif "Aggressive" in ability_names and "Berserk" in ability_names:
            return "Berserker Lord"
        elif "Veteran" in ability_names and "Last Stand" in ability_names:
            return "Grizzled Veteran"
        elif "Tactician" in ability_names:
            return "Master Tactician"
        elif "Aggressive" in ability_names:
            return "Aggressive Commander"
        elif "Veteran" in ability_names:
            return "Veteran Officer"
        else:
            return "Field Commander"
            
    @staticmethod
    def create_starting_generals_for_unit(unit_class: str) -> List[General]:
        """Create appropriate starting generals for a unit type"""
        from game.entities.knight import KnightClass
        
        if unit_class == KnightClass.CAVALRY:
            return [
                GeneralFactory.create_general("Cavalry Expert"),
                GeneralFactory.create_general("Aggressive Commander")
            ]
        elif unit_class == KnightClass.WARRIOR:
            return [
                GeneralFactory.create_general("Defensive Master"),
                GeneralFactory.create_general("Veteran Officer")
            ]
        elif unit_class == KnightClass.ARCHER:
            return [
                GeneralFactory.create_general("Tactical Genius"),
                GeneralFactory.create_general("Veteran Officer")
            ]
        elif unit_class == KnightClass.MAGE:
            return [
                GeneralFactory.create_general("Tactical Genius"),
                GeneralFactory.create_general("Inspiring Leader")
            ]
        else:
            return [GeneralFactory.create_random_general()]