"""Tests for general display functionality"""
import pygame
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.general_factory import GeneralFactory

# Initialize pygame for tests
pygame.init()


class TestGeneralDisplay:
    """Test showing generals in info panel"""
    
    def test_unit_has_generals_property(self):
        """Test that units have a generals property"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        assert hasattr(unit, 'generals')
        assert unit.generals is not None
        assert unit.generals.generals == []
    
    def test_general_can_be_attached_to_unit(self):
        """Test attaching generals to units"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Create and attach a general
        general = GeneralFactory.create_general("Veteran Officer")
        result = unit.generals.add_general(general)
        
        assert result is True
        assert len(unit.generals.generals) == 1
        # The general name should be a string
        assert isinstance(unit.generals.generals[0].name, str)
        assert unit.generals.generals[0].title == "Veteran Officer"
    
    def test_multiple_generals_can_be_attached(self):
        """Test attaching multiple generals to a unit"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Create and attach multiple generals
        general1 = GeneralFactory.create_general("Veteran Officer")
        general2 = GeneralFactory.create_general("Tactical Genius")
        
        result1 = unit.generals.add_general(general1)
        result2 = unit.generals.add_general(general2)
        
        assert result1 is True
        assert result2 is True
        assert len(unit.generals.generals) == 2
        
    def test_general_limit_enforced(self):
        """Test that general roster has a maximum limit"""
        game_state = MockGameState()
        unit = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 0, 0, add_generals=False)
        unit.player_id = 1
        game_state.add_knight(unit)
        
        # Try to add more generals than allowed
        max_generals = unit.generals.max_generals
        
        for i in range(max_generals + 1):
            general = GeneralFactory.create_general()
            result = unit.generals.add_general(general)
            
            if i < max_generals:
                assert result is True
            else:
                assert result is False
                
        assert len(unit.generals.generals) == max_generals