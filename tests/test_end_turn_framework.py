import pytest
from unittest.mock import Mock, MagicMock
from game.campaign.end_turn_steps.base import EndTurnContext, EndTurnStep, StepPriority
from game.campaign.end_turn_steps.processor import EndTurnProcessor
from game.campaign.end_turn_steps.income_step import IncomeCollectionStep
from game.campaign.end_turn_steps.movement_step import MovementResetStep
from game.campaign.end_turn_steps.population_step import PopulationCalculationStep


class TestEndTurnStep(EndTurnStep):
    """Test implementation of EndTurnStep for testing."""
    __test__ = False
    
    def __init__(self, name: str, priority: StepPriority, dependencies=None):
        self._name = name
        self._priority = priority
        self._dependencies = dependencies or []
        self.executed = False
        self.should_execute_result = True
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def priority(self) -> StepPriority:
        return self._priority
    
    @property
    def dependencies(self):
        return self._dependencies
    
    def should_execute(self, context: EndTurnContext) -> bool:
        return self.should_execute_result
    
    def execute(self, context: EndTurnContext):
        self.executed = True
        return f"result_from_{self.name}"


class TestEndTurnContext:
    """Test EndTurnContext functionality."""
    
    def test_context_creation(self):
        campaign_state = Mock()
        context = EndTurnContext(
            campaign_state=campaign_state,
            current_country_id=1,
            turn_number=5,
            step_results={}
        )
        
        assert context.campaign_state is campaign_state
        assert context.current_country_id == 1
        assert context.turn_number == 5
        assert context.step_results == {}
    
    def test_result_storage_and_retrieval(self):
        context = EndTurnContext(
            campaign_state=Mock(),
            current_country_id=1,
            turn_number=1,
            step_results={}
        )
        
        # Test setting and getting results
        context.set_result("test_step", {"income": 100})
        result = context.get_result("test_step")
        assert result == {"income": 100}
        
        # Test default value for missing result
        missing = context.get_result("missing_step", "default")
        assert missing == "default"


class TestEndTurnProcessor:
    """Test EndTurnProcessor functionality."""
    
    def test_step_registration(self):
        processor = EndTurnProcessor()
        step = TestEndTurnStep("test", StepPriority.INCOME)
        
        processor.register_step(step)
        assert step.name in processor._step_map
        assert step in processor._steps
    
    def test_duplicate_step_registration_raises_error(self):
        processor = EndTurnProcessor()
        step1 = TestEndTurnStep("test", StepPriority.INCOME)
        step2 = TestEndTurnStep("test", StepPriority.POPULATION)
        
        processor.register_step(step1)
        with pytest.raises(ValueError, match="already registered"):
            processor.register_step(step2)
    
    def test_step_unregistration(self):
        processor = EndTurnProcessor()
        step = TestEndTurnStep("test", StepPriority.INCOME)
        
        processor.register_step(step)
        processor.unregister_step("test")
        
        assert step.name not in processor._step_map
        assert step not in processor._steps
    
    def test_execution_order_by_priority(self):
        processor = EndTurnProcessor()
        
        step_high = TestEndTurnStep("high", StepPriority.PREPARATION)
        step_low = TestEndTurnStep("low", StepPriority.CLEANUP)
        step_medium = TestEndTurnStep("medium", StepPriority.INCOME)
        
        processor.register_step(step_low)
        processor.register_step(step_high)
        processor.register_step(step_medium)
        
        order = processor.get_execution_order()
        assert [s.name for s in order] == ["high", "medium", "low"]
    
    def test_dependency_ordering(self):
        processor = EndTurnProcessor()
        
        step_a = TestEndTurnStep("step_a", StepPriority.INCOME)
        step_b = TestEndTurnStep("step_b", StepPriority.INCOME, dependencies=["step_a"])
        step_c = TestEndTurnStep("step_c", StepPriority.INCOME, dependencies=["step_b"])
        
        processor.register_step(step_c)
        processor.register_step(step_a)
        processor.register_step(step_b)
        
        order = processor.get_execution_order()
        assert [s.name for s in order] == ["step_a", "step_b", "step_c"]
    
    def test_circular_dependency_detection(self):
        processor = EndTurnProcessor()
        
        step_a = TestEndTurnStep("step_a", StepPriority.INCOME, dependencies=["step_b"])
        step_b = TestEndTurnStep("step_b", StepPriority.INCOME, dependencies=["step_a"])
        
        processor.register_step(step_a)
        processor.register_step(step_b)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            processor.get_execution_order()
    
    def test_execute_with_mock_campaign_state(self):
        processor = EndTurnProcessor()
        step = TestEndTurnStep("test", StepPriority.INCOME)
        processor.register_step(step)
        
        campaign_state = Mock()
        context = processor.execute(campaign_state, 1, 5)
        
        assert step.executed
        assert context.campaign_state is campaign_state
        assert context.current_country_id == 1
        assert context.turn_number == 5
        assert context.get_result("test") == "result_from_test"
    
    def test_should_execute_false_skips_step(self):
        processor = EndTurnProcessor()
        step = TestEndTurnStep("test", StepPriority.INCOME)
        step.should_execute_result = False
        processor.register_step(step)
        
        campaign_state = Mock()
        context = processor.execute(campaign_state, 1, 5)
        
        assert not step.executed
        assert "test" not in context.step_results


