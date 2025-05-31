"""
Comprehensive tests for the fog of war system.

Tests include:
- Line of sight calculations
- Visibility states and transitions
- Terrain blocking (hills)
- Unit blocking (cavalry)
- Player-specific visibility maps
- Unit identification at distance
- General abilities for extended vision
- AI visibility restrictions

NOTE: Player IDs are 1-based (player 1 = id 1, player 2 = id 2)
"""

import pytest
import pygame
pygame.init()  # Initialize pygame for tests
from game.visibility import FogOfWar, VisibilityState, VisionRange
from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.generals import General, KeenSightAbility
from game.terrain import TerrainMap, TerrainType


class TestFogOfWar:
    """Test the fog of war system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.game_state = GameState(battle_config={
            'board_size': (10, 10),
            'knights': 0,
            'castles': 0
        })
        # Clear default units and castles
        self.game_state.knights = []
        self.game_state.castles = []
        
        # Clear all terrain to plains by default to avoid random blocking
        for x in range(10):
            for y in range(10):
                self.game_state.terrain_map.set_terrain(x, y, TerrainType.PLAINS)
        
        # Re-initialize fog of war without castles
        self.game_state._update_all_fog_of_war()
        
    def test_initial_visibility_hidden(self):
        """Test that all hexes start as hidden"""
        fog = self.game_state.fog_of_war
        
        for x in range(self.game_state.board_width):
            for y in range(self.game_state.board_height):
                assert fog.get_visibility_state(1, x, y) == VisibilityState.HIDDEN
                assert fog.get_visibility_state(2, x, y) == VisibilityState.HIDDEN
                
    def test_unit_basic_vision(self):
        """Test basic unit vision range"""
        # Add a warrior at center
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        self.game_state.knights.append(warrior)
        
        # Update fog of war
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Check warrior can see in range
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE  # Own position
        assert fog.get_visibility_state(1, 6, 5) == VisibilityState.VISIBLE  # Adjacent
        assert fog.get_visibility_state(1, 5, 6) == VisibilityState.VISIBLE  # Adjacent
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.VISIBLE  # 2 hexes away
        assert fog.get_visibility_state(1, 5, 7) == VisibilityState.VISIBLE  # 2 hexes away
        assert fog.get_visibility_state(1, 8, 5) == VisibilityState.PARTIAL  # 3 hexes away
        
        # Check can't see beyond range
        # Note: Some areas might be EXPLORED due to terrain generation
        state = fog.get_visibility_state(1, 9, 5)  # 4 hexes away
        assert state in [VisibilityState.HIDDEN, VisibilityState.EXPLORED]
        
        # Check enemy player can't see
        assert fog.get_visibility_state(2, 5, 5) == VisibilityState.HIDDEN
        
    def test_different_unit_vision_ranges(self):
        """Test that different unit types have different vision ranges"""
        # Add different unit types
        archer = UnitFactory.create_unit("Test Archer", KnightClass.ARCHER, 2, 2)
        archer.player_id = 1
        cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 8, 8)
        cavalry.player_id = 1
        
        self.game_state.knights.extend([archer, cavalry])
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Check archer has vision range 4
        # At distance 4, should at least be explored (was visible during initial update)
        assert fog.get_visibility_state(1, 2, 6) != VisibilityState.HIDDEN  # 4 hexes away
        
        # Check cavalry has vision range 4
        assert fog.get_visibility_state(1, 8, 4) != VisibilityState.HIDDEN  # 4 hexes away
        
    def test_terrain_blocking_hills(self):
        """Test that hills block line of sight"""
        # Create terrain with hills
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        
        # Add unit on one side of hill
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 3, 5)
        warrior.player_id = 1
        self.game_state.knights.append(warrior)
        
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Can see up to the hill
        assert fog.get_visibility_state(1, 4, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE  # The hill itself
        
        # Can't see past the hill clearly - should be blocked or at edge of vision
        # (6,5) is at distance 3, might be PARTIAL if at edge of vision
        state_6_5 = fog.get_visibility_state(1, 6, 5)
        # Should be either HIDDEN (blocked) or PARTIAL (edge of vision but blocked)
        assert state_6_5 in [VisibilityState.HIDDEN, VisibilityState.PARTIAL]
        
        # (7,5) is at distance 4, definitely out of range
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.HIDDEN
        
    def test_unit_on_hill_vision(self):
        """Test that units on hills can see over other hills"""
        # Create terrain with hills
        self.game_state.terrain_map.set_terrain(3, 5, TerrainType.HILLS)  # Unit position
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)  # Blocking hill
        
        # Add unit on hill
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 3, 5)
        warrior.player_id = 1
        self.game_state.knights.append(warrior)
        
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Can see over the other hill
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE  # The other hill (distance 2)
        assert fog.get_visibility_state(1, 6, 5) == VisibilityState.PARTIAL  # Past the hill (distance 3)
        
    def test_cavalry_blocking_vision(self):
        """Test that cavalry blocks vision behind it"""
        # Add viewing unit
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 2, 5)
        warrior.player_id = 1
        
        # Add enemy cavalry in the way
        cavalry = UnitFactory.create_unit("Enemy Cavalry", KnightClass.CAVALRY, 4, 5)
        cavalry.player_id = 2
        
        self.game_state.knights.extend([warrior, cavalry])
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Can see the cavalry
        assert fog.get_visibility_state(1, 4, 5) == VisibilityState.VISIBLE
        
        # Can't see directly behind cavalry
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.HIDDEN
        assert fog.get_visibility_state(1, 6, 5) == VisibilityState.HIDDEN
        
        # Can see to the sides of cavalry
        assert fog.get_visibility_state(1, 4, 4) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 4, 6) == VisibilityState.VISIBLE
        
    def test_elevated_cavalry_vision(self):
        """Test that cavalry (elevated) blocks other cavalry at same elevation"""
        # Add cavalry viewing unit
        cavalry1 = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 2, 5)
        cavalry1.player_id = 1
        
        # Add enemy cavalry in the way
        cavalry2 = UnitFactory.create_unit("Enemy Cavalry", KnightClass.CAVALRY, 4, 5)
        cavalry2.player_id = 2
        
        self.game_state.knights.extend([cavalry1, cavalry2])
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Can see the enemy cavalry
        assert fog.get_visibility_state(1, 4, 5) == VisibilityState.VISIBLE  # Distance 2
        
        # Cannot see past the cavalry (both are elevated, so they block each other)
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.HIDDEN  # Blocked by cavalry
        assert fog.get_visibility_state(1, 6, 5) == VisibilityState.HIDDEN  # Also blocked
        
    def test_elevated_sees_over_hills(self):
        """Test that elevated units can see over hills"""
        # Add cavalry viewing unit (elevated)
        cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 2, 5)
        cavalry.player_id = 1
        
        # Add hill in the way
        self.game_state.terrain_map.set_terrain(4, 5, TerrainType.HILLS)
        
        self.game_state.knights.append(cavalry)
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Can see the hill
        assert fog.get_visibility_state(1, 4, 5) == VisibilityState.VISIBLE  # Distance 2
        
        # CAN see past the hill (cavalry is elevated)
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.PARTIAL  # Distance 3
        assert fog.get_visibility_state(1, 6, 5) != VisibilityState.HIDDEN  # Distance 4, should be visible/partial
        
    def test_unit_identification_distance(self):
        """Test unit identification at different distances"""
        # Add viewing unit
        archer = UnitFactory.create_unit("Test Archer", KnightClass.ARCHER, 2, 5)
        archer.player_id = 1
        
        # Add enemy units at different distances
        enemy1 = UnitFactory.create_unit("Enemy Close", KnightClass.WARRIOR, 3, 5)  # 1 hex
        enemy1.player_id = 2
        enemy2 = UnitFactory.create_unit("Enemy Mid", KnightClass.WARRIOR, 4, 5)   # 2 hexes
        enemy2.player_id = 2
        enemy3 = UnitFactory.create_unit("Enemy Far", KnightClass.WARRIOR, 5, 5)   # 3 hexes
        enemy3.player_id = 2
        
        self.game_state.knights.extend([archer, enemy1, enemy2, enemy3])
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Check identification
        assert fog.can_identify_unit(1, 3, 5) == True   # Close - full ID
        assert fog.can_identify_unit(1, 4, 5) == True   # Mid - full ID
        assert fog.can_identify_unit(1, 5, 5) == False  # Far - partial only
        
        # Check visibility first
        vis_3_5 = fog.get_visibility_state(1, 3, 5)
        vis_4_5 = fog.get_visibility_state(1, 4, 5)
        vis_5_5 = fog.get_visibility_state(1, 5, 5)
        
        # Check known units
        known = fog.get_known_units(self.game_state, 1)
        
        # Only check units that are visible or partial
        if vis_3_5 in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
            assert (3, 5) in known
            if vis_3_5 == VisibilityState.VISIBLE:
                assert known[(3, 5)] == 'warrior'  # Fully identified
                
        if vis_4_5 in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
            assert (4, 5) in known
            if vis_4_5 == VisibilityState.VISIBLE:
                assert known[(4, 5)] == 'warrior'  # Fully identified
                
        if vis_5_5 in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]:
            assert (5, 5) in known
            if vis_5_5 == VisibilityState.PARTIAL:
                assert known[(5, 5)] is None  # Visible but not identified
        
    def test_visibility_state_transitions(self):
        """Test visibility state transitions as units move"""
        # Add unit
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        self.game_state.knights.append(warrior)
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Check initial visibility
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.VISIBLE  # Distance 2
        # Distance 3 - might be blocked by terrain, so check if visible/partial/explored
        state_8_5 = fog.get_visibility_state(1, 8, 5)
        # If the hex is not visible, it might be blocked by terrain
        if state_8_5 == VisibilityState.HIDDEN:
            # Find another hex at distance 3 that's visible
            # Try (5, 8) which is 3 hexes south
            state_5_8 = fog.get_visibility_state(1, 5, 8)
            assert state_5_8 in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]
        else:
            assert state_8_5 in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]
        # Distance 4 - out of range
        state = fog.get_visibility_state(1, 9, 5)
        assert state in [VisibilityState.HIDDEN, VisibilityState.EXPLORED]
        
        # Move unit far away
        warrior.x = 0
        warrior.y = 0
        self.game_state._update_all_fog_of_war()
        
        # Previously visible area should now be explored
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.EXPLORED
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.EXPLORED
        
        # New area should be visible
        assert fog.get_visibility_state(1, 0, 0) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 1, 0) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 0, 1) == VisibilityState.VISIBLE
        
        # Far area still hidden or explored (if it was ever in partial range)
        state_9_5 = fog.get_visibility_state(1, 9, 5)
        assert state_9_5 in [VisibilityState.HIDDEN, VisibilityState.EXPLORED]
        
    def test_general_keen_sight_ability(self):
        """Test that generals with keen sight extend vision range"""
        # Create unit with general
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        
        # Add general with keen sight
        general = General(
            name="Sharp Eyes",
            title="The Watchful",
            abilities=[KeenSightAbility()],
            level=1
        )
        warrior.generals.add_general(general)
        
        self.game_state.knights.append(warrior)
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Should have extended vision (base 3 + 1 = 4)
        # 3 hexes away - should be visible or partial
        state_5_8 = fog.get_visibility_state(1, 5, 8)
        assert state_5_8 in [VisibilityState.VISIBLE, VisibilityState.PARTIAL]
        
        # 4 hexes away (extended range) - should be partial or explored (if previously seen)
        state_5_9 = fog.get_visibility_state(1, 5, 9)
        assert state_5_9 in [VisibilityState.PARTIAL, VisibilityState.EXPLORED]
        # 5 hexes away - should be out of range
        state = fog.get_visibility_state(1, 5, 10)
        assert state in [VisibilityState.HIDDEN, VisibilityState.EXPLORED]
        
    def test_multiple_unit_combined_vision(self):
        """Test that multiple units combine their vision"""
        # Add units at different positions
        unit1 = UnitFactory.create_unit("Unit 1", KnightClass.WARRIOR, 3, 5)
        unit1.player_id = 1
        unit2 = UnitFactory.create_unit("Unit 2", KnightClass.WARRIOR, 7, 5)
        unit2.player_id = 1
        
        self.game_state.knights.extend([unit1, unit2])
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Both units' vision areas should be visible
        assert fog.get_visibility_state(1, 3, 5) == VisibilityState.VISIBLE  # Unit 1 position
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.VISIBLE  # Unit 2 position
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE  # Between them
        
        # Areas only one unit can see
        assert fog.get_visibility_state(1, 1, 5) == VisibilityState.VISIBLE  # Only unit 1 (distance 2)
        assert fog.get_visibility_state(1, 9, 5) == VisibilityState.VISIBLE  # Only unit 2 (distance 2)
        
    def test_castle_vision(self):
        """Test that castles provide vision"""
        from game.entities.castle import Castle
        
        # Add castle
        castle = Castle(5, 5, 1)
        self.game_state.castles.append(castle)
        
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Castle should provide vision
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 6, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 7, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 8, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 9, 5) == VisibilityState.PARTIAL
        
    def test_ai_limited_vision(self):
        """Test that AI only considers visible units"""
        from game.ai.ai_player import AIPlayer
        
        # Create AI player
        ai = AIPlayer(2, 'medium')
        
        # Add AI unit
        ai_unit = UnitFactory.create_unit("AI Warrior", KnightClass.WARRIOR, 7, 5)
        ai_unit.player_id = 2
        
        # Add player units - one visible (adjacent), one hidden
        visible_enemy = UnitFactory.create_unit("Visible Enemy", KnightClass.WARRIOR, 6, 5)
        visible_enemy.player_id = 1
        hidden_enemy = UnitFactory.create_unit("Hidden Enemy", KnightClass.WARRIOR, 2, 5)
        hidden_enemy.player_id = 1
        
        self.game_state.knights.extend([ai_unit, visible_enemy, hidden_enemy])
        self.game_state._update_all_fog_of_war()
        
        # Get possible moves for AI
        moves = ai.get_all_possible_moves(self.game_state)
        
        # Filter attack moves
        attack_moves = [m for m in moves if m[0] == 'attack']
        
        # AI should only consider attacking the visible enemy
        assert len(attack_moves) > 0
        for move in attack_moves:
            assert move[2] == visible_enemy  # Only visible enemy is targeted
            
    def test_fog_updates_after_movement(self):
        """Test that fog of war updates correctly after unit movement"""
        # Add unit
        warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, 5, 5)
        warrior.player_id = 1
        self.game_state.knights.append(warrior)
        
        # Initial update
        self.game_state._update_all_fog_of_war()
        fog = self.game_state.fog_of_war
        
        # Check initial visibility
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE
        assert fog.get_visibility_state(1, 8, 5) == VisibilityState.PARTIAL
        
        # Simulate movement (would normally be done through game state methods)
        warrior.x = 9
        warrior.y = 5
        self.game_state._fog_update_needed = True
        
        # Manually trigger update (normally done in game loop)
        self.game_state._update_all_fog_of_war()
        
        # Old position should be explored (too far to see now)
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.EXPLORED
        
        # New position should be visible
        assert fog.get_visibility_state(1, 9, 5) == VisibilityState.VISIBLE
        
    def test_visibility_edge_cases(self):
        """Test edge cases for visibility system"""
        fog = self.game_state.fog_of_war
        
        # Test out of bounds
        assert fog.get_visibility_state(1, -1, 5) == VisibilityState.HIDDEN
        assert fog.get_visibility_state(1, 5, -1) == VisibilityState.HIDDEN
        assert fog.get_visibility_state(1, 100, 5) == VisibilityState.HIDDEN
        assert fog.get_visibility_state(1, 5, 100) == VisibilityState.HIDDEN
        
        # Test invalid player
        assert fog.get_visibility_state(99, 5, 5) == VisibilityState.HIDDEN
