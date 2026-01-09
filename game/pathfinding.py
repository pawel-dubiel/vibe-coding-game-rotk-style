"Pathfinding abstractions for game movement"
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
import heapq
import math
from game.hex_utils import HexCoord, HexGrid
from functools import lru_cache
from game.config import USE_C_EXTENSIONS


@dataclass
class PathNode:
    """Node in a pathfinding search"""
    position: Tuple[int, int]
    g_cost: float  # Cost from start
    h_cost: float  # Heuristic cost to goal
    parent: Optional['PathNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total estimated cost"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other):
        """For priority queue comparison"""
        return self.f_cost < other.f_cost


class PathFinder(ABC):
    """Abstract base class for pathfinding algorithms"""
    
    @abstractmethod
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int], 
                  game_state, unit=None, max_cost: Optional[float] = None,
                  cost_function=None) -> Optional[List[Tuple[int, int]]]:
        """Find a path from start to end, or None if no path exists
        
        Args:
            start: Starting position (x, y)
            end: Target position (x, y)
            game_state: Current game state for checking passability
            unit: Unit requesting the path (for unit-specific constraints)
            max_cost: Maximum allowed path cost (e.g., available AP)
            cost_function: Optional function to calculate movement cost
            
        Returns:
            List of positions from start to end (excluding start), or None
        """
        pass
    
    def _get_movement_cost(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                          game_state, unit) -> float:
        """Calculate movement cost between adjacent positions"""
        # Base terrain cost
        terrain_cost = 1.0
        if game_state.terrain_map and unit:
            terrain_cost = float(game_state.terrain_map.get_movement_cost(
                to_pos[0], to_pos[1], unit
            ))
        
        final_cost = max(1.0, terrain_cost)
        # print(f"Move {from_pos} -> {to_pos}: Raw {terrain_cost}, Final {final_cost}")
        return final_cost

    def _is_position_valid(self, pos: Tuple[int, int], game_state, unit) -> bool:
        """Check if a position is valid for pathfinding"""
        x, y = pos
        
        # Check bounds
        if not (0 <= x < game_state.board_width and 0 <= y < game_state.board_height):
            return False
        
        # Check terrain passability
        if game_state.terrain_map and unit:
            if not game_state.terrain_map.is_passable(x, y, unit):
                return False
        
        # Check for enemy units blocking (but allow own position)
        if unit:
            for other in game_state.knights:
                # Skip if it's the same unit (allow own position)
                if other == unit:
                    continue
                # Block if enemy unit at this position
                if other.player_id != unit.player_id and other.x == x and other.y == y:
                    return False
        
        return True
    
    def _get_hex_neighbors(self, pos: Tuple[int, int], game_state) -> List[Tuple[int, int]]:
        """Get valid neighboring positions in hex grid"""
        # Use cached hex grid if available in pathfinder instance
        if hasattr(self, '_cached_hex_grid'):
            if self._cached_hex_grid is None or \
               self._cached_hex_grid.width != game_state.board_width or \
               self._cached_hex_grid.height != game_state.board_height:
                self._cached_hex_grid = CachedHexGrid(game_state.board_width, game_state.board_height)
            return self._cached_hex_grid.get_neighbors(pos[0], pos[1])
        
        # Fallback to original implementation
        hex_grid = HexGrid()
        hex_coord = hex_grid.offset_to_axial(pos[0], pos[1])
        neighbors = []
        
        for neighbor_hex in hex_coord.get_neighbors():
            offset_pos = hex_grid.axial_to_offset(neighbor_hex)
            if (0 <= offset_pos[0] < game_state.board_width and 
                0 <= offset_pos[1] < game_state.board_height):
                neighbors.append(offset_pos)
        
        return neighbors
    
    def _reconstruct_path(self, end_node: PathNode) -> List[Tuple[int, int]]:
        """Reconstruct path from end node"""
        path = []
        current = end_node
        while current.parent is not None:
            path.append(current.position)
            current = current.parent
        path.reverse()
        return path


