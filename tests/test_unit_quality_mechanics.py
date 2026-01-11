
import pytest
from unittest.mock import MagicMock, patch
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.entities.quality import UnitQuality
from game.combat_config import CombatConfig

class TestUnitQualityMechanics:
    
    @pytest.fixture
    def mock_game_state(self):
        gs = MagicMock()
        gs.knights = []
        gs.board_width = 10
        gs.board_height = 10
        gs.get_knight_at.return_value = None
        return gs

    def test_unit_initialization(self):
        unit_reg = Unit("Regular", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.REGULAR)
        assert unit_reg.quality == UnitQuality.REGULAR
        assert unit_reg.times_routed == 0
        
        unit_mil = Unit("Militia", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.MILITIA)
        assert unit_mil.quality == UnitQuality.MILITIA
        
        unit_elite = Unit("Elite", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.ELITE)
        assert unit_elite.quality == UnitQuality.ELITE

    def test_routing_counter_increment(self, mock_game_state):
        unit = Unit("Test", KnightClass.WARRIOR, 0, 0)
        assert unit.times_routed == 0
        
        # Start routing
        unit._start_routing(mock_game_state)
        assert unit.is_routing
        assert unit.times_routed == 1
        
        # Call again while already routing (should not increment)
        unit._start_routing(mock_game_state)
        assert unit.times_routed == 1
        
        # Manually stop routing
        unit.is_routing = False
        
        # Start routing again
        unit._start_routing(mock_game_state)
        assert unit.times_routed == 2

    @patch('random.random')
    def test_militia_rally_limit(self, mock_random, mock_game_state):
        # Militia has max_rallies = 0
        unit = Unit("Militia", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.MILITIA)
        
        # Force high morale/cohesion to ensure rally logic would pass if not for quality
        unit.stats.stats.morale = 100
        unit.stats.stats.current_cohesion = 100
        
        # Route 1st time
        unit._start_routing(mock_game_state)
        assert unit.times_routed == 1
        assert unit.is_routing
        
        # Mock random to always succeed rally check
        mock_random.return_value = 0.0 
        
        # Try to rally
        unit.end_turn()
        
        # Should NOT rally because times_routed (1) > max_rallies (0)
        assert unit.is_routing
        assert not getattr(unit, 'has_rallied_this_turn', False)

    @patch('random.random')
    def test_regular_rally_limit(self, mock_random, mock_game_state):
        # Regular has max_rallies = 1
        unit = Unit("Regular", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.REGULAR)
        
        unit.stats.stats.morale = 100
        unit.stats.stats.current_cohesion = 100
        mock_random.return_value = 0.0 

        # Route 1st time
        unit._start_routing(mock_game_state)
        assert unit.times_routed == 1
        
        # Try to rally - Should SUCCEED (1 <= 1)
        unit.end_turn()
        assert not unit.is_routing
        assert unit.has_rallied_this_turn
        
        # Route 2nd time
        unit._start_routing(mock_game_state)
        assert unit.times_routed == 2
        
        # Try to rally - Should FAIL (2 > 1)
        unit.end_turn()
        assert unit.is_routing

    @patch('random.random')
    def test_elite_rally_limit(self, mock_random, mock_game_state):
        # Elite has max_rallies = 3
        unit = Unit("Elite", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.ELITE)
        
        unit.stats.stats.morale = 100
        unit.stats.stats.current_cohesion = 100
        mock_random.return_value = 0.0 

        # Route/Rally 1
        unit._start_routing(mock_game_state)
        unit.end_turn()
        assert not unit.is_routing
        
        # Route/Rally 2
        unit._start_routing(mock_game_state)
        unit.end_turn()
        assert not unit.is_routing
        
        # Route/Rally 3
        unit._start_routing(mock_game_state)
        unit.end_turn()
        assert not unit.is_routing
        
        # Route 4 - Should Stick
        unit._start_routing(mock_game_state)
        assert unit.times_routed == 4
        unit.end_turn()
        assert unit.is_routing

    def test_factory_creation(self):
        from game.entities.unit_factory import UnitFactory
        
        # Default creation (should be REGULAR)
        u1 = UnitFactory.create_warrior("Warrior", 0, 0)
        assert u1.quality == UnitQuality.REGULAR
        
        # Explicit creation
        u2 = UnitFactory.create_warrior("Elite Warrior", 0, 0, quality=UnitQuality.ELITE)
        assert u2.quality == UnitQuality.ELITE
        
        u3 = UnitFactory.create_archer("Militia Archer", 0, 0, quality=UnitQuality.MILITIA)
        assert u3.quality == UnitQuality.MILITIA

    def test_quality_stat_modifiers(self):
        # Regular (Baseline)
        reg = Unit("Reg", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.REGULAR)
        base_morale = reg.stats.stats.max_morale
        base_cohesion = reg.stats.stats.max_cohesion
        
        # Elite (+10)
        elite = Unit("Elite", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.ELITE)
        assert elite.stats.stats.max_morale == base_morale + 10.0
        assert elite.stats.stats.max_cohesion == base_cohesion + 10.0
        
        # Militia (-10)
        militia = Unit("Militia", KnightClass.WARRIOR, 0, 0, quality=UnitQuality.MILITIA)
        assert militia.stats.stats.max_morale == base_morale - 10.0
        assert militia.stats.stats.max_cohesion == base_cohesion - 10.0

