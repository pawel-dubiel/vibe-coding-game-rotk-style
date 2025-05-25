"""Test height advantage/disadvantage for ranged attacks"""
import pygame
pygame.init()

from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType
from game.behaviors.combat import ArcherAttackBehavior


def test_archer_shooting_uphill_penalty():
    """Test that archers shooting uphill do less damage"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (10, 10),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Set terrain - target on hills
    game_state.terrain_map.set_terrain(6, 5, TerrainType.HILLS)
    
    # Create archer on plains
    archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 4, 5)
    archer.player_id = 0
    archer.action_points = 10
    
    # Create enemy on hills
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    # Warriors have 100 soldiers by default
    
    game_state.knights.extend([archer, enemy])
    
    # Calculate damage shooting uphill
    attacker_terrain = game_state.terrain_map.get_terrain(archer.x, archer.y)
    target_terrain = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
    
    # Test with archer attack behavior
    archer_behavior = ArcherAttackBehavior()
    damage_uphill = archer_behavior.calculate_damage(archer, enemy, attacker_terrain, target_terrain)
    
    # Now test shooting on flat ground for comparison
    game_state.terrain_map.set_terrain(6, 5, TerrainType.PLAINS)
    target_terrain_flat = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
    damage_flat = archer_behavior.calculate_damage(archer, enemy, attacker_terrain, target_terrain_flat)
    
    # Damage uphill should be about 70% of flat damage
    expected_ratio = 0.7
    actual_ratio = damage_uphill / damage_flat if damage_flat > 0 else 0
    
    print(f"Damage on flat ground: {damage_flat}")
    print(f"Damage shooting uphill: {damage_uphill}")
    print(f"Actual ratio: {actual_ratio:.2f} (expected: {expected_ratio})")
    
    # Allow some variance due to rounding
    assert 0.65 <= actual_ratio <= 0.75
    print("✓ Archers shooting uphill have 30% damage penalty")


def test_archer_shooting_downhill_bonus():
    """Test that archers shooting downhill do more damage"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (10, 10),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Set terrain - archer on hills
    game_state.terrain_map.set_terrain(4, 5, TerrainType.HILLS)
    
    # Create archer on hills
    archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 4, 5)
    archer.player_id = 0
    archer.action_points = 10
    
    # Create enemy on plains
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    # Warriors have 100 soldiers by default
    
    game_state.knights.extend([archer, enemy])
    
    # Calculate damage shooting downhill
    attacker_terrain = game_state.terrain_map.get_terrain(archer.x, archer.y)
    target_terrain = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
    
    # Test with archer attack behavior
    archer_behavior = ArcherAttackBehavior()
    damage_downhill = archer_behavior.calculate_damage(archer, enemy, attacker_terrain, target_terrain)
    
    # Now test shooting on flat ground for comparison
    game_state.terrain_map.set_terrain(4, 5, TerrainType.PLAINS)
    attacker_terrain_flat = game_state.terrain_map.get_terrain(archer.x, archer.y)
    damage_flat = archer_behavior.calculate_damage(archer, enemy, attacker_terrain_flat, target_terrain)
    
    # Damage downhill should be about 120% of flat damage
    expected_ratio = 1.2
    actual_ratio = damage_downhill / damage_flat if damage_flat > 0 else 0
    
    print(f"\nDamage on flat ground: {damage_flat}")
    print(f"Damage shooting downhill: {damage_downhill}")
    print(f"Actual ratio: {actual_ratio:.2f} (expected: {expected_ratio})")
    
    # Allow some variance due to rounding
    assert 1.15 <= actual_ratio <= 1.25
    print("✓ Archers shooting downhill have 20% damage bonus")


def test_melee_no_height_advantage():
    """Test that melee attacks are not affected by height advantage"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (10, 10),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Set terrain - enemy on hills
    game_state.terrain_map.set_terrain(6, 5, TerrainType.HILLS)
    
    # Create warrior on plains (adjacent for melee)
    warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 5, 5)
    warrior.player_id = 0
    warrior.action_points = 10
    
    # Create enemy on hills
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    # Warriors have 100 soldiers by default
    
    game_state.knights.extend([warrior, enemy])
    
    # Calculate melee damage against unit on hills
    attacker_terrain = game_state.terrain_map.get_terrain(warrior.x, warrior.y)
    target_terrain = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
    
    damage_vs_hills = warrior.calculate_damage(enemy, attacker_terrain, target_terrain)
    
    # Now test against unit on plains
    game_state.terrain_map.set_terrain(6, 5, TerrainType.PLAINS)
    target_terrain_flat = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
    damage_vs_plains = warrior.calculate_damage(enemy, attacker_terrain, target_terrain_flat)
    
    print(f"\nMelee damage vs plains: {damage_vs_plains}")
    print(f"Melee damage vs hills: {damage_vs_hills}")
    
    # The difference should only be from terrain defense bonus, not height
    # Hills give +10 defense, so damage should be somewhat less but not 30% less
    if damage_vs_plains > 0:
        ratio = damage_vs_hills / damage_vs_plains
        print(f"Ratio: {ratio:.2f}")
        # Should be more than 0.7 (which would indicate height penalty was applied)
        assert ratio > 0.75
    
    print("✓ Melee attacks are not affected by height advantage")


def test_mage_ranged_height_advantage():
    """Test that mage ranged attacks also get height advantage"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (10, 10),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Set terrain - mage on hills
    game_state.terrain_map.set_terrain(4, 5, TerrainType.HILLS)
    
    # Create mage on hills with ranged attack
    mage = UnitFactory.create_unit("Mage", KnightClass.MAGE, 4, 5)
    mage.player_id = 0
    mage.action_points = 10
    # Ensure mage has ranged attack behavior
    if 'attack' in mage.behaviors:
        mage.behaviors['attack'].attack_range = 2  # Give mage ranged attack
    
    # Create enemy on plains
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    # Warriors have 100 soldiers by default
    
    game_state.knights.extend([mage, enemy])
    
    # Calculate damage shooting downhill
    attacker_terrain = game_state.terrain_map.get_terrain(mage.x, mage.y)
    target_terrain = game_state.terrain_map.get_terrain(enemy.x, enemy.y)
    
    damage_downhill = mage.calculate_damage(enemy, attacker_terrain, target_terrain)
    
    # Now test on flat ground
    game_state.terrain_map.set_terrain(4, 5, TerrainType.PLAINS)
    attacker_terrain_flat = game_state.terrain_map.get_terrain(mage.x, mage.y)
    damage_flat = mage.calculate_damage(enemy, attacker_terrain_flat, target_terrain)
    
    print(f"\nMage damage on flat ground: {damage_flat}")
    print(f"Mage damage from hills: {damage_downhill}")
    
    if damage_flat > 0:
        ratio = damage_downhill / damage_flat
        print(f"Ratio: {ratio:.2f}")
        # Should get bonus for shooting downhill
        assert ratio > 1.1
    
    print("✓ Mages with ranged attacks get height advantage")


if __name__ == "__main__":
    test_archer_shooting_uphill_penalty()
    test_archer_shooting_downhill_bonus()
    test_melee_no_height_advantage()
    test_mage_ranged_height_advantage()
    print("\nAll height advantage tests passed!")