class AStarPathFinder(PathFinder):
    """A* pathfinding implementation for hex grid"""
    
    def __init__(self):
        self._path_cache = {}  # Cache for computed paths
        self._cache_generation = 0  # Invalidate cache when game state changes
        self._cached_hex_grid = None  # Lazy-initialized
        self._c_pathfinder = None
        
        if USE_C_EXTENSIONS:
            try:
                from game.c_pathfinding_wrapper import CPathFinder
                self._c_pathfinder = CPathFinder()
            except ImportError:
                # Silently fail if extension not compiled, fallback to Python
                pass
    
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int], 
                  game_state, unit=None, max_cost: Optional[float] = None,
                  cost_function=None) -> Optional[List[Tuple[int, int]]]:
        """Find optimal path using A* algorithm"""
        
        # Try C implementation first
        if self._c_pathfinder and cost_function is None:
            # Note: C implementation handles caching internally or ignores it (it's fast enough)
            path = self._c_pathfinder.find_path(start, end, game_state, unit, max_cost)
            # If path is found, return it. If None, it might be no path or fallback needed?
            # Our wrapper falls back to super().find_path if C ext is missing.
            # But here self._c_pathfinder is a separate instance.
            # If C returns a path (list), return it.
            # If C returns None, it means no path found (or error caught in wrapper returning None).
            # We assume C is correct if enabled.
            return path
        
        # Use provided cost function or default
        get_cost = cost_function if cost_function else self._get_movement_cost
        
        # Check cache first (skip cache if custom cost function is used)
        if cost_function is None:
            cache_key = (start, end, unit.unit_class if unit else None, max_cost)
            if hasattr(self, '_path_cache') and cache_key in self._path_cache:
                cached_path, cached_generation = self._path_cache[cache_key]
                if cached_generation == self._cache_generation:
                    return cached_path
        
        # Check if start and end are valid
        if not self._is_position_valid(end, game_state, unit):
            return None
        
        # Initialize hex grid for distance calculations
        hex_grid = HexGrid()
        start_hex = hex_grid.offset_to_axial(start[0], start[1])
        end_hex = hex_grid.offset_to_axial(end[0], end[1])
        
        # Priority queue of nodes to explore
        open_set = []
        # Set of explored positions
        closed_set: Set[Tuple[int, int]] = set()
        # Best g_cost to reach each position
        g_costs: Dict[Tuple[int, int], float] = {}
        
        # Create start node
        start_node = PathNode(
            position=start,
            g_cost=0,
            h_cost=float(start_hex.distance_to(end_hex))
        )
        heapq.heappush(open_set, start_node)
        g_costs[start] = 0
        
        while open_set:
            current = heapq.heappop(open_set)
            
            # Found the goal
            if current.position == end:
                path = self._reconstruct_path(current)
                # Only cache if using default cost function
                if cost_function is None and hasattr(self, '_path_cache'):
                    self._path_cache[cache_key] = (path, self._cache_generation)
                return path
            
            # Skip if already processed
            if current.position in closed_set:
                continue
            
            closed_set.add(current.position)
            
            # Explore neighbors
            for neighbor_pos in self._get_hex_neighbors(current.position, game_state):
                if neighbor_pos in closed_set:
                    continue
                
                if not self._is_position_valid(neighbor_pos, game_state, unit):
                    continue
                
                # Calculate costs using selected function
                movement_cost = get_cost(current.position, neighbor_pos, game_state, unit)
                
                # Handle blocked paths (infinite cost)
                if movement_cost == float('inf'):
                    continue
                    
                tentative_g = current.g_cost + movement_cost
                
                # Check if exceeds max cost
                if max_cost is not None and tentative_g > max_cost:
                    continue
                
                # Check if this is a better path to the neighbor
                if neighbor_pos in g_costs and tentative_g >= g_costs[neighbor_pos]:
                    continue
                
                # Update best cost
                g_costs[neighbor_pos] = tentative_g
                
                # Calculate heuristic
                neighbor_hex = hex_grid.offset_to_axial(neighbor_pos[0], neighbor_pos[1])
                h_cost = float(neighbor_hex.distance_to(end_hex))
                
                # Create neighbor node
                neighbor_node = PathNode(
                    position=neighbor_pos,
                    g_cost=tentative_g,
                    h_cost=h_cost,
                    parent=current
                )
                
                heapq.heappush(open_set, neighbor_node)
        
        # No path found
        if cost_function is None and hasattr(self, '_path_cache'):
            self._path_cache[cache_key] = (None, self._cache_generation)
        return None


    def invalidate_cache(self):
        """Invalidate the path cache when game state changes"""
        self._cache_generation += 1
        # Optionally clear old cache entries to save memory
        if len(self._path_cache) > 1000:
            self._path_cache.clear()


