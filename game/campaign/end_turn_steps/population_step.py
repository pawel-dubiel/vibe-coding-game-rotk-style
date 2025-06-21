import random
from typing import Dict, Any, Optional
from .base import EndTurnStep, EndTurnContext, StepPriority
from ..city_specialization import CitySpecialization

class PopulationCalculationStep(EndTurnStep):
    """Calculates population growth/decline for all cities."""
    
    @property
    def name(self) -> str:
        return "population_calculation"
    
    @property
    def priority(self) -> StepPriority:
        return StepPriority.POPULATION
    
    @property
    def description(self) -> str:
        return "Calculates population growth/decline based on city specialization and random factors"
    
    def execute(self, context: EndTurnContext) -> Optional[Dict[str, Any]]:
        """Execute population calculation for all cities."""
        campaign_state = context.campaign_state
        population_changes = {}
        
        for city_name, city in campaign_state.cities.items():
            old_population = city.population
            
            # Calculate base growth rate based on specialization
            specialization_enum = CitySpecialization.from_string(city.specialization)
            base_growth_rate = CitySpecialization.get_growth_rate(specialization_enum)
            
            # Add random factor (-0.5% to +0.5%)
            random_factor = (random.random() - 0.5) * 0.01
            
            # Calculate actual growth rate
            growth_rate = base_growth_rate + random_factor
            
            # Apply growth
            population_change = int(city.population * growth_rate)
            new_population = max(1000, city.population + population_change)  # Minimum 1000 population
            
            # Update city population
            city.population = new_population
            
            # Track changes
            population_changes[city_name] = {
                'old_population': old_population,
                'new_population': new_population,
                'change': population_change,
                'growth_rate': growth_rate,
                'specialization': city.specialization
            }
        
        return population_changes
    
