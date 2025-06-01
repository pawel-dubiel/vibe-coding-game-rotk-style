#!/usr/bin/env python3
"""
Test archer line-of-sight restrictions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.terrain import TerrainMap, TerrainType, Terrain
from game.visibility import FogOfWar, VisibilityState
from game.test_utils.mock_game_state import MockGameState

def test_archer_hills_blocking():
    """Test that hills block archer line of sight"""
    
    # Create a manual 7x5 terrain map
    terrain_map = TerrainMap.__new__(TerrainMap)
    terrain_map.width = 7
    terrain_map.height = 5
    terrain_map.terrain_grid = []
    
    # Initialize with all plains
    for y in range(5):
        row = []
        for x in range(7):
            row.append(Terrain(TerrainType.PLAINS))
        terrain_map.terrain_grid.append(row)
    
    # Add hill line blocking shots
    for y in range(5):
        terrain_map.terrain_grid[y][3] = Terrain(TerrainType.HILLS)
    
    # Create mock game state
    game_state = MockGameState(7, 5, create_terrain=False)
    game_state._terrain_map = terrain_map
    game_state.current_player = 1
    
    # Create archer on left, target on right (hills in between)
    archer = UnitFactory.create_archer("Test Archer", 1, 2)
    archer.player_id = 1
    
    target = UnitFactory.create_warrior("Target", 4, 2)  # Distance 3, within range
    target.player_id = 2
    
    game_state._knights = [archer, target]
    
    # Initialize fog of war with full visibility
    game_state.fog_of_war = FogOfWar(7, 5, 2)
    game_state.fog_of_war.visibility_maps[1][(1, 2)] = VisibilityState.VISIBLE
    game_state.fog_of_war.visibility_maps[1][(4, 2)] = VisibilityState.VISIBLE
    
    # Test that archer cannot target through hills
    attack_behavior = archer.behaviors.get('attack')
    valid_targets = attack_behavior.get_valid_targets(archer, game_state)
    
    assert target not in valid_targets, "Hills should block archer line of sight"
    
    # Test feedback message
    reason = attack_behavior.get_attack_blocked_reason(archer, target, game_state)
    assert "line of sight" in reason.lower(), f"Should mention line of sight, got: {reason}"
    
    print("✓ Hills block archer line of sight")

def test_archer_mountains_blocking():
    """Test that mountains always block archer line of sight"""
    
    # Create a manual 5x3 terrain map
    terrain_map = TerrainMap.__new__(TerrainMap)
    terrain_map.width = 5
    terrain_map.height = 3
    terrain_map.terrain_grid = []
    
    # Initialize with all plains
    for y in range(3):
        row = []
        for x in range(5):
            row.append(Terrain(TerrainType.PLAINS))
        terrain_map.terrain_grid.append(row)
    
    # Add mountain blocking
    terrain_map.terrain_grid[1][2] = Terrain(TerrainType.MOUNTAINS)
    
    # Create mock game state
    game_state = MockGameState(5, 3, create_terrain=False)
    game_state._terrain_map = terrain_map
    game_state.current_player = 1
    
    # Create archer and target with mountain between
    archer = UnitFactory.create_archer("Test Archer", 1, 1)
    archer.player_id = 1
    
    target = UnitFactory.create_warrior("Target", 3, 1)
    target.player_id = 2
    
    game_state._knights = [archer, target]
    
    # Initialize fog of war with full visibility
    game_state.fog_of_war = FogOfWar(5, 3, 2)
    game_state.fog_of_war.visibility_maps[1][(1, 1)] = VisibilityState.VISIBLE
    game_state.fog_of_war.visibility_maps[1][(3, 1)] = VisibilityState.VISIBLE
    
    # Test that archer cannot target through mountains
    attack_behavior = archer.behaviors.get('attack')
    valid_targets = attack_behavior.get_valid_targets(archer, game_state)
    
    assert target not in valid_targets, "Mountains should always block archer line of sight"
    
    # Test feedback message
    reason = attack_behavior.get_attack_blocked_reason(archer, target, game_state)
    assert "line of sight" in reason.lower(), f"Should mention line of sight, got: {reason}"
    
    print("✓ Mountains block archer line of sight")

def test_archer_clear_line_of_sight():
    """Test that archers can shoot with clear line of sight"""
    
    # Create a manual 5x3 terrain map with all plains
    terrain_map = TerrainMap.__new__(TerrainMap)
    terrain_map.width = 5
    terrain_map.height = 3
    terrain_map.terrain_grid = []
    
    # Initialize with all plains
    for y in range(3):
        row = []
        for x in range(5):
            row.append(Terrain(TerrainType.PLAINS))
        terrain_map.terrain_grid.append(row)
    
    # Create mock game state
    game_state = MockGameState(5, 3, create_terrain=False)
    game_state._terrain_map = terrain_map
    game_state.current_player = 1
    
    # Create archer and target with clear line of sight
    archer = UnitFactory.create_archer("Test Archer", 1, 1)
    archer.player_id = 1
    
    target = UnitFactory.create_warrior("Target", 3, 1)
    target.player_id = 2
    
    game_state._knights = [archer, target]
    
    # Initialize fog of war with full visibility
    game_state.fog_of_war = FogOfWar(5, 3, 2)
    game_state.fog_of_war.visibility_maps[1][(1, 1)] = VisibilityState.VISIBLE
    game_state.fog_of_war.visibility_maps[1][(3, 1)] = VisibilityState.VISIBLE
    
    # Test that archer can target with clear line of sight
    attack_behavior = archer.behaviors.get('attack')
    valid_targets = attack_behavior.get_valid_targets(archer, game_state)
    
    assert target in valid_targets, "Archer should be able to shoot with clear line of sight"
    
    # Test feedback message should be positive
    reason = attack_behavior.get_attack_blocked_reason(archer, target, game_state)
    assert "should be possible" in reason.lower(), f"Should be possible, got: {reason}"
    
    print("✓ Clear line of sight allows archer attacks")

def test_archer_out_of_range():
    """Test archer range limitations with feedback"""
    
    # Create a manual 7x3 terrain map with all plains
    terrain_map = TerrainMap.__new__(TerrainMap)
    terrain_map.width = 7
    terrain_map.height = 3
    terrain_map.terrain_grid = []
    
    # Initialize with all plains
    for y in range(3):
        row = []
        for x in range(7):
            row.append(Terrain(TerrainType.PLAINS))
        terrain_map.terrain_grid.append(row)
    
    # Create mock game state
    game_state = MockGameState(7, 3, create_terrain=False)
    game_state._terrain_map = terrain_map
    game_state.current_player = 1
    
    # Create archer and target beyond range (archer range is 3)
    archer = UnitFactory.create_archer("Test Archer", 1, 1)
    archer.player_id = 1
    
    target = UnitFactory.create_warrior("Target", 5, 1)  # Distance 4, range 3
    target.player_id = 2
    
    game_state._knights = [archer, target]
    
    # Initialize fog of war with full visibility
    game_state.fog_of_war = FogOfWar(7, 3, 2)
    game_state.fog_of_war.visibility_maps[1][(1, 1)] = VisibilityState.VISIBLE
    game_state.fog_of_war.visibility_maps[1][(5, 1)] = VisibilityState.VISIBLE
    
    # Test that archer cannot target beyond range
    attack_behavior = archer.behaviors.get('attack')
    valid_targets = attack_behavior.get_valid_targets(archer, game_state)
    
    assert target not in valid_targets, "Target should be out of archer range"
    
    # Test feedback message mentions range
    reason = attack_behavior.get_attack_blocked_reason(archer, target, game_state)
    assert "out of range" in reason.lower(), f"Should mention out of range, got: {reason}"
    
    print("✓ Out of range targets properly blocked with feedback")

if __name__ == "__main__":
    print("Testing archer line-of-sight system...")
    print()
    
    test_archer_hills_blocking()
    test_archer_mountains_blocking()
    test_archer_clear_line_of_sight()
    test_archer_out_of_range()
    
    print()
    print("All archer line-of-sight tests passed!")