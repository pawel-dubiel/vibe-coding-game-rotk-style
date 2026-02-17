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
        self._terrain_cache = {}  # (map_id, revision, width, height) -> (grid, type_to_id, terrain_types)

    def _get_or_build_terrain_cache(self, game_state):
        width = game_state.board_width
        height = game_state.board_height
        map_obj = game_state.terrain_map
        map_id = id(map_obj)
        map_revision = getattr(map_obj, "revision", None)
        cache_key = (map_id, map_revision, width, height)

        if cache_key not in self._terrain_cache:
            terrain_types = list(TerrainType)
            type_to_id = {t: i for i, t in enumerate(terrain_types)}

            grid = []
            for y in range(height):
                for x in range(width):
                    terrain = map_obj.get_terrain(x, y)
                    if terrain:
                        grid.append(type_to_id[terrain.type])
                    else:
                        grid.append(-1)

            stale_keys = [key for key in self._terrain_cache if key[0] == map_id and key != cache_key]
            for stale_key in stale_keys:
                del self._terrain_cache[stale_key]

            self._terrain_cache[cache_key] = (grid, type_to_id, terrain_types)

        return self._terrain_cache[cache_key]
        
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int], 
                  game_state, unit=None, max_cost: Optional[float] = None,
                  cost_function=None) -> Optional[List[Tuple[int, int]]]:
        
        if not C_EXTENSION_AVAILABLE or cost_function is not None:
            # Fallback to Python implementation if C ext missing or custom cost function used
            # (C implementation doesn't support custom cost functions yet)
            return super().find_path(start, end, game_state, unit, max_cost, cost_function)

        width = game_state.board_width
        height = game_state.board_height
        grid, type_to_id, terrain_types = self._get_or_build_terrain_cache(game_state)
        
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
        
        # Add castles to blockers
        if hasattr(game_state, 'castles'):
            for castle in game_state.castles:
                if hasattr(castle, 'occupied_tiles'):
                    blockers.extend(castle.occupied_tiles)
        
        # 4. Call C Extension
        try:
            # Use -1.0 to indicate no cost limit in C implementation
            c_max_cost = float(max_cost) if max_cost is not None else -1.0
            
            path = c_algorithms.find_path(
                width, height,
                grid,
                cost_map,
                start, end,
                blockers,
                c_max_cost
            )
            
            return path
            
        except Exception as e:
            print(f"C Pathfinding error: {e}")
            return None # Fallback or fail

    def find_all_reachable(self, start: Tuple[int, int], game_state, unit=None, 
                          max_cost: float = None, cost_function=None) -> Dict[Tuple[int, int], float]:
        """Find all reachable positions using C extension"""
        
        if not C_EXTENSION_AVAILABLE:
            return None

        width = game_state.board_width
        height = game_state.board_height
        grid, type_to_id, terrain_types = self._get_or_build_terrain_cache(game_state)
        
        # 2. Build Cost Map for this Unit
        cost_map = {}
        for t in terrain_types:
            temp_terrain = Terrain(t)
            cost = temp_terrain.get_movement_cost_for_unit(unit)
            cost_map[type_to_id[t]] = float(cost)
            
        # 3. Blockers
        blockers = []
        if unit:
            for knight in game_state.knights:
                if knight.player_id != unit.player_id:
                     blockers.append((knight.x, knight.y))
        
        # Add castles to blockers
        if hasattr(game_state, 'castles'):
            for castle in game_state.castles:
                if hasattr(castle, 'occupied_tiles'):
                    blockers.extend(castle.occupied_tiles)
                    
        # 4. Build ZOC Map (if unit provided)
        zoc_map = None
        if unit:
            zoc_map = []
            from game.systems.engagement import EngagementSystem
            
            # Optimization: Pre-calculate ZOC sources
            zoc_sources = []
            for enemy in game_state.knights:
                if enemy.player_id != unit.player_id and enemy.has_zone_of_control():
                    zoc_sources.append(enemy)
            
            # Only build map if there are enemies with ZOC
            if zoc_sources:
                for y in range(height):
                    for x in range(width):
                        in_zoc = False
                        for enemy in zoc_sources:
                            dx = abs(x - enemy.x)
                            dy = abs(y - enemy.y)
                            if dx <= 1 and dy <= 1 and (dx + dy > 0):
                                in_zoc = True
                                break
                        zoc_map.append(1 if in_zoc else 0)
        
        # 5. Call C Extension
        try:
            c_max_cost = float(max_cost) if max_cost is not None else 999.0
            
            reachable = c_algorithms.find_reachable(
                width, height,
                grid,
                cost_map,
                start,
                blockers,
                c_max_cost,
                zoc_map
            )
            
            return reachable
            
        except Exception as e:
            print(f"C Reachable finding error: {e}")
            return None
