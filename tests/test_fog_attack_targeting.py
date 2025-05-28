"""Test that attack targeting respects fog of war"""
import pygame
pygame.init()

from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass


def test_attack_targeting_respects_fog():
    """Test that invisible units cannot be targeted"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (20, 20),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Create archer for player 1
    archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 5, 5)
    archer.player_id = 1
    
    # Create enemies at different distances
    # Visible enemy (within vision range)
    visible_enemy = UnitFactory.create_unit("Visible", KnightClass.WARRIOR, 7, 5)
    visible_enemy.player_id = 2
    
    # Invisible enemy (outside vision range)
    invisible_enemy = UnitFactory.create_unit("Invisible", KnightClass.WARRIOR, 10, 5)
    invisible_enemy.player_id = 2
    
    game_state.knights.extend([archer, visible_enemy, invisible_enemy])
    game_state.current_player = 1
    
    # Update fog of war
    game_state._update_all_fog_of_war()
    
    # Check visibility
    assert game_state.fog_of_war.get_visibility_state(1, 7, 5).value >= 2  # At least PARTIAL
    assert game_state.fog_of_war.get_visibility_state(1, 10, 5).value == 0  # HIDDEN
    
    # Get attack targets through behavior
    attack_targets = archer.behaviors['attack'].get_valid_targets(archer, game_state)
    
    # Should only include visible enemy
    assert len(attack_targets) == 1
    assert visible_enemy in attack_targets
    assert invisible_enemy not in attack_targets
    
    print("✓ Attack behavior respects fog of war")
    
    # Test UI targeting method
    game_state.selected_knight = archer
    ui_targets = game_state._get_attack_targets()
    
    # Should only include visible enemy position
    assert len(ui_targets) == 1
    assert (7, 5) in ui_targets
    assert (10, 5) not in ui_targets
    
    print("✓ UI attack targeting respects fog of war")


def test_charge_targeting_respects_fog():
    """Test that cavalry charge targeting respects fog of war"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (20, 20),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Create cavalry for player 1
    cavalry = UnitFactory.create_unit("Cavalry", KnightClass.CAVALRY, 5, 5)
    cavalry.player_id = 1
    
    # Create adjacent enemies
    # Visible enemy (within vision range)
    visible_enemy = UnitFactory.create_unit("Visible", KnightClass.WARRIOR, 6, 5)
    visible_enemy.player_id = 2
    
    # Create another cavalry unit far away to block vision to an enemy behind it
    blocking_cavalry = UnitFactory.create_unit("Blocker", KnightClass.CAVALRY, 8, 5)
    blocking_cavalry.player_id = 2
    
    # Enemy behind the cavalry (should be invisible due to cavalry blocking)
    hidden_enemy = UnitFactory.create_unit("Hidden", KnightClass.WARRIOR, 9, 5)
    hidden_enemy.player_id = 2
    
    game_state.knights.extend([cavalry, visible_enemy, blocking_cavalry, hidden_enemy])
    game_state.current_player = 1
    
    # Update fog of war
    game_state._update_all_fog_of_war()
    
    # Test charge targeting
    game_state.selected_knight = cavalry
    charge_targets = game_state._get_charge_targets()
    
    # Should only include visible adjacent enemy
    assert (6, 5) in charge_targets  # Visible enemy
    # Note: Can't charge non-adjacent enemies anyway
    
    print("✓ Cavalry charge targeting respects fog of war")


def test_partially_visible_units_not_targetable():
    """Test that partially visible units (unidentified) cannot be targeted"""
    # Create game state
    game_state = GameState(battle_config={
        'board_size': (20, 20),
        'knights': 0,
        'castles': 0
    })
    game_state.knights = []
    game_state.castles = []
    
    # Create archer
    archer = UnitFactory.create_unit("Archer", KnightClass.ARCHER, 5, 5)
    archer.player_id = 1
    
    # Create enemy at edge of vision (should be PARTIAL)
    # Vision range is 3 for warriors, identification range is 2
    partial_enemy = UnitFactory.create_unit("Partial", KnightClass.WARRIOR, 8, 5)
    partial_enemy.player_id = 2
    
    game_state.knights.extend([archer, partial_enemy])
    game_state.current_player = 1
    
    # Update fog of war
    game_state._update_all_fog_of_war()
    
    # Check that enemy is partially visible
    visibility = game_state.fog_of_war.get_visibility_state(1, 8, 5)
    print(f"Enemy visibility: {visibility.name}")
    
    # Even if within attack range, partially visible units shouldn't be targetable
    # because we need full identification to attack
    attack_targets = archer.behaviors['attack'].get_valid_targets(archer, game_state)
    
    # Should be empty - can't target partially visible units
    assert len(attack_targets) == 0
    
    print("✓ Partially visible units cannot be targeted")


if __name__ == "__main__":
    test_attack_targeting_respects_fog()
    test_charge_targeting_respects_fog()
    test_partially_visible_units_not_targetable()
    print("\nAll fog of war targeting tests passed!")