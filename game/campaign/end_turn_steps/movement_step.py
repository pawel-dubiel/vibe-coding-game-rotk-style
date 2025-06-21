from typing import Dict, Any, Optional
from .base import EndTurnStep, EndTurnContext, StepPriority

class MovementResetStep(EndTurnStep):
    """Resets movement points for all armies belonging to the current country."""
    
    @property
    def name(self) -> str:
        return "movement_reset"
    
    @property
    def priority(self) -> StepPriority:
        return StepPriority.PREPARATION
    
    @property
    def description(self) -> str:
        return "Resets movement points for all armies of the current country"
    
    def execute(self, context: EndTurnContext) -> Optional[Dict[str, Any]]:
        """Execute movement reset for the current country's armies."""
        campaign_state = context.campaign_state
        current_country = context.current_country_id
        reset_armies = {}
        
        for army_id, army in campaign_state.armies.items():
            if army.country == current_country:
                old_movement = army.movement_points
                army.movement_points = army.max_movement_points
                reset_armies[army_id] = {
                    'old_movement': old_movement,
                    'new_movement': army.movement_points
                }
        
        return {
            'armies_reset': len(reset_armies),
            'army_details': reset_armies
        }