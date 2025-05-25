"""Manual test to verify cavalry disruption display"""
import pygame
from game.game_state import GameState
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.terrain import TerrainType

def test_cavalry_disruption_display():
    """Test that shows cavalry disruption in different scenarios"""
    pygame.init()
    
    # Create game state
    game_state = GameState(vs_ai=False)
    
    # Clear existing knights
    game_state.knights = []
    
    # Find different terrain types
    plains_pos = None
    forest_pos = None
    hills_pos = None
    
    for x in range(game_state.board_width):
        for y in range(game_state.board_height):
            terrain = game_state.terrain_map.get_terrain(x, y)
            if terrain:
                if terrain.type == TerrainType.PLAINS and not plains_pos:
                    plains_pos = (x, y)
                elif terrain.type == TerrainType.FOREST and not forest_pos:
                    forest_pos = (x, y)
                elif terrain.type == TerrainType.HILLS and not hills_pos:
                    hills_pos = (x, y)
    
    # Create cavalry units in different terrains
    if plains_pos:
        cavalry1 = UnitFactory.create_unit("Plains Cavalry", KnightClass.CAVALRY, plains_pos[0], plains_pos[1], add_generals=False)
        cavalry1.player_id = 1
        game_state.knights.append(cavalry1)
        print(f"Cavalry on plains at {plains_pos}: disrupted = {cavalry1.is_disrupted}")
    
    if forest_pos:
        cavalry2 = UnitFactory.create_unit("Forest Cavalry", KnightClass.CAVALRY, forest_pos[0], forest_pos[1], add_generals=False)
        cavalry2.player_id = 1
        cavalry2.is_disrupted = True  # Should be disrupted in forest
        game_state.knights.append(cavalry2)
        print(f"Cavalry in forest at {forest_pos}: disrupted = {cavalry2.is_disrupted}")
    
    if hills_pos:
        cavalry3 = UnitFactory.create_unit("Hills Cavalry", KnightClass.CAVALRY, hills_pos[0], hills_pos[1], add_generals=False)
        cavalry3.player_id = 2  # Enemy cavalry
        cavalry3.is_disrupted = True  # Should be disrupted in hills
        game_state.knights.append(cavalry3)
        print(f"Enemy cavalry in hills at {hills_pos}: disrupted = {cavalry3.is_disrupted}")
    
    # Also test with a castle
    castle = game_state.castles[0]
    cavalry4 = UnitFactory.create_unit("Castle Cavalry", KnightClass.CAVALRY, castle.center_x, castle.center_y, add_generals=False)
    cavalry4.player_id = 1
    cavalry4.is_disrupted = True  # Should be disrupted in castle
    game_state.knights.append(cavalry4)
    print(f"Cavalry in castle at ({castle.center_x}, {castle.center_y}): disrupted = {cavalry4.is_disrupted}")
    
    return game_state

if __name__ == "__main__":
    test_cavalry_disruption_display()