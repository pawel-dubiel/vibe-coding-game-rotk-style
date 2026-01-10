
from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.test_utils.mock_game_state import MockGameState
from game.terrain import TerrainType
from game.combat_config import CombatConfig

def debug_hills_ap():
    game_state = MockGameState(board_width=10, board_height=10)
    
    # Set hills terrain
    game_state.terrain_map.set_terrain(5, 5, TerrainType.HILLS)
    
    # Create warrior
    warrior = UnitFactory.create_unit("Warrior", KnightClass.WARRIOR, 4, 5)
    warrior.player_id = 1
    
    target = UnitFactory.create_unit("Target", KnightClass.WARRIOR, 5, 5)
    target.player_id = 2
    
    game_state.add_knight(warrior)
    game_state.add_knight(target)
    
    attack_behavior = warrior.behaviors['attack']
    
    base_cost = CombatConfig.get_attack_ap_cost(warrior.unit_class.value)
    print(f"Base AP Cost for Warrior: {base_cost}")
    
    target_terrain = game_state.terrain_map.get_terrain(target.x, target.y)
    print(f"Target Terrain: {target_terrain.type}")
    print(f"Target Terrain Cost: {target_terrain.movement_cost}")
    
    ap_cost = attack_behavior.get_ap_cost(warrior, target, game_state)
    print(f"Total AP Cost: {ap_cost}")
    
    # Check if any other behaviors affect it? No.

if __name__ == "__main__":
    debug_hills_ap()
