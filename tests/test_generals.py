"""Test the general system"""
import unittest
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.general_factory import GeneralFactory
from game.components.generals import (
    InspireAbility, AggressiveAbility, RallyAbility, 
    BerserkAbility, LastStandAbility
)

class TestGeneralSystem(unittest.TestCase):
    """Test general abilities and bonuses"""
    
    def test_general_creation(self):
        """Test creating generals with factory"""
        general = GeneralFactory.create_general("Aggressive Commander")
        self.assertEqual(general.title, "Aggressive Commander")
        self.assertEqual(general.level, 1)
        self.assertTrue(len(general.abilities) > 0)
        
    def test_unit_with_generals(self):
        """Test units created with generals"""
        warrior = UnitFactory.create_warrior("Test Warrior", 5, 5)
        
        # Should have 2 starting generals
        self.assertEqual(len(warrior.generals.generals), 2)
        
        # Check passive bonuses are applied
        bonuses = warrior.generals.get_all_passive_bonuses(warrior)
        self.assertIn('morale_bonus', bonuses)
        self.assertIn('defense_bonus', bonuses)
        
    def test_morale_bonus(self):
        """Test morale bonuses from generals"""
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        
        # Add a general with Inspire ability
        general = GeneralFactory.create_custom_general(
            "Inspiring General",
            "Leader",
            [InspireAbility()],
            level=1
        )
        unit.generals.add_general(general)
        
        # Base morale is 100, Inspire adds 5, level 1 adds 1
        self.assertEqual(unit.morale, 100)  # Capped at 100
        
        # Lower morale to see bonus
        unit.stats.stats.morale = 80
        # With reduced bonuses: +5 Inspire, +1 per level
        self.assertEqual(unit.morale, 86)  # 80 + 5 (Inspire) + 1 (level)
        
    def test_damage_bonus(self):
        """Test damage bonuses from generals"""
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        
        # Add aggressive general
        general = GeneralFactory.create_custom_general(
            "Aggressive General",
            "Commander",
            [AggressiveAbility()],
            level=1
        )
        unit.generals.add_general(general)
        
        # Check damage modifier
        modifier = unit.get_damage_modifier()
        self.assertAlmostEqual(modifier, 1.17)  # 1.0 + 0.15 (Aggressive) + 0.02 (level)
        
    def test_movement_bonus(self):
        """Test movement bonus from Tactician"""
        from game.components.generals import TacticianAbility
        
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        base_range = unit.get_movement_range()
        
        # Add tactician general
        general = GeneralFactory.create_custom_general(
            "Tactician",
            "Strategist",
            [TacticianAbility()],
            level=1
        )
        unit.generals.add_general(general)
        
        # Check increased movement
        new_range = unit.get_movement_range()
        self.assertEqual(new_range, base_range + 1)
        
    def test_active_ability_rally(self):
        """Test Rally active ability"""
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        
        # Add general with Rally
        general = GeneralFactory.create_custom_general(
            "Rally Master",
            "Leader",
            [RallyAbility()],
            level=1
        )
        unit.generals.add_general(general)
        
        # Lower morale and set routing
        unit.stats.stats.morale = 50
        unit.is_routing = True
        
        # Get active abilities
        active_abilities = unit.generals.get_active_abilities(unit)
        self.assertEqual(len(active_abilities), 1)
        
        # Execute Rally
        gen, ability = active_abilities[0]
        result = unit.execute_general_ability(gen, ability)
        
        self.assertTrue(result['success'])
        self.assertEqual(unit.stats.stats.morale, 80)  # 50 + 30
        self.assertFalse(unit.is_routing)
        self.assertEqual(unit.will, 80)  # 100 - 20
        
    def test_berserk_ability(self):
        """Test Berserk active ability"""
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        
        # Add general with Berserk
        general = GeneralFactory.create_custom_general(
            "Berserker",
            "Lord",
            [BerserkAbility()],
            level=1
        )
        unit.generals.add_general(general)
        
        # Execute Berserk
        ability = general.abilities[0]
        result = unit.execute_general_ability(general, ability)
        
        self.assertTrue(result['success'])
        self.assertEqual(unit.temp_damage_multiplier, 2.0)
        self.assertEqual(unit.temp_vulnerability, 1.5)
        self.assertEqual(unit.will, 70)  # 100 - 30
        
    def test_last_stand_triggered(self):
        """Test Last Stand triggered ability"""
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        
        # Add general with Last Stand
        general = GeneralFactory.create_custom_general(
            "Last Stander",
            "Defender",
            [LastStandAbility()],
            level=1
        )
        unit.generals.add_general(general)
        
        # Not triggered when healthy
        reduction = unit.get_damage_reduction()
        self.assertAlmostEqual(reduction, 0.0)
        
        # Reduce soldiers below 25%
        unit.stats.stats.current_soldiers = 20  # 20% of 100
        
        # Now Last Stand should trigger
        reduction = unit.get_damage_reduction()
        self.assertAlmostEqual(reduction, 0.3)  # 30% reduction
        
    def test_general_experience(self):
        """Test general leveling"""
        general = GeneralFactory.create_random_general(level=1)
        
        # Gain experience
        self.assertFalse(general.gain_experience(50))  # Not enough to level
        self.assertEqual(general.experience, 50)
        
        # Level up
        self.assertTrue(general.gain_experience(60))  # Total 110, needs 100 for level 2
        self.assertEqual(general.level, 2)
        self.assertEqual(general.experience, 10)  # 110 - 100
        
    def test_max_generals(self):
        """Test max general limit"""
        unit = UnitFactory.create_unit("Test", KnightClass.WARRIOR, 0, 0, add_generals=False)
        
        # Add 3 generals (max)
        for i in range(3):
            general = GeneralFactory.create_random_general()
            self.assertTrue(unit.generals.add_general(general))
            
        # Try to add 4th
        general = GeneralFactory.create_random_general()
        self.assertFalse(unit.generals.add_general(general))
        self.assertEqual(len(unit.generals.generals), 3)

if __name__ == '__main__':
    unittest.main()