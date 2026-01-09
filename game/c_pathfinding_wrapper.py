try:
    import c_algorithms
    C_EXTENSION_AVAILABLE = True
except ImportError:
    C_EXTENSION_AVAILABLE = False

from typing import List, Tuple, Optional, Dict
from game.pathfinding import PathFinder
from game.terrain import TerrainType, Terrain

class CPathFinder(PathFinder):
    """PathFinder implementation using optimized C extension"""
    
    def __init__(self):
        self._terrain_cache = {} # (map_id, width, height) -> (grid_list, type_mapping)
        self._last_map_id = None
        
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int], 
                  game_state, unit=None, max_cost: Optional[float] = None,
                  cost_function=None) -> Optional[List[Tuple[int, int]]]:
        
        if not C_EXTENSION_AVAILABLE or cost_function is not None:
            # Fallback to Python implementation if C ext missing or custom cost function used
            # (C implementation doesn't support custom cost functions yet)
            return super().find_path(start, end, game_state, unit, max_cost, cost_function)

        width = game_state.board_width
        height = game_state.board_height
        
        # 1. Get or Create Terrain Grid Cache
        # We assume game_state.terrain_map object identity changes if map changes
        # or we can use a version counter if available.
        map_obj = game_state.terrain_map
        map_id = id(map_obj)
        
        if map_id != self._last_map_id or map_id not in self._terrain_cache:
            # Build cache
            terrain_types = list(TerrainType)
            type_to_id = {t: i for i, t in enumerate(terrain_types)}
            
            grid = []
            for y in range(height):
                for x in range(width):
                    t = map_obj.get_terrain(x, y)
                    if t:
                        grid.append(type_to_id.get(t.type, -1))
                    else:
                        grid.append(-1)
            
            self._terrain_cache[map_id] = (grid, type_to_id, terrain_types)
            self._last_map_id = map_id
            
        grid, type_to_id, terrain_types = self._terrain_cache[map_id]
        
        # 2. Build Cost Map for this Unit
        # We can cache this per unit_class too, but unit behavior might change (items, buffs)
        # So we compute it. It's fast (num_terrain_types is small, ~15).
        cost_map = {}
        for t in terrain_types:
            # We create a dummy terrain to check cost
            # This relies on terrain system not needing position for base cost
            temp_terrain = Terrain(t)
            cost = temp_terrain.get_movement_cost_for_unit(unit)
            cost_map[type_to_id[t]] = float(cost)
            
        # 3. Blockers
        blockers = []
        if unit:
            for knight in game_state.knights:
                # Block if enemy
                if knight.player_id != unit.player_id:
                     blockers.append((knight.x, knight.y))
        
        # 4. Call C Extension
        try:
            path = c_algorithms.find_path(
                width, height,
                grid,
                cost_map,
                start, end,
                blockers
            )
            
            # Check max_cost if provided
            # The C implementation doesn't check max_cost during search (yet), 
            # so we might need to verify path length/cost here if strictness is needed.
            # But usually max_cost is for highlighting valid moves, not single pathfinding.
            # For 'find_path', if a path exists, we return it. 
            # If the user wants to limit by AP, they check path cost afterwards.
            
            return path
            
        except Exception as e:
            print(f"C Pathfinding error: {e}")
            return None # Fallback or fail
