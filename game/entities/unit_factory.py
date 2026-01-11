"""Factory for creating units with appropriate behaviors"""
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.entities.quality import UnitQuality
from game.behaviors.movement import MovementBehavior
from game.behaviors.combat import AttackBehavior, ArcherAttackBehavior
from game.behaviors.special_abilities import CavalryChargeBehavior
from game.behaviors.breakaway import BreakawayBehavior
from game.behaviors.rotation import RotationBehavior
from game.behaviors.vision import VisionBehavior, ArcherVisionBehavior, ScoutVisionBehavior, StandardVisionBehavior
from game.behaviors.terrain_movement import (
    CavalryTerrainBehavior, ArcherTerrainBehavior, 
    WarriorTerrainBehavior, MageTerrainBehavior
)
from game.components.general_factory import GeneralFactory

class UnitFactory:
    """Factory for creating units with appropriate behaviors based on class"""
    
    @staticmethod
    def create_unit(name: str, unit_class: KnightClass, x: int, y: int, add_generals: bool = True, quality: UnitQuality = UnitQuality.REGULAR) -> Unit:
        """Create a unit with behaviors appropriate to its class"""
        unit = Unit(name, unit_class, x, y, quality=quality)
        
        # Add behaviors based on unit class
        if unit_class == KnightClass.WARRIOR:
            unit.add_behavior(MovementBehavior(movement_range=3))
            unit.add_behavior(AttackBehavior(attack_range=1))
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            unit.add_behavior(StandardVisionBehavior())
            unit.add_behavior(WarriorTerrainBehavior())
            
        elif unit_class == KnightClass.ARCHER:
            unit.add_behavior(MovementBehavior(movement_range=3))
            unit.add_behavior(ArcherAttackBehavior())
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            unit.add_behavior(ArcherVisionBehavior())
            unit.add_behavior(ArcherTerrainBehavior())
            
        elif unit_class == KnightClass.CAVALRY:
            unit.add_behavior(MovementBehavior(movement_range=4))
            unit.add_behavior(AttackBehavior(attack_range=1))
            unit.add_behavior(CavalryChargeBehavior())
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            unit.add_behavior(ScoutVisionBehavior())  # Cavalry scouts ahead
            unit.add_behavior(CavalryTerrainBehavior())
            
        elif unit_class == KnightClass.MAGE:
            unit.add_behavior(MovementBehavior(movement_range=2))
            unit.add_behavior(AttackBehavior(attack_range=2))
            unit.add_behavior(BreakawayBehavior())
            unit.add_behavior(RotationBehavior())
            unit.add_behavior(StandardVisionBehavior())
            unit.add_behavior(MageTerrainBehavior())
            
        # Add starting generals if requested
        if add_generals:
            starting_generals = GeneralFactory.create_starting_generals_for_unit(unit_class)
            for general in starting_generals[:2]:  # Max 2 starting generals
                unit.generals.add_general(general)
            
        return unit
        
    @staticmethod
    def create_warrior(name: str, x: int, y: int, quality: UnitQuality = UnitQuality.REGULAR) -> Unit:
        """Create a warrior unit"""
        return UnitFactory.create_unit(name, KnightClass.WARRIOR, x, y, quality=quality)
        
    @staticmethod
    def create_archer(name: str, x: int, y: int, quality: UnitQuality = UnitQuality.REGULAR) -> Unit:
        """Create an archer unit"""
        return UnitFactory.create_unit(name, KnightClass.ARCHER, x, y, quality=quality)
        
    @staticmethod
    def create_cavalry(name: str, x: int, y: int, quality: UnitQuality = UnitQuality.REGULAR) -> Unit:
        """Create a cavalry unit"""
        return UnitFactory.create_unit(name, KnightClass.CAVALRY, x, y, quality=quality)
        
    @staticmethod
    def create_mage(name: str, x: int, y: int, quality: UnitQuality = UnitQuality.REGULAR) -> Unit:
        """Create a mage unit"""
        return UnitFactory.create_unit(name, KnightClass.MAGE, x, y, quality=quality)