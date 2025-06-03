"""
Game state serialization and deserialization for save/load functionality.

Handles converting complex game objects to/from serializable data structures.
Extracted from GameState for better separation of concerns and testability.
"""
from typing import Dict, Any, List
from game.entities.unit import Unit
from game.entities.castle import Castle
from game.terrain import TerrainMap
from game.visibility import FogOfWar
from game.ai.ai_player import AIPlayer


class StateSerializer:
    """Handles game state serialization and deserialization for save/load."""
    
    def prepare_for_save(self, game_state) -> None:
        """Prepare game state for saving by cleaning up non-serializable objects."""
        # Clear any animations that can't be serialized
        if hasattr(game_state, 'animation_coordinator'):
            game_state.animation_coordinator.clear_animations()
    
    def serialize_game_state(self, game_state) -> Dict[str, Any]:
        """
        Convert game state to serializable dictionary.
        
        Args:
            game_state: The GameState instance to serialize
            
        Returns:
            Dictionary containing all serializable game state data
        """
        return {
            # Basic game properties
            'board_width': game_state.board_width,
            'board_height': game_state.board_height,
            'tile_size': game_state.tile_size,
            'current_player': game_state.current_player,
            'turn_number': game_state.turn_number,
            'vs_ai': game_state.vs_ai,
            'ai_difficulty': game_state.ai_player.difficulty if game_state.ai_player else None,
            
            # Camera state
            'camera_x': game_state.camera_x,
            'camera_y': game_state.camera_y,
            
            # Messages and history
            'messages': getattr(game_state, 'messages', []),
            'movement_history': getattr(game_state, 'movement_history', []),
            
            # Game entities
            'knights': self._serialize_units(game_state.knights),
            'castles': self._serialize_castles(game_state.castles),
            
            # World state
            'terrain_map': self._serialize_terrain_map(game_state.terrain_map),
            'fog_of_war': self._serialize_fog_of_war(game_state.fog_of_war)
        }
    
    def deserialize_game_state(self, save_data: Dict[str, Any], game_state) -> None:
        """
        Restore game state from serialized data.
        
        Args:
            save_data: Dictionary containing serialized game state
            game_state: The GameState instance to restore into
        """
        from game.entities.unit_factory import UnitFactory
        from game.entities.castle import Castle
        from game.entities.knight import KnightClass
        from game.components.facing import FacingDirection
        from game.terrain import TerrainType, TerrainMap
        from game.visibility import FogOfWar, VisibilityState
        from game.ai.ai_player import AIPlayer
        
        # Restore basic properties
        game_state.board_width = save_data['board_width']
        game_state.board_height = save_data['board_height']
        game_state.tile_size = save_data['tile_size']
        game_state.current_player = save_data['current_player']
        game_state.turn_number = save_data['turn_number']
        game_state.vs_ai = save_data['vs_ai']
        
        # Restore AI player
        if game_state.vs_ai and save_data['ai_difficulty']:
            game_state.ai_player = AIPlayer(2, save_data['ai_difficulty'])
        else:
            game_state.ai_player = None
            
        # Restore camera position
        game_state.camera_x = save_data['camera_x']
        game_state.camera_y = save_data['camera_y']
        
        # Restore messages and history
        game_state.messages = save_data['messages']
        game_state.movement_history = save_data['movement_history']
        
        # Clear existing entities
        game_state.knights.clear()
        game_state.castles.clear()
        
        # Restore units
        self._deserialize_units(save_data['knights'], game_state)
        
        # Restore castles
        self._deserialize_castles(save_data['castles'], game_state)
        
        # Link garrisoned units to castles
        self._link_garrisoned_units(save_data['castles'], game_state)
        
        # Restore terrain map
        self._deserialize_terrain_map(save_data['terrain_map'], game_state)
        
        # Restore fog of war
        self._deserialize_fog_of_war(save_data['fog_of_war'], game_state)
    
    def _serialize_units(self, units: List[Unit]) -> List[Dict[str, Any]]:
        """Serialize list of units to dictionaries."""
        serialized_units = []
        
        for unit in units:
            unit_data = {
                'name': unit.name,
                'unit_class': unit.unit_class.value,
                'x': unit.x,
                'y': unit.y,
                'player_id': unit.player_id,
                'has_moved': unit.has_moved,
                'has_attacked': unit.has_attacked,
                'action_points': unit.action_points,
                'max_action_points': unit.max_action_points,
                'health': unit.health,
                'max_health': unit.max_health,
                'morale': unit.morale,
                'max_morale': unit.max_morale,
                'is_routing': unit.is_routing,
                'facing_direction': unit.facing.direction.value if hasattr(unit, 'facing') else 0,
                'garrison_location': unit.garrison_location.center_x if unit.garrison_location else None,
                'generals': []
            }
            
            # Serialize generals
            if hasattr(unit, 'generals') and unit.generals:
                for general in unit.generals.generals:
                    general_data = {
                        'name': general.name,
                        'general_type': general.general_type.value,
                        'level': general.level,
                        'experience': general.experience
                    }
                    unit_data['generals'].append(general_data)
            
            serialized_units.append(unit_data)
        
        return serialized_units
    
    def _serialize_castles(self, castles: List[Castle]) -> List[Dict[str, Any]]:
        """Serialize list of castles to dictionaries."""
        serialized_castles = []
        
        for castle in castles:
            castle_data = {
                'center_x': castle.center_x,
                'center_y': castle.center_y,
                'player_id': castle.player_id,
                'max_health': castle.max_health,
                'health': castle.health,
                'defense': castle.defense,
                'arrow_damage_per_archer': castle.arrow_damage_per_archer,
                'arrow_range': castle.arrow_range,
                'garrison_slots': castle.garrison_slots,
                'garrisoned_units': [unit.name for unit in castle.garrisoned_units]
            }
            serialized_castles.append(castle_data)
        
        return serialized_castles
    
    def _serialize_terrain_map(self, terrain_map: TerrainMap) -> List[Dict[str, Any]]:
        """Serialize terrain map to list of terrain data."""
        if not terrain_map:
            return []
            
        terrain_data = []
        for x in range(terrain_map.width):
            for y in range(terrain_map.height):
                terrain = terrain_map.get_terrain(x, y)
                if terrain:
                    terrain_data.append({
                        'x': x,
                        'y': y,
                        'type': terrain.type.value
                    })
        
        return terrain_data
    
    def _serialize_fog_of_war(self, fog_of_war: FogOfWar) -> Dict[str, Any]:
        """Serialize fog of war state."""
        if not fog_of_war:
            return {}
            
        visibility_maps = {}
        for player_id, vis_map in fog_of_war.visibility_maps.items():
            visibility_maps[str(player_id)] = {
                f"{x},{y}": state.value for (x, y), state in vis_map.items()
            }
        
        return {
            'width': fog_of_war.width,
            'height': fog_of_war.height,
            'num_players': fog_of_war.num_players,
            'visibility_maps': visibility_maps
        }
    
    def _deserialize_units(self, units_data: List[Dict[str, Any]], game_state) -> None:
        """Deserialize units from data and add to game state."""
        from game.entities.unit_factory import UnitFactory
        from game.entities.knight import KnightClass
        from game.components.facing import FacingDirection
        from game.components.generals import GeneralType, General
        
        for unit_data in units_data:
            # Create unit with proper class
            unit_class = KnightClass(unit_data['unit_class'])
            unit = UnitFactory.create_unit(
                unit_data['name'],
                unit_class,
                unit_data['x'],
                unit_data['y'],
                add_generals=False  # We'll restore generals separately
            )
            
            # Restore unit properties
            unit.player_id = unit_data['player_id']
            unit.has_moved = unit_data['has_moved']
            unit.has_attacked = unit_data['has_attacked']
            unit.action_points = unit_data['action_points']
            unit.max_action_points = unit_data['max_action_points']
            unit.health = unit_data['health']
            unit.max_health = unit_data['max_health']
            unit.morale = unit_data['morale']
            unit.max_morale = unit_data['max_morale']
            unit.is_routing = unit_data['is_routing']
            
            # Restore facing direction
            if hasattr(unit, 'facing') and 'facing_direction' in unit_data:
                unit.facing.direction = FacingDirection(unit_data['facing_direction'])
            
            # Restore generals
            if 'generals' in unit_data:
                for general_data in unit_data['generals']:
                    general_type = GeneralType(general_data['general_type'])
                    general = General(
                        name=general_data['name'],
                        general_type=general_type,
                        abilities=[],  # Empty for now
                        level=general_data['level'],
                        experience=general_data['experience']
                    )
                    unit.generals.add_general(general)
            
            game_state.knights.append(unit)
    
    def _deserialize_castles(self, castles_data: List[Dict[str, Any]], game_state) -> None:
        """Deserialize castles from data and add to game state."""
        from game.entities.castle import Castle
        
        for castle_data in castles_data:
            castle = Castle(
                castle_data['center_x'],
                castle_data['center_y'],
                castle_data['player_id']
            )
            
            # Restore castle properties
            castle.max_health = castle_data['max_health']
            castle.health = castle_data['health']
            castle.defense = castle_data['defense']
            castle.arrow_damage_per_archer = castle_data['arrow_damage_per_archer']
            castle.arrow_range = castle_data['arrow_range']
            castle.garrison_slots = castle_data['garrison_slots']
            
            game_state.castles.append(castle)
    
    def _link_garrisoned_units(self, castles_data: List[Dict[str, Any]], game_state) -> None:
        """Link garrisoned units to their castles after deserialization."""
        for castle, castle_data in zip(game_state.castles, castles_data):
            for unit_name in castle_data['garrisoned_units']:
                for unit in game_state.knights:
                    if unit.name == unit_name:
                        castle.garrisoned_units.append(unit)
                        unit.garrison_location = castle
                        break
    
    def _deserialize_terrain_map(self, terrain_data: List[Dict[str, Any]], game_state) -> None:
        """Deserialize terrain map from data."""
        from game.terrain import TerrainType, TerrainMap
        
        if terrain_data:
            game_state.terrain_map = TerrainMap(game_state.board_width, game_state.board_height)
            for terrain_entry in terrain_data:
                terrain_type = TerrainType(terrain_entry['type'])
                game_state.terrain_map.set_terrain(
                    terrain_entry['x'],
                    terrain_entry['y'],
                    terrain_type
                )
        else:
            game_state.terrain_map = TerrainMap(game_state.board_width, game_state.board_height)
    
    def _deserialize_fog_of_war(self, fog_data: Dict[str, Any], game_state) -> None:
        """Deserialize fog of war from data."""
        from game.visibility import FogOfWar, VisibilityState
        
        if fog_data:
            game_state.fog_of_war = FogOfWar(
                fog_data['width'],
                fog_data['height'],
                fog_data['num_players']
            )
            
            # Restore visibility states
            for player_id_str, vis_map in fog_data['visibility_maps'].items():
                player_id = int(player_id_str)
                for coord_str, state_value in vis_map.items():
                    x, y = map(int, coord_str.split(','))
                    game_state.fog_of_war.visibility_maps[player_id][(x, y)] = VisibilityState(state_value)
        else:
            game_state.fog_of_war = FogOfWar(game_state.board_width, game_state.board_height, 2)