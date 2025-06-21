from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, List, Dict, Any

class StepPriority(IntEnum):
    """Priority levels for end-turn steps. Lower values execute first."""
    PREPARATION = 100
    INCOME = 200
    POPULATION = 300
    PRODUCTION = 400
    CONSUMPTION = 500
    MAINTENANCE = 600
    EVENTS = 700
    CLEANUP = 800

@dataclass
class EndTurnContext:
    """Context passed to each end-turn step containing campaign state and results from previous steps."""
    campaign_state: Any  # Will be CampaignState
    current_country_id: int
    turn_number: int
    step_results: Dict[str, Any]  # Results from previous steps
    
    def get_result(self, step_name: str, default: Any = None) -> Any:
        """Get the result from a previous step."""
        return self.step_results.get(step_name, default)
    
    def set_result(self, step_name: str, result: Any) -> None:
        """Store a result for use by later steps."""
        self.step_results[step_name] = result

class EndTurnStep(ABC):
    """Base class for all end-turn processing steps."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this step."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> StepPriority:
        """Priority determines execution order. Lower values execute first."""
        pass
    
    @property
    def description(self) -> str:
        """Optional description of what this step does."""
        return ""
    
    @property
    def dependencies(self) -> List[str]:
        """List of step names that must execute before this step."""
        return []
    
    def should_execute(self, context: EndTurnContext) -> bool:
        """
        Determine if this step should execute for the current context.
        Override to add conditional execution logic.
        """
        return True
    
    @abstractmethod
    def execute(self, context: EndTurnContext) -> Optional[Any]:
        """
        Execute the end-turn step.
        
        Args:
            context: The end-turn context with campaign state and previous results
            
        Returns:
            Optional result that will be stored in context for use by later steps
        """
        pass
    
    def validate_dependencies(self, context: EndTurnContext) -> bool:
        """Validate that all dependencies have been executed."""
        for dep in self.dependencies:
            if dep not in context.step_results:
                return False
        return True