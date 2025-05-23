"""Base component and entity classes"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.entities.unit import Unit

class Component(ABC):
    """Base class for all components"""
    def __init__(self, owner: Optional['Unit'] = None):
        self.owner = owner
    
    def attach(self, owner: 'Unit'):
        """Attach this component to an entity"""
        self.owner = owner
        
    @abstractmethod
    def update(self, dt: float):
        """Update component state"""
        pass

class Behavior(ABC):
    """Base class for behaviors that can be executed"""
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    def can_execute(self, unit: 'Unit', game_state: Any) -> bool:
        """Check if this behavior can be executed"""
        pass
        
    @abstractmethod
    def execute(self, unit: 'Unit', game_state: Any, **kwargs) -> Dict[str, Any]:
        """Execute the behavior and return results"""
        pass
    
    @abstractmethod
    def get_ap_cost(self) -> int:
        """Get the action point cost for this behavior"""
        pass