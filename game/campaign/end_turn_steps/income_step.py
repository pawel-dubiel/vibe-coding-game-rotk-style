from typing import Dict, Any, Optional
from .base import EndTurnStep, EndTurnContext, StepPriority

class IncomeCollectionStep(EndTurnStep):
    """Collects income from cities for the current country."""
    
    @property
    def name(self) -> str:
        return "income_collection"
    
    @property
    def priority(self) -> StepPriority:
        return StepPriority.INCOME
    
    @property
    def description(self) -> str:
        return "Collects income from all cities belonging to the current country"
    
    def execute(self, context: EndTurnContext) -> Optional[Dict[str, Any]]:
        """Execute income collection for the current country."""
        campaign_state = context.campaign_state
        current_country = context.current_country_id
        total_income = 0
        city_incomes = {}
        
        # Get cities belonging to current country
        current_country_cities = campaign_state.get_country_cities(current_country)
        
        for city in current_country_cities:
            campaign_state.country_treasury[current_country] += city.income
            city_incomes[city.name] = city.income
            total_income += city.income
        
        return {
            'total_income': total_income,
            'city_incomes': city_incomes,
            'treasury_after': campaign_state.country_treasury.get(current_country, 0)
        }