class CachedHexGrid:
    """Cached hex grid operations for performance"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._neighbor_cache = {}
        self._hex_grid = HexGrid()
        self._precompute_neighbors()
    
    def _precompute_neighbors(self):
        """Pre-compute all hex neighbors for the grid"""
        for y in range(self.height):
            for x in range(self.width):
                hex_coord = self._hex_grid.offset_to_axial(x, y)
                neighbors = []
                for neighbor_hex in hex_coord.get_neighbors():
                    offset_pos = self._hex_grid.axial_to_offset(neighbor_hex)
                    if (0 <= offset_pos[0] < self.width and 
                        0 <= offset_pos[1] < self.height):
                        neighbors.append(offset_pos)
                self._neighbor_cache[(x, y)] = neighbors
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get cached neighbors for a position"""
        return self._neighbor_cache.get((x, y), [])


class DijkstraPathFinder(PathFinder):
    """Dijkstra's pathfinding implementation for hex grid"""
    
    def __init__(self):
        self._cached_hex_grid = None  # For performance optimization
    
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int], 
                  game_state, unit=None, max_cost: Optional[float] = None,
                  cost_function=None) -> Optional[List[Tuple[int, int]]]:
        """Find path using Dijkstra's algorithm (no heuristic)"""
        
        # Use provided cost function or default
        get_cost = cost_function if cost_function else self._get_movement_cost
        
        # Check if end is valid
        if not self._is_position_valid(end, game_state, unit):
            return None
        
        # Track costs and parents for path reconstruction
        costs: Dict[Tuple[int, int], float] = {start: 0}
        parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        # Priority queue: (cost, position)
        queue = [(0, start)]
        visited: Set[Tuple[int, int]] = set()
        
        while queue:
            current_cost, current_pos = heapq.heappop(queue)
            
            # Skip if already visited
            if current_pos in visited:
                continue
            
            visited.add(current_pos)
            
            # Found target
            if current_pos == end:
                # Reconstruct path
                path = []
                current = end
                while parents[current] is not None:
                    path.append(current)
                    current = parents[current]
                path.reverse()
                return path
            
            # Explore neighbors
            for neighbor_pos in self._get_hex_neighbors(current_pos, game_state):
                if neighbor_pos in visited:
                    continue
                
                if not self._is_position_valid(neighbor_pos, game_state, unit):
                    continue
                
                # Calculate cost
                movement_cost = get_cost(current_pos, neighbor_pos, game_state, unit)
                
                # Handle blocked paths
                if movement_cost == float('inf'):
                    continue
                    
                new_cost = current_cost + movement_cost
                
                # Check if exceeds max cost
                if max_cost is not None and new_cost > max_cost:
                    continue
                
                # Update if better path found
                if neighbor_pos not in costs or new_cost < costs[neighbor_pos]:
                    costs[neighbor_pos] = new_cost
                    parents[neighbor_pos] = current_pos
                    heapq.heappush(queue, (new_cost, neighbor_pos))
        
        # No path found
        return None
    
    def find_all_reachable(self, start: Tuple[int, int], game_state, unit=None, 
                          max_cost: float = None, cost_function=None) -> Dict[Tuple[int, int], float]:
        """Find all reachable positions within cost limit
        
        Returns:
            Dictionary mapping positions to their minimum cost from start
        """
        # Use provided cost function or default
        get_cost = cost_function if cost_function else self._get_movement_cost
        
        costs: Dict[Tuple[int, int], float] = {start: 0}
        queue = [(0, start)]
        visited: Set[Tuple[int, int]] = set()
        
        while queue:
            current_cost, current_pos = heapq.heappop(queue)
            
            if current_pos in visited:
                continue
            
            visited.add(current_pos)
            
            # Explore neighbors
            for neighbor_pos in self._get_hex_neighbors(current_pos, game_state):
                if neighbor_pos in visited:
                    continue
                
                if not self._is_position_valid(neighbor_pos, game_state, unit):
                    continue
                
                # Calculate cost
                movement_cost = get_cost(current_pos, neighbor_pos, game_state, unit)
                
                # Handle blocked paths
                if movement_cost == float('inf'):
                    continue
                    
                new_cost = current_cost + movement_cost
                
                # Check if exceeds max cost
                if max_cost is not None and new_cost > max_cost:
                    continue
                
                # Update if better path found
                if neighbor_pos not in costs or new_cost < costs[neighbor_pos]:
                    costs[neighbor_pos] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor_pos))
        
        return costs
