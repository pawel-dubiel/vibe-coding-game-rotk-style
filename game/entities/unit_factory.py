"""Factory for creating units with appropriate behaviors"""
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.behaviors.movement import MovementBehavior
from game.behaviors.combat import AttackBehavior, ArcherAttackBehavior
from game.behaviors.special_abilities import CavalryChargeBehavior
from game.behaviors.breakaway import BreakawayBehavior
from game.behaviors.rotation import RotationBehavior
from game.components.general_factory import GeneralFactory

class UnitFactory:
    """Factory for creating units with appropriate behaviors based on class"""
    
    @staticmethod
    def create_unit(name: str, unit_class: KnightClass, x: int, y: int, add_generals: bool = True) -> Unit:
        """Create a unit with behaviors appropriate to its class"""
        unit = Unit(name, unit_class, x, y)
        
        # Add behaviors based on unit class
        if unit_class == KnightClass.WARRIOR:
            unit.add_behavior(MovementBehavior(movement_range=3))
            unit.add_behavior(AttackBehavior(attack_range=1))
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            
        elif unit_class == KnightClass.ARCHER:
            unit.add_behavior(MovementBehavior(movement_range=3))
            unit.add_behavior(ArcherAttackBehavior())
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            
        elif unit_class == KnightClass.CAVALRY:
            unit.add_behavior(MovementBehavior(movement_range=4))
            unit.add_behavior(AttackBehavior(attack_range=1))
            unit.add_behavior(CavalryChargeBehavior())
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            
        elif unit_class == KnightClass.MAGE:
            unit.add_behavior(MovementBehavior(movement_range=2))
            unit.add_behavior(AttackBehavior(attack_range=2))
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            
        # Add starting generals if requested
        if add_generals:
            starting_generals = GeneralFactory.create_starting_generals_for_unit(unit_class)
            for general in starting_generals[:2]:  # Max 2 starting generals
                unit.generals.add_general(general)
            
        return unit
        
    @staticmethod
    def create_warrior(name: str, x: int, y: int) -> Unit:
        """Create a warrior unit"""
        return UnitFactory.create_unit(name, KnightClass.WARRIOR, x, y)
        
    @staticmethod
    def create_archer(name: str, x: int, y: int) -> Unit:
        """Create an archer unit"""
        return UnitFactory.create_unit(name, KnightClass.ARCHER, x, y)
        
    @staticmethod
    def create_cavalry(name: str, x: int, y: int) -> Unit:
        """Create a cavalry unit"""
        return UnitFactory.create_unit(name, KnightClass.CAVALRY, x, y)
        
    @staticmethod
    def create_mage(name: str, x: int, y: int) -> Unit:
        """Create a mage unit"""
        return UnitFactory.create_unit(name, KnightClass.MAGE, x, y)