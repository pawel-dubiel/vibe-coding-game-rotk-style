from typing import List, Dict, Set
import logging
from .base import EndTurnStep, EndTurnContext

logger = logging.getLogger(__name__)

class EndTurnProcessor:
    """Manages and executes end-turn steps in the correct order."""
    
    def __init__(self):
        self._steps: List[EndTurnStep] = []
        self._step_map: Dict[str, EndTurnStep] = {}
    
    def register_step(self, step: EndTurnStep) -> None:
        """Register a new end-turn step."""
        if step.name in self._step_map:
            raise ValueError(f"Step with name '{step.name}' already registered")
        
        self._steps.append(step)
        self._step_map[step.name] = step
        logger.info(f"Registered end-turn step: {step.name} (priority: {step.priority})")
    
    def unregister_step(self, step_name: str) -> None:
        """Remove a step from the processor."""
        if step_name in self._step_map:
            step = self._step_map[step_name]
            self._steps.remove(step)
            del self._step_map[step_name]
            logger.info(f"Unregistered end-turn step: {step_name}")
    
    def get_execution_order(self) -> List[EndTurnStep]:
        """
        Get the steps in execution order, respecting priorities and dependencies.
        Uses topological sort to handle dependencies correctly.
        """
        # First sort by priority
        sorted_steps = sorted(self._steps, key=lambda s: s.priority)
        
        # Build dependency graph
        dependencies: Dict[str, Set[str]] = {}
        for step in sorted_steps:
            dependencies[step.name] = set(step.dependencies)
        
        # Topological sort within each priority level
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(step_name: str):
            if step_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {step_name}")
            if step_name in visited:
                return
            
            temp_visited.add(step_name)
            
            # Visit dependencies first
            step = self._step_map.get(step_name)
            if step:
                for dep in step.dependencies:
                    if dep in self._step_map:
                        visit(dep)
            
            temp_visited.remove(step_name)
            visited.add(step_name)
            
            if step:
                result.append(step)
        
        # Process all steps
        for step in sorted_steps:
            visit(step.name)
        
        return result
    
    def execute(self, campaign_state, current_country_id: int, turn_number: int) -> EndTurnContext:
        """
        Execute all registered end-turn steps in order.
        
        Args:
            campaign_state: The current campaign state
            current_country_id: ID of the country whose turn is ending
            turn_number: Current turn number
            
        Returns:
            The context with all step results
        """
        context = EndTurnContext(
            campaign_state=campaign_state,
            current_country_id=current_country_id,
            turn_number=turn_number,
            step_results={}
        )
        
        execution_order = self.get_execution_order()
        logger.info(f"Executing {len(execution_order)} end-turn steps for country {current_country_id}")
        
        for step in execution_order:
            try:
                # Check dependencies
                if not step.validate_dependencies(context):
                    logger.error(f"Step {step.name} missing dependencies: {step.dependencies}")
                    continue
                
                # Check if step should execute
                if not step.should_execute(context):
                    logger.debug(f"Skipping step {step.name} (should_execute returned False)")
                    continue
                
                logger.debug(f"Executing step: {step.name}")
                result = step.execute(context)
                
                if result is not None:
                    context.set_result(step.name, result)
                    
            except Exception as e:
                logger.error(f"Error executing step {step.name}: {e}", exc_info=True)
                # Continue with other steps even if one fails
        
        logger.info("End-turn processing complete")
        return context