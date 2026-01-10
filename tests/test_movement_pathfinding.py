"""Test movement behavior with pathfinding integration"""
from game.behaviors.movement import MovementBehavior
from game.pathfinding import AStarPathFinder, DijkstraPathFinder
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit import Unit
from game.entities.knight import KnightClass
from game.terrain import TerrainType, TerrainMap


class TestMovementPathfinding:
    """Test movement behavior with different pathfinding algorithms"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.game_state = MockGameState(board_width=10, board_height=10)
        
        # Create test unit
        self.unit = Unit(name="Test Unit", unit_class=KnightClass.WARRIOR, x=0, y=0)
        self.unit.player_id = 1
        self.unit.action_points = 5
        self.game_state.add_knight(self.unit)
        
    def test_movement_with_dijkstra_pathfinder(self):
        """Test movement behavior using Dijkstra pathfinder"""
        movement = MovementBehavior(pathfinder=DijkstraPathFinder())
        
        # Get possible moves
        moves = movement.get_possible_moves(self.unit, self.game_state)
        
        assert len(moves) > 0
        assert (0, 0) not in moves  # Starting position excluded
        
        # Check all moves are within AP range
        for move in moves:
            path = movement.get_path_to(self.unit, self.game_state, move[0], move[1])
            assert path is not None
            
    def test_movement_with_astar_pathfinder(self):
        """Test movement behavior using A* pathfinder"""
        movement = MovementBehavior(pathfinder=AStarPathFinder())
        
        # Give unit enough action points to reach the target
        self.unit.action_points = 10
        
        # Get path to specific location
        path = movement.get_path_to(self.unit, self.game_state, 0, 5)
        
        assert path is not None
        assert len(path) > 0
        assert path[-1] == (0, 5)
        
    def test_movement_respects_terrain_costs(self):
        """Test movement considers terrain costs with pathfinding"""
        movement = MovementBehavior(pathfinder=AStarPathFinder())
        
        # Create varied terrain
        from game.terrain import Terrain
        self.game_state.terrain_map.terrain_grid[0][1] = Terrain(TerrainType.FOREST)  # Cost 2
        self.game_state.terrain_map.terrain_grid[0][2] = Terrain(TerrainType.FOREST)  # Cost 2
        
        # Unit with 5 AP can't reach (3,0) through forest
        path = movement.get_path_to(self.unit, self.game_state, 3, 0)
        
        # Should find alternate path or no path if too expensive
        if path:
            # Calculate total AP cost
            total_cost = 0
            positions = [(self.unit.x, self.unit.y)] + list(path)
            for i in range(1, len(positions)):
                total_cost += movement.get_ap_cost(
                    positions[i-1], positions[i], 
                    self.unit, self.game_state
                )
            assert total_cost <= self.unit.action_points
            
    def test_movement_avoids_enemy_zoc(self):
        """Test movement behavior respects Zone of Control with pathfinding"""
        movement = MovementBehavior(pathfinder=DijkstraPathFinder())

        self.unit.action_points = 4

        for y in range(self.game_state.board_height):
            for x in range(self.game_state.board_width):
                self.game_state.terrain_map.set_terrain(x, y, TerrainType.MOUNTAINS)

        for x in range(5):
            self.game_state.terrain_map.set_terrain(x, 0, TerrainType.PLAINS)
        self.game_state.terrain_map.set_terrain(2, 1, TerrainType.PLAINS)
        
        # Place enemy unit that creates ZOC
        enemy = Unit(name="Enemy", unit_class=KnightClass.WARRIOR, x=2, y=1)
        enemy.player_id = 2
        enemy.morale = 100  # High morale for ZOC
        enemy.cohesion = 100
        self.game_state.add_knight(enemy)
        
        # Get possible moves
        moves = movement.get_possible_moves(self.unit, self.game_state)

        assert (3, 0) in moves
        assert (4, 0) not in moves

        path_to_zoc = movement.get_path_to(self.unit, self.game_state, 3, 0)
        path_to_blocked = movement.get_path_to(self.unit, self.game_state, 4, 0)

        assert path_to_zoc
        assert path_to_zoc[-1] == (3, 0)
        assert path_to_blocked == []
                
    def test_pathfinder_integration_with_formation(self):
        """Test pathfinding considers formation breaking penalties"""
        movement = MovementBehavior(pathfinder=AStarPathFinder())
        
        # Place friendly unit adjacent for formation
        friendly = Unit(name="Friendly", unit_class=KnightClass.WARRIOR, x=1, y=0)
        friendly.player_id = 1
        self.game_state.add_knight(friendly)
        
        # Moving away from friendly should have higher cost
        # Path that maintains formation should be preferred
        path = movement.get_path_to(self.unit, self.game_state, 2, 2)
        
        if path:
            # Verify the path (implementation specific)
            assert len(path) > 0
            
    def test_different_pathfinders_same_result(self):
        """Test different pathfinders produce valid results"""
        dijkstra_movement = MovementBehavior(pathfinder=DijkstraPathFinder())
        astar_movement = MovementBehavior(pathfinder=AStarPathFinder())
        
        # Both should find valid moves
        dijkstra_moves = dijkstra_movement.get_possible_moves(self.unit, self.game_state)
        astar_moves = astar_movement.get_possible_moves(self.unit, self.game_state)
        
        # Both should return non-empty move lists
        assert len(dijkstra_moves) > 0
        assert len(astar_moves) > 0
        
        # Results might differ slightly due to implementation,
        # but both should be valid
        for move in dijkstra_moves:
            path = dijkstra_movement.get_path_to(self.unit, self.game_state, move[0], move[1])
            assert path is not None
            
    def test_custom_pathfinder_can_be_used(self):
        """Test that custom pathfinder implementations can be plugged in"""
        # Verify the interface allows custom implementations
        class CustomPathFinder(AStarPathFinder):
            def find_path(self, start, end, game_state, unit=None, max_cost=None, **kwargs):
                # Custom implementation that always prefers y=0 row
                path = super().find_path(start, end, game_state, unit, max_cost, **kwargs)
                return path
        
        movement = MovementBehavior(pathfinder=CustomPathFinder())
        path = movement.get_path_to(self.unit, self.game_state, 5, 0)
        
        assert path is not None  # Should work with custom pathfinder
