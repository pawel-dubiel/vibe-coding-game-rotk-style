import unittest
from unittest.mock import MagicMock
from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType
from game.components.facing import FacingDirection

class TestAutoFacing(unittest.TestCase):
    def setUp(self):
        import pygame
        pygame.init()
        # Mock display for font/image operations if needed
        if not pygame.display.get_surface():
            pygame.display.set_mode((1, 1), pygame.NOFRAME)
            
        # Create game state (10x10 board)
        self.game_state = GameState({'board_size': (10, 10), 'knights': 0, 'castles': 0}, vs_ai=False)
        self.game_state.knights = []
        
        # Helper to create units
        self.factory = UnitFactory()
        
    def tearDown(self):
        import pygame
        pygame.quit()
        
    def _add_unit(self, unit_class, x, y, player_id, name="Unit"):
        unit = UnitFactory.create_unit(name, unit_class, x, y)
        unit.player_id = player_id
        if hasattr(unit, 'facing'):
            unit.facing.facing = FacingDirection.EAST # Default
        self.game_state.knights.append(unit)
        # Update fog of war so units can see each other
        self.game_state._update_all_fog_of_war()
        return unit

    def _get_screen_pos(self, hex_x, hex_y):
        """Get screen pixel coordinates for a hex"""
        return self.game_state.hex_layout.hex_to_pixel(hex_x, hex_y)

    def _prepare_move(self, unit, target_x, target_y):
        """Prepare unit for movement"""
        self.game_state.selected_knight = unit
        # Populate possible moves using the unit's logic
        self.game_state.possible_moves = unit.get_possible_moves(
            self.game_state.board_width, 
            self.game_state.board_height, 
            self.game_state.terrain_map, 
            self.game_state
        )
        
        # Ensure target is in possible moves (if reachable)
        if (target_x, target_y) not in self.game_state.possible_moves:
            pass

    def _flush_animations(self):
        """Run animations to completion"""
        # Update with a large delta to finish animations
        self.game_state.animation_coordinator.update(10.0)
        # Also force cleanup if needed
        self.game_state.update(0.1)

    def test_autoface_on_move_adjacent(self):
        """Test unit faces enemy when moving adjacent"""
        # Enemy at (5, 5)
        enemy = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Enemy")
        
        # Player unit starts at (2, 5) facing East
        player = self._add_unit(KnightClass.WARRIOR, 2, 5, 1, "Player")
        player.facing.facing = FacingDirection.EAST
        
        # Move to (4, 5) - Adjacent (West of enemy)
        target_x, target_y = 4, 5
        self._prepare_move(player, target_x, target_y)
        
        px, py = self._get_screen_pos(target_x, target_y)
        self.game_state.move_selected_knight(px, py)
        self._flush_animations()
        
        # Should now face EAST (towards enemy at 5,5)
        self.assertEqual(player.facing.facing, FacingDirection.EAST)
        
        # Move another unit to (6, 5)
        player2 = self._add_unit(KnightClass.WARRIOR, 8, 5, 1, "Player2")
        player2.facing.facing = FacingDirection.EAST # Wrong way
        
        target_x, target_y = 6, 5
        self._prepare_move(player2, target_x, target_y)
        
        px, py = self._get_screen_pos(target_x, target_y)
        self.game_state.move_selected_knight(px, py)
        self._flush_animations()
        
        # Should face WEST (towards enemy at 5,5)
        self.assertEqual(player2.facing.facing, FacingDirection.WEST)

    def test_autoface_on_attack(self):
        """Test unit faces enemy when attacking"""
        # Enemy at (5, 5)
        enemy = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Enemy")
        
        # Player unit at (5, 4) (North-ish) facing North (wrong way)
        player = self._add_unit(KnightClass.WARRIOR, 5, 4, 1, "Player")
        player.facing.facing = FacingDirection.NORTH_WEST # Wrong
        player.morale = 100
        player.cohesion = player.max_cohesion
        enemy.morale = 100
        enemy.cohesion = enemy.max_cohesion
        
        # Execute attack
        self.game_state.selected_knight = player
        # Attack target hex (5, 5)
        px, py = self._get_screen_pos(5, 5)
        self.game_state.attack_with_selected_knight(px, py)
        self._flush_animations()
        
        # Should face towards enemy.
        # From (5, 4) [Even row] to (5, 5) [Odd row] is SOUTH_EAST neighbor
        self.assertEqual(player.facing.facing, FacingDirection.SOUTH_EAST)

    def test_autoface_nearest_enemy(self):
        """Test unit faces the NEAREST enemy when moving into a cluster"""
        # Clear
        self.game_state.knights = []
        near_enemy = self._add_unit(KnightClass.WARRIOR, 4, 5, 2, "West Enemy")
        far_enemy = self._add_unit(KnightClass.WARRIOR, 7, 5, 2, "East Enemy")
        
        # Player moves to (5, 5) - In between
        player = self._add_unit(KnightClass.WARRIOR, 5, 2, 1, "Player")
        
        target_x, target_y = 5, 5
        self._prepare_move(player, target_x, target_y)
        
        px, py = self._get_screen_pos(target_x, target_y)
        self.game_state.move_selected_knight(px, py)
        self._flush_animations()
        
        # Dist to (4, 5) is 1. Dist to (7, 5) is 2.
        # Should face West (towards near enemy)
        self.assertEqual(player.facing.facing, FacingDirection.WEST)

    def test_no_autoface_if_routing(self):
        """Test routing units do NOT auto-face enemies (they flee)"""
        enemy = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Enemy")
        player = self._add_unit(KnightClass.WARRIOR, 3, 5, 1, "Player")
        player.is_routing = True
        player.facing.facing = FacingDirection.EAST # Start facing East
        
        # Move AWAY (Routing units can only move away)
        # (3, 5) -> (2, 5) is West. Enemy is East.
        target_x, target_y = 2, 5
        self._prepare_move(player, target_x, target_y)
    
        px, py = self._get_screen_pos(target_x, target_y)
        self.game_state.move_selected_knight(px, py)
        self._flush_animations()
    
        # Should face movement direction (WEST) because routing disables auto-face (which would face EAST/Enemy)
        self.assertEqual(player.facing.facing, FacingDirection.WEST)

    def test_archer_ranged_autoface(self):
        """Test archer faces target when attacking from range"""
        enemy = self._add_unit(KnightClass.WARRIOR, 8, 5, 2, "Enemy")
        archer = self._add_unit(KnightClass.ARCHER, 5, 5, 1, "Archer")
        archer.facing.facing = FacingDirection.WEST # Facing away
        
        # Attack from range (dist 3)
        self.game_state.selected_knight = archer
        px, py = self._get_screen_pos(8, 5)
        self.game_state.attack_with_selected_knight(px, py)
        self._flush_animations()
        
        # Should face East
        self.assertEqual(archer.facing.facing, FacingDirection.EAST)

    def test_terrain_does_not_block_autoface(self):
        """Test that being on hills/forest doesn't prevent auto-facing"""
        # Set terrain
        from game.terrain import Terrain
        self.game_state.terrain_map.terrain_grid[5][5] = Terrain(TerrainType.HILLS)
        
        enemy = self._add_unit(KnightClass.WARRIOR, 5, 5, 2, "Enemy")
        player = self._add_unit(KnightClass.WARRIOR, 4, 5, 1, "Player")
        
        # Move player to (3, 5) -> (4, 5) (Wait, player is AT 4,5)
        # Let's start player at 3,5
        player.x, player.y = 3, 5
        
        target_x, target_y = 4, 5
        self._prepare_move(player, target_x, target_y)
        
        px, py = self._get_screen_pos(target_x, target_y)
        self.game_state.move_selected_knight(px, py)
        self._flush_animations()
        
        self.assertEqual(player.facing.facing, FacingDirection.EAST)
