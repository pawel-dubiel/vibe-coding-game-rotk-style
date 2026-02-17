"""Comprehensive tests for cavalry auto-disruption feature"""
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType
from game.behaviors.movement import MovementBehavior


class TestCavalryAutoDisruption:
    """Test that cavalry is automatically disrupted in difficult terrain during movement"""
    
    def test_cavalry_starts_not_disrupted(self):
        """Test that cavalry starts without disruption"""
        game_state = MockGameState()
        cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, 0, 0, add_generals=False)
        cavalry.player_id = 1
        game_state.add_knight(cavalry)
        
        assert cavalry.is_disrupted is False
    
    def test_cavalry_disrupted_when_moving_to_forest(self):
        """Test cavalry becomes disrupted when moving to forest"""
        game_state = MockGameState()
        
        # Find a plains tile and adjacent forest tile
        plains_x, plains_y = None, None
        forest_x, forest_y = None, None
        
        for x in range(game_state.board_width - 1):
            for y in range(game_state.board_height - 1):
                terrain = game_state.terrain_map.get_terrain(x, y)
                if terrain and terrain.type == TerrainType.PLAINS:
                    # Check adjacent tiles for forest
                    for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                        adj_x, adj_y = x + dx, y + dy
                        if 0 <= adj_x < game_state.board_width and 0 <= adj_y < game_state.board_height:
                            adj_terrain = game_state.terrain_map.get_terrain(adj_x, adj_y)
                            if adj_terrain and adj_terrain.type == TerrainType.FOREST:
                                plains_x, plains_y = x, y
                                forest_x, forest_y = adj_x, adj_y
                                break
                if forest_x is not None:
                    break
            if forest_x is not None:
                break
        
        if plains_x is not None and forest_x is not None:
            # Create cavalry on plains
            cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, plains_x, plains_y, add_generals=False)
            cavalry.player_id = 1
            game_state.add_knight(cavalry)
            
            assert cavalry.is_disrupted is False
            
            # Move cavalry to forest
            if cavalry.action_points > 0:
                result = cavalry.behaviors['move'].execute(cavalry, game_state, forest_x, forest_y)
                if result['success']:
                    # In the real game, disruption is checked when animation completes
                    # For testing, we manually check it
                    from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
                    check_cavalry_disruption_for_terrain(cavalry, game_state)
                    assert cavalry.is_disrupted is True
    
    def test_cavalry_disrupted_when_moving_to_hills(self):
        """Test cavalry becomes disrupted when moving to hills"""
        game_state = MockGameState()
        
        # Find a plains tile and adjacent hills tile
        plains_x, plains_y = None, None
        hills_x, hills_y = None, None
        
        for x in range(game_state.board_width - 1):
            for y in range(game_state.board_height - 1):
                terrain = game_state.terrain_map.get_terrain(x, y)
                if terrain and terrain.type == TerrainType.PLAINS:
                    # Check adjacent tiles for hills
                    for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                        adj_x, adj_y = x + dx, y + dy
                        if 0 <= adj_x < game_state.board_width and 0 <= adj_y < game_state.board_height:
                            adj_terrain = game_state.terrain_map.get_terrain(adj_x, adj_y)
                            if adj_terrain and adj_terrain.type == TerrainType.HILLS:
                                plains_x, plains_y = x, y
                                hills_x, hills_y = adj_x, adj_y
                                break
                if hills_x is not None:
                    break
            if hills_x is not None:
                break
        
        if plains_x is not None and hills_x is not None:
            # Create cavalry on plains
            cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, plains_x, plains_y, add_generals=False)
            cavalry.player_id = 1
            game_state.add_knight(cavalry)
            
            assert cavalry.is_disrupted is False
            
            # Move cavalry to hills
            if cavalry.action_points > 0:
                result = cavalry.behaviors['move'].execute(cavalry, game_state, hills_x, hills_y)
                if result['success']:
                    # In the real game, disruption is checked when animation completes
                    # For testing, we manually check it
                    from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
                    check_cavalry_disruption_for_terrain(cavalry, game_state)
                    assert cavalry.is_disrupted is True
    
    def test_cavalry_disrupted_when_moving_to_castle(self):
        """Test cavalry becomes disrupted when moving to castle"""
        game_state = MockGameState()
        castle = game_state.castles[0]
        
        # Place cavalry adjacent to castle
        cavalry_x = castle.center_x - 2
        cavalry_y = castle.center_y
        
        cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, cavalry_x, cavalry_y, add_generals=False)
        cavalry.player_id = 1
        game_state.add_knight(cavalry)
        
        assert cavalry.is_disrupted is False
        
        # Move cavalry to castle
        if cavalry.action_points > 0:
            result = cavalry.behaviors['move'].execute(cavalry, game_state, castle.center_x, castle.center_y)
            if result['success']:
                # In the real game, disruption is checked when animation completes
                # For testing, we manually check it
                from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
                check_cavalry_disruption_for_terrain(cavalry, game_state)
                assert cavalry.is_disrupted is True
    
    def test_cavalry_disruption_cleared_when_moving_to_plains(self):
        """Test cavalry disruption is cleared when moving back to plains"""
        game_state = MockGameState()
        
        # Find a forest tile and adjacent plains tile
        forest_x, forest_y = None, None
        plains_x, plains_y = None, None
        
        for x in range(game_state.board_width - 1):
            for y in range(game_state.board_height - 1):
                terrain = game_state.terrain_map.get_terrain(x, y)
                if terrain and terrain.type == TerrainType.FOREST:
                    # Check adjacent tiles for plains
                    for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                        adj_x, adj_y = x + dx, y + dy
                        if 0 <= adj_x < game_state.board_width and 0 <= adj_y < game_state.board_height:
                            adj_terrain = game_state.terrain_map.get_terrain(adj_x, adj_y)
                            if adj_terrain and adj_terrain.type == TerrainType.PLAINS:
                                forest_x, forest_y = x, y
                                plains_x, plains_y = adj_x, adj_y
                                break
                if plains_x is not None:
                    break
            if plains_x is not None:
                break
        
        if forest_x is not None and plains_x is not None:
            # Create cavalry in forest (manually set disrupted)
            cavalry = UnitFactory.create_unit("Test Cavalry", KnightClass.CAVALRY, forest_x, forest_y, add_generals=False)
            cavalry.player_id = 1
            cavalry.is_disrupted = True
            game_state.add_knight(cavalry)
            
            assert cavalry.is_disrupted is True
            
            # Move cavalry to plains
            if cavalry.action_points > 0:
                result = cavalry.behaviors['move'].execute(cavalry, game_state, plains_x, plains_y)
                if result['success']:
                    # In the real game, disruption is checked when animation completes
                    # For testing, we manually check it
                    from game.entities.unit_helpers import check_cavalry_disruption_for_terrain
                    check_cavalry_disruption_for_terrain(cavalry, game_state)
                    assert cavalry.is_disrupted is False
    
    def test_non_cavalry_not_disrupted_in_difficult_terrain(self):
        """Test that non-cavalry units are not disrupted by terrain"""
        game_state = MockGameState()
        
        # Find a forest tile
        forest_x, forest_y = None, None
        for x in range(game_state.board_width):
            for y in range(game_state.board_height):
                terrain = game_state.terrain_map.get_terrain(x, y)
                if terrain and terrain.type == TerrainType.FOREST:
                    forest_x, forest_y = x, y
                    break
            if forest_x is not None:
                break
        
        if forest_x is not None:
            # Create warrior in forest
            warrior = UnitFactory.create_unit("Test Warrior", KnightClass.WARRIOR, forest_x, forest_y, add_generals=False)
            warrior.player_id = 1
            game_state.add_knight(warrior)
            
            # Warrior should not be disrupted
            assert warrior.is_disrupted is False
            
            # Move warrior within forest
            if warrior.action_points > 0:
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    new_x, new_y = forest_x + dx, forest_y + dy
                    if 0 <= new_x < game_state.board_width and 0 <= new_y < game_state.board_height:
                        terrain = game_state.terrain_map.get_terrain(new_x, new_y)
                        if terrain and terrain.type == TerrainType.FOREST:
                            result = warrior.behaviors['move'].execute(warrior, game_state, new_x, new_y)
                            if result['success']:
                                # Still not disrupted
                                assert warrior.is_disrupted is False
                                break
    
    def test_cavalry_disruption_affects_combat(self):
        """Test that disrupted cavalry has reduced combat effectiveness"""
        game_state = MockGameState()
        
        # Create two cavalry units
        cavalry1 = UnitFactory.create_unit("Cavalry 1", KnightClass.CAVALRY, 0, 0, add_generals=False)
        cavalry1.player_id = 1
        cavalry2 = UnitFactory.create_unit("Cavalry 2", KnightClass.CAVALRY, 2, 0, add_generals=False)
        cavalry2.player_id = 2
        game_state.add_knight(cavalry1)
        game_state.add_knight(cavalry2)
        
        # Disrupt one cavalry
        cavalry1.is_disrupted = True
        
        # Test combat effectiveness
        from game.behaviors.combat import AttackBehavior
        attack_behavior = AttackBehavior()
        
        # Disrupted cavalry attacking
        disrupted_damage = attack_behavior.calculate_damage(cavalry1, cavalry2)
        
        # Non-disrupted cavalry attacking
        cavalry1.is_disrupted = False
        normal_damage = attack_behavior.calculate_damage(cavalry1, cavalry2)
        
        # Disrupted damage should be less
        assert disrupted_damage < normal_damage
        # Due to rounding and combat calculations, allow reasonable variance
        assert disrupted_damage <= normal_damage * 0.85
