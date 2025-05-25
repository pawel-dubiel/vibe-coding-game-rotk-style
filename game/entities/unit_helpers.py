"""Helper functions for units"""
from game.entities.knight import KnightClass

def check_cavalry_disruption_for_terrain(unit, game_state):
    """Check if cavalry should be disrupted based on current terrain"""
    if unit.unit_class != KnightClass.CAVALRY:
        return
    
    # Get terrain at unit position
    terrain = game_state.terrain_map.get_terrain(unit.x, unit.y)
    castle_at_pos = game_state.get_castle_at(unit.x, unit.y)
    
    # Disrupt cavalry in difficult terrain
    if (terrain and terrain.type.value in ["Forest", "Hills"]) or castle_at_pos:
        unit.is_disrupted = True
    else:
        unit.is_disrupted = False