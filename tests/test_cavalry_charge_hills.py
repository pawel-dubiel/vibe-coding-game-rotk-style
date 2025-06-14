"""Test cavalry charge restrictions on hills"""
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType


def test_cavalry_cannot_charge_from_hills():
    """Test that cavalry cannot charge when standing on hills"""
    # Create game state
    game_state = MockGameState(board_width=10, board_height=10)
    
    # Set terrain - cavalry on hills
    game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
    
    # Create cavalry on hills
    cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 5, 5)
    cavalry.player_id = 0
    cavalry.will = 100  # Plenty of will
    
    # Create enemy adjacent
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    
    game_state.add_knight(cavalry)
    game_state.add_knight(enemy)
    
    # Test charge
    can_charge, reason = cavalry.can_charge(enemy, game_state)
    
    assert not can_charge
    assert "Cannot charge from hills" in reason
    print("✓ Cavalry cannot charge when on hills")


def test_cavalry_cannot_charge_enemy_on_hills():
    """Test that cavalry cannot charge enemies on hills"""
    # Create game state
    game_state = MockGameState(board_width=10, board_height=10)
    
    # Ensure cavalry position is plains
    game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
    # Set terrain - enemy on hills
    game_state.terrain_map.set_terrain(6, 5, TerrainType.HILLS)
    
    # Create cavalry on plains
    cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 5, 5)
    cavalry.player_id = 0
    cavalry.will = 100  # Plenty of will
    
    # Create enemy on hills
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    
    game_state.add_knight(cavalry)
    game_state.add_knight(enemy)
    
    # Test charge
    can_charge, reason = cavalry.can_charge(enemy, game_state)
    
    assert not can_charge
    assert "Cannot charge enemies on hills" in reason
    print("✓ Cavalry cannot charge enemies on hills")


def test_cavalry_can_charge_on_plains():
    """Test that cavalry can charge normally on plains"""
    # Create game state
    game_state = MockGameState(board_width=10, board_height=10)
    
    # Ensure both positions are plains
    game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
    game_state.terrain_map.set_terrain(6, 5, TerrainType.PLAINS)
    
    # Create cavalry
    cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 5, 5)
    cavalry.player_id = 0
    cavalry.will = 100  # Plenty of will
    
    # Create enemy adjacent
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    
    game_state.add_knight(cavalry)
    game_state.add_knight(enemy)
    
    # Test charge
    can_charge, reason = cavalry.can_charge(enemy, game_state)
    
    assert can_charge
    assert reason == "Can charge"
    print("✓ Cavalry can charge normally on plains")


def test_cavalry_charge_behavior_respects_hills():
    """Test that the cavalry charge behavior also respects hill restrictions"""
    from game.behaviors.special_abilities import CavalryChargeBehavior
    
    # Create game state
    game_state = MockGameState(board_width=10, board_height=10)
    
    # Set terrain - cavalry on hills, enemy on plains
    game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
    game_state.terrain_map.set_terrain(6, 5, TerrainType.PLAINS)
    
    # Create cavalry with charge behavior
    cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 5, 5)
    cavalry.player_id = 0
    cavalry.will = 100  # Plenty of will
    cavalry.action_points = 10  # Plenty of AP
    cavalry.behaviors['charge'] = CavalryChargeBehavior()
    
    # Create enemy adjacent
    enemy = UnitFactory.create_unit("Enemy", KnightClass.WARRIOR, 6, 5)
    enemy.player_id = 1
    
    game_state.add_knight(cavalry)
    game_state.add_knight(enemy)
    
    # Test charge through behavior
    result = cavalry.behaviors['charge'].execute(cavalry, game_state, enemy)
    
    assert not result['success']
    assert "Cannot charge from hills" in result['reason']
    print("✓ Cavalry charge behavior respects hill restrictions")


if __name__ == "__main__":
    test_cavalry_cannot_charge_from_hills()
    test_cavalry_cannot_charge_enemy_on_hills()
    test_cavalry_can_charge_on_plains()
    test_cavalry_charge_behavior_respects_hills()
    print("\nAll cavalry charge hill restriction tests passed!")