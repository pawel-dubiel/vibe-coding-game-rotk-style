"""
Tests for the shadow casting line-of-sight algorithm.

Tests include:
- Basic visibility calculation
- Shadow propagation
- Terrain blocking (hills, mountains)
- Unit blocking
- Elevation effects
- Performance comparison with old algorithm
"""

import pytest
import pygame
import time

from game.shadowcasting import SimpleShadowcaster, HexShadowcaster
from game.visibility import FogOfWar, VisibilityState
from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainMap, TerrainType
from game.hex_utils import HexGrid


class TestShadowCasting:
    """Test the shadow casting algorithm"""
    
    def setup_method(self):
        """Setup test environment with completely fresh state"""
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
            
        # Create completely fresh game state for each test
        self._create_fresh_game_state()
        
    def _create_fresh_game_state(self):
        """Create completely fresh game state to avoid any contamination"""
        self.game_state = GameState(battle_config={
            'board_size': (20, 20),
            'knights': 0,
            'castles': 0
        })
        # Ensure completely empty state
        self.game_state.knights = []
        self.game_state.castles = []
        self.game_state.current_player = 1
        self.game_state.selected_knight = None
        
        # Create fresh shadowcaster
        self.shadowcaster = SimpleShadowcaster()
        
    def teardown_method(self):
        """Clean up test environment"""
        # Clean up game state
        if hasattr(self, 'game_state'):
            # Clear all units and castles completely
            self.game_state.knights.clear()
            self.game_state.castles.clear()
            
            # Reset terrain map to clear any modifications
            from game.terrain import TerrainMap
            self.game_state.terrain_map = TerrainMap(self.game_state.board_width, self.game_state.board_height)
            
            # Reset any other game state that might affect visibility
            self.game_state.selected_knight = None
            if hasattr(self.game_state, 'current_player'):
                self.game_state.current_player = 1
        
    def test_basic_visibility(self):
        """Test basic visibility calculation without obstacles"""
        origin = (10, 10)
        max_range = 3
        
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range, is_elevated=False
        )
        
        # Should see origin
        assert origin in visible
        assert visible[origin] == 0
        
        # Check we can see hexes within range
        hex_grid = HexGrid()
        origin_hex = hex_grid.offset_to_axial(origin[0], origin[1])
        
        # Count visible hexes at each distance
        for distance in range(1, max_range + 1):
            hexes_at_distance = sum(1 for d in visible.values() if d == distance)
            # In a hex grid, there are 6 * distance hexes at each ring
            # But some might be out of bounds
            assert hexes_at_distance > 0
            
    def test_hill_blocking(self):
        """Test that hills block vision correctly"""
        # Place viewer at (5, 5) on plains
        origin = (5, 5)
        
        # Ensure viewer is on plains (not on hills)
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
        
        # Place hill at (7, 5) - should block vision beyond
        self.game_state.terrain_map.set_terrain(7, 5, TerrainType.HILLS)
        
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=4, is_elevated=False
        )
        
        # Should see the hill
        assert (7, 5) in visible
        
        # Should NOT see directly behind the hill
        # In a hex grid, (8, 5) and (9, 5) should be blocked
        assert (8, 5) not in visible
        assert (9, 5) not in visible
        
    def test_elevated_viewer_sees_over_hills(self):
        """Test that elevated viewers can see over hills"""
        origin = (5, 5)
        
        # Place hill at (7, 5)
        self.game_state.terrain_map.set_terrain(7, 5, TerrainType.HILLS)
        
        # Elevated viewer (like cavalry)
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=4, is_elevated=True
        )
        
        # Should see over the hill
        assert (7, 5) in visible
        assert (8, 5) in visible  # Can see past hill
        
    def test_viewer_on_hills_sees_over_hills(self):
        """Test that viewers on hills can see over other hills"""
        origin = (5, 5)
        
        # Place viewer on hill
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
        # Place another hill in the way
        self.game_state.terrain_map.set_terrain(7, 5, TerrainType.HILLS)
        
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=4, is_elevated=False
        )
        
        # Should see over the other hill
        assert (8, 5) in visible
        
    def test_mountains_always_block(self):
        """Test that mountains always block vision"""
        origin = (5, 5)
        
        # Place mountain at (7, 5)
        self.game_state.terrain_map.set_terrain(7, 5, TerrainType.MOUNTAINS)
        
        # Even elevated viewers can't see over mountains
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=4, is_elevated=True
        )
        
        # Should see the mountain
        assert (7, 5) in visible
        
        # Should NOT see past it
        assert (8, 5) not in visible
        
    def test_unit_blocking(self):
        """Test that units can block vision"""
        origin = (5, 5)
        
        # Place a cavalry unit (blocks vision) at (7, 5)
        blocker = UnitFactory.create_unit("Blocker", KnightClass.CAVALRY, 7, 5)
        blocker.player_id = 2  # Enemy unit
        self.game_state.knights.append(blocker)
        
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=4, is_elevated=False
        )
        
        # Should see the unit
        assert (7, 5) in visible
        
        # Should NOT see directly behind it
        assert (8, 5) not in visible
        
    def test_shadow_sectors(self):
        """Test that shadows propagate correctly in sectors"""
        # Create completely fresh state for this test
        self._create_fresh_game_state()
        
        origin = (10, 10)
        
        # Place a mountain to create a shadow
        self.game_state.terrain_map.set_terrain(12, 10, TerrainType.MOUNTAINS)
        
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=5, is_elevated=False
        )
        
        # The mountain should cast a shadow in its sector
        # Hexes behind it in the same direction should be blocked
        assert (12, 10) in visible  # Can see the mountain
        assert (13, 10) not in visible  # Blocked by mountain
        assert (14, 10) not in visible  # Also in shadow
        
        # But adjacent sectors should still be visible
        # These are at similar distances but different angles
        assert (12, 9) in visible  # Different sector
        assert (12, 11) in visible  # Different sector
        
    def test_performance_comparison(self):
        """Compare performance of shadow casting vs old algorithm"""
        # Create a complex terrain with many obstacles
        for i in range(5):
            for j in range(5):
                if (i + j) % 3 == 0:
                    self.game_state.terrain_map.set_terrain(
                        10 + i, 10 + j, TerrainType.HILLS
                    )
                    
        origin = (10, 10)
        max_range = 5
        
        # Time the shadow casting algorithm
        start_time = time.time()
        for _ in range(100):
            visible_shadow = self.shadowcaster.calculate_visible_hexes(
                self.game_state, origin, max_range, is_elevated=False
            )
        shadow_time = time.time() - start_time
        
        # For comparison with the old algorithm, we'd need to implement
        # a reference to the old method. For now, just ensure it's fast
        assert shadow_time < 1.0  # Should complete 100 iterations in < 1 second
        
        # Verify we get reasonable results
        assert len(visible_shadow) > 0
        assert origin in visible_shadow
        
    def test_fog_of_war_integration(self):
        """Test that fog of war correctly uses the shadow casting algorithm"""
        # Create completely fresh state for this test
        self._create_fresh_game_state()
        
        # Ensure starting position is on plains
        self.game_state.terrain_map.set_terrain(5, 5, TerrainType.PLAINS)
        
        # Add a unit for player 1
        unit = UnitFactory.create_unit("Scout", KnightClass.ARCHER, 5, 5)
        unit.player_id = 1
        self.game_state.knights.append(unit)
        
        # Add some terrain
        self.game_state.terrain_map.set_terrain(7, 5, TerrainType.HILLS)
        
        # Update fog of war
        self.game_state.fog_of_war.update_player_visibility(self.game_state, 1)
        
        # Check visibility states
        fog = self.game_state.fog_of_war
        
        # Unit's position should be visible
        assert fog.get_visibility_state(1, 5, 5) == VisibilityState.VISIBLE
        
        # Nearby hexes should be visible
        assert fog.get_visibility_state(1, 6, 5) == VisibilityState.VISIBLE
        
        # The hill should be visible (archer has vision range 4, hill is at distance 2)
        state = fog.get_visibility_state(1, 7, 5)
        assert state == VisibilityState.VISIBLE  # Distance 2 is within full_id_range
        
        # Behind the hill should NOT be visible
        behind_state = fog.get_visibility_state(1, 8, 5)
        assert behind_state in [VisibilityState.HIDDEN, VisibilityState.EXPLORED]
        
    def test_edge_of_board(self):
        """Test visibility calculation at board edges"""
        # Place unit at corner
        origin = (0, 0)
        
        visible = self.shadowcaster.calculate_visible_hexes(
            self.game_state, origin, max_range=3, is_elevated=False
        )
        
        # Should handle board boundaries correctly
        assert origin in visible
        
        # Should not crash or include out-of-bounds hexes
        for (x, y) in visible.keys():
            assert 0 <= x < self.game_state.board_width
            assert 0 <= y < self.game_state.board_height