class TestIncomeCollectionStep:
    """Test IncomeCollectionStep functionality."""
    
    def test_income_collection(self):
        # Mock campaign state
        campaign_state = Mock()
        
        # Mock cities
        city1 = Mock()
        city1.name = "City1"
        city1.income = 100
        
        city2 = Mock()
        city2.name = "City2" 
        city2.income = 50
        
        campaign_state.get_country_cities.return_value = [city1, city2]
        campaign_state.country_treasury = {"test_country": 200}
        
        # Create context
        context = EndTurnContext(
            campaign_state=campaign_state,
            current_country_id="test_country",
            turn_number=1,
            step_results={}
        )
        
        # Execute step
        step = IncomeCollectionStep()
        result = step.execute(context)
        
        # Verify results
        assert result["total_income"] == 150
        assert result["city_incomes"]["City1"] == 100
        assert result["city_incomes"]["City2"] == 50
        assert campaign_state.country_treasury["test_country"] == 350  # 200 + 150


class TestMovementResetStep:
    """Test MovementResetStep functionality."""
    
    def test_movement_reset(self):
        # Mock campaign state
        campaign_state = Mock()
        
        # Mock armies
        army1 = Mock()
        army1.country = "test_country"
        army1.movement_points = 1
        army1.max_movement_points = 3
        
        army2 = Mock()
        army2.country = "other_country"
        army2.movement_points = 0
        army2.max_movement_points = 3
        
        army3 = Mock()
        army3.country = "test_country"
        army3.movement_points = 2 
        army3.max_movement_points = 4
        
        campaign_state.armies = {"army1": army1, "army2": army2, "army3": army3}
        
        # Create context
        context = EndTurnContext(
            campaign_state=campaign_state,
            current_country_id="test_country",
            turn_number=1,
            step_results={}
        )
        
        # Execute step
        step = MovementResetStep()
        result = step.execute(context)
        
        # Verify results
        assert result["armies_reset"] == 2
        assert army1.movement_points == 3
        assert army2.movement_points == 0  # Not reset (different country)
        assert army3.movement_points == 4


class TestPopulationCalculationStep:
    """Test PopulationCalculationStep functionality."""
    
    def test_population_calculation(self):
        # Mock campaign state
        campaign_state = Mock()
        
        # Mock cities
        city1 = Mock()
        city1.name = "TradeCity"
        city1.population = 10000
        city1.specialization = "trade"
        
        city2 = Mock()
        city2.name = "MilitaryCity"
        city2.population = 15000
        city2.specialization = "military"
        
        campaign_state.cities = {"TradeCity": city1, "MilitaryCity": city2}
        
        # Create context
        context = EndTurnContext(
            campaign_state=campaign_state,
            current_country_id="test_country",
            turn_number=1,
            step_results={}
        )
        
        # Execute step
        step = PopulationCalculationStep()
        result = step.execute(context)
        
        # Verify results structure
        assert "TradeCity" in result
        assert "MilitaryCity" in result
        
        trade_result = result["TradeCity"]
        assert trade_result["old_population"] == 10000
        assert trade_result["specialization"] == "trade"
        assert trade_result["new_population"] > 10000  # Should grow (trade has positive growth)
        
        military_result = result["MilitaryCity"]
        assert military_result["old_population"] == 15000
        assert military_result["specialization"] == "military"
        # Military cities have low growth (0.3%) + random factor, can grow or decline slightly
        # But minimum population is enforced at 1000, so should be reasonable
        assert military_result["new_population"] >= 1000
        assert abs(military_result["new_population"] - 15000) <= 200  # Within reasonable range
    
    def test_minimum_population_enforced(self):
        # Mock campaign state with very small city
        campaign_state = Mock()
        
        city = Mock()
        city.name = "SmallCity"
        city.population = 500  # Below minimum
        city.specialization = "military"
        
        campaign_state.cities = {"SmallCity": city}
        
        context = EndTurnContext(
            campaign_state=campaign_state,
            current_country_id="test_country",
            turn_number=1,
            step_results={}
        )
        
        step = PopulationCalculationStep()
        step.execute(context)
        
        # Should be set to minimum of 1000
        assert city.population >= 1000


if __name__ == "__main__":
    pytest.main([__file__])