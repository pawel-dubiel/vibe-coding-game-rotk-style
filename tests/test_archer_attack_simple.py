"""Simple test for archer attack functionality without pygame dependencies"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass

def test_archer_has_attack_behavior():
    """Test that archers have attack behavior with correct name"""
    archer = UnitFactory.create_archer("Test Archer", 10, 10)
    
    # Check archer has attack behavior (not archer_attack)
    assert 'attack' in archer.behaviors, f"Archer behaviors: {list(archer.behaviors.keys())}"
    
    # Check can_attack works
    assert archer.can_attack(), "Archer should be able to attack"
    
    # Check attack range
    attack_behavior = archer.behaviors['attack']
    assert attack_behavior.attack_range == 3, f"Archer range should be 3, got {attack_behavior.attack_range}"
    
    print("✓ Archer has 'attack' behavior")
    print("✓ Archer can_attack() returns True")
    print("✓ Archer has range 3")

def test_all_units_have_attack():
    """Test that all unit types have attack behavior"""
    units = [
        (UnitFactory.create_warrior("Warrior", 0, 0), "Warrior", 1),
        (UnitFactory.create_archer("Archer", 0, 0), "Archer", 3),
        (UnitFactory.create_cavalry("Cavalry", 0, 0), "Cavalry", 1),
        (UnitFactory.create_mage("Mage", 0, 0), "Mage", 2),
    ]
    
    for unit, name, expected_range in units:
        assert 'attack' in unit.behaviors, f"{name} missing 'attack' behavior"
        assert unit.can_attack(), f"{name} can_attack() returned False"
        assert unit.behaviors['attack'].attack_range == expected_range, f"{name} has wrong range"
        print(f"✓ {name} has attack behavior with range {expected_range}")

if __name__ == "__main__":
    print("Testing archer attack fix...\n")
    
    test_archer_has_attack_behavior()
    print()
    test_all_units_have_attack()
    
    print("\nAll tests passed! Archers can now attack properly.")