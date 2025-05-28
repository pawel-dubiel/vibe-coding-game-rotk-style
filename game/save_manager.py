"""Save and load game functionality with multiple save slots"""
import pickle
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import shutil


@dataclass
class SaveMetadata:
    """Metadata for a save file"""
    slot_number: int
    save_name: str
    timestamp: str
    turn_number: int
    current_player: int
    knight_count: int
    vs_ai: bool
    board_size: tuple[int, int]
    

class SaveManager:
    """Manages game saves with multiple slots"""
    
    # Default save directory relative to game root
    SAVE_DIR = "saves"
    METADATA_FILE = "save_metadata.json"
    MAX_SLOTS = 10
    
    def __init__(self):
        self.save_dir = self._get_save_directory()
        self._ensure_save_directory()
        self.metadata = self._load_metadata()
        
    def _get_save_directory(self) -> str:
        """Get the absolute path to the save directory"""
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to game root
        game_root = os.path.dirname(current_dir)
        # Create saves directory path
        return os.path.join(game_root, self.SAVE_DIR)
        
    def _ensure_save_directory(self):
        """Create save directory if it doesn't exist"""
        os.makedirs(self.save_dir, exist_ok=True)
        
    def _get_save_filename(self, slot: int) -> str:
        """Get filename for a save slot"""
        return os.path.join(self.save_dir, f"save_slot_{slot}.pkl")
        
    def _get_metadata_path(self) -> str:
        """Get path to metadata file"""
        return os.path.join(self.save_dir, self.METADATA_FILE)
        
    def _load_metadata(self) -> Dict[int, SaveMetadata]:
        """Load save metadata from JSON file"""
        metadata_path = self._get_metadata_path()
        if not os.path.exists(metadata_path):
            return {}
            
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                # Convert back to SaveMetadata objects
                metadata = {}
                for slot_str, meta_dict in data.items():
                    slot = int(slot_str)
                    metadata[slot] = SaveMetadata(
                        slot_number=slot,
                        save_name=meta_dict['save_name'],
                        timestamp=meta_dict['timestamp'],
                        turn_number=meta_dict['turn_number'],
                        current_player=meta_dict['current_player'],
                        knight_count=meta_dict['knight_count'],
                        vs_ai=meta_dict['vs_ai'],
                        board_size=tuple(meta_dict['board_size'])
                    )
                return metadata
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}
            
    def _save_metadata(self):
        """Save metadata to JSON file"""
        try:
            # Convert SaveMetadata objects to dicts
            data = {}
            for slot, meta in self.metadata.items():
                data[str(slot)] = {
                    'save_name': meta.save_name,
                    'timestamp': meta.timestamp,
                    'turn_number': meta.turn_number,
                    'current_player': meta.current_player,
                    'knight_count': meta.knight_count,
                    'vs_ai': meta.vs_ai,
                    'board_size': list(meta.board_size)
                }
                
            with open(self._get_metadata_path(), 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
            
    def get_save_slots(self) -> List[Optional[SaveMetadata]]:
        """Get list of save slots with their metadata (None for empty slots)"""
        slots = []
        for i in range(1, self.MAX_SLOTS + 1):
            if i in self.metadata:
                slots.append(self.metadata[i])
            else:
                slots.append(None)
        return slots
        
    def save_game(self, game_state, slot: int, save_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Save game state to specified slot
        
        Args:
            game_state: The GameState object to save
            slot: Save slot number (1-10)
            save_name: Optional custom save name
            
        Returns:
            Dict with 'success' bool and 'message' string
        """
        if not 1 <= slot <= self.MAX_SLOTS:
            return {'success': False, 'message': f'Invalid slot number: {slot}'}
            
        try:
            # Create save data dictionary with all necessary state
            save_data = {
                'board_width': game_state.board_width,
                'board_height': game_state.board_height,
                'tile_size': game_state.tile_size,
                'current_player': game_state.current_player,
                'turn_number': game_state.turn_number,
                'vs_ai': game_state.vs_ai,
                'ai_difficulty': game_state.ai_player.difficulty if game_state.ai_player else None,
                
                # Units and castles
                'knights': self._serialize_knights(game_state.knights),
                'castles': self._serialize_castles(game_state.castles),
                
                # Terrain
                'terrain_map': self._serialize_terrain(game_state.terrain_map),
                
                # Fog of war
                'fog_of_war': self._serialize_fog_of_war(game_state.fog_of_war),
                
                # Camera position
                'camera_x': game_state.camera_x,
                'camera_y': game_state.camera_y,
                
                # Messages
                'messages': game_state.messages,
                
                # Movement history
                'movement_history': game_state.movement_history,
            }
            
            # Save to file
            filename = self._get_save_filename(slot)
            with open(filename, 'wb') as f:
                pickle.dump(save_data, f)
                
            # Update metadata
            if save_name is None:
                save_name = f"Turn {game_state.turn_number}"
                
            self.metadata[slot] = SaveMetadata(
                slot_number=slot,
                save_name=save_name,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                turn_number=game_state.turn_number,
                current_player=game_state.current_player,
                knight_count=len(game_state.knights),
                vs_ai=game_state.vs_ai,
                board_size=(game_state.board_width, game_state.board_height)
            )
            self._save_metadata()
            
            return {'success': True, 'message': f'Game saved to slot {slot}'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error saving game: {str(e)}'}
            
    def load_game(self, slot: int) -> Dict[str, Any]:
        """
        Load game state from specified slot
        
        Args:
            slot: Save slot number (1-10)
            
        Returns:
            Dict with 'success' bool, 'message' string, and 'data' dict if successful
        """
        if not 1 <= slot <= self.MAX_SLOTS:
            return {'success': False, 'message': f'Invalid slot number: {slot}'}
            
        if slot not in self.metadata:
            return {'success': False, 'message': f'No save in slot {slot}'}
            
        filename = self._get_save_filename(slot)
        if not os.path.exists(filename):
            return {'success': False, 'message': f'Save file missing for slot {slot}'}
            
        try:
            with open(filename, 'rb') as f:
                save_data = pickle.load(f)
                
            return {
                'success': True, 
                'message': f'Game loaded from slot {slot}',
                'data': save_data
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error loading game: {str(e)}'}
            
    def delete_save(self, slot: int) -> Dict[str, Any]:
        """Delete a save file"""
        if not 1 <= slot <= self.MAX_SLOTS:
            return {'success': False, 'message': f'Invalid slot number: {slot}'}
            
        if slot not in self.metadata:
            return {'success': False, 'message': f'No save in slot {slot}'}
            
        try:
            filename = self._get_save_filename(slot)
            if os.path.exists(filename):
                os.remove(filename)
                
            del self.metadata[slot]
            self._save_metadata()
            
            return {'success': True, 'message': f'Save deleted from slot {slot}'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error deleting save: {str(e)}'}
            
    def backup_save(self, slot: int) -> Dict[str, Any]:
        """Create a backup of a save file"""
        if not 1 <= slot <= self.MAX_SLOTS:
            return {'success': False, 'message': f'Invalid slot number: {slot}'}
            
        if slot not in self.metadata:
            return {'success': False, 'message': f'No save in slot {slot}'}
            
        try:
            filename = self._get_save_filename(slot)
            backup_dir = os.path.join(self.save_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"save_slot_{slot}_backup_{timestamp}.pkl")
            
            shutil.copy2(filename, backup_file)
            
            return {'success': True, 'message': f'Backup created for slot {slot}'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating backup: {str(e)}'}
            
    def _serialize_knights(self, knights):
        """Serialize knight data for saving"""
        serialized = []
        for knight in knights:
            data = {
                'name': knight.name,
                'unit_class': knight.unit_class.value,
                'x': knight.x,
                'y': knight.y,
                'player_id': knight.player_id,
                'has_moved': knight.has_moved,
                'has_acted': knight.has_acted,
                'has_used_special': knight.has_used_special,
                'max_action_points': knight.max_action_points,
                'action_points': knight.action_points,
                
                # Stats
                'current_soldiers': knight.stats.stats.current_soldiers,
                'max_soldiers': knight.stats.stats.max_soldiers,
                'morale': knight.stats.stats.morale,
                'will': knight.stats.stats.will,
                'max_will': knight.stats.stats.max_will,
                
                # State flags
                'is_garrisoned': knight.is_garrisoned,
                'is_disrupted': knight.is_disrupted,
                'is_routing': knight.is_routing,
                'in_enemy_zoc': knight.in_enemy_zoc,
                'is_engaged_in_combat': knight.is_engaged_in_combat,
                
                # Facing
                'facing': knight.facing.facing.value if hasattr(knight, 'facing') else None,
                
                # Generals
                'generals': self._serialize_generals(knight.generals) if hasattr(knight, 'generals') else []
            }
            serialized.append(data)
        return serialized
        
    def _serialize_generals(self, general_roster):
        """Serialize general roster data"""
        generals = []
        for general in general_roster.generals:
            # Serialize abilities by their class names
            ability_names = []
            for ability in general.abilities:
                ability_names.append(ability.__class__.__name__)
                
            generals.append({
                'name': general.name,
                'title': general.title,
                'level': general.level,
                'experience': general.experience,
                'abilities': ability_names
            })
        return generals
        
    def _serialize_castles(self, castles):
        """Serialize castle data"""
        serialized = []
        for castle in castles:
            data = {
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
            serialized.append(data)
        return serialized
        
    def _serialize_terrain(self, terrain_map):
        """Serialize terrain map data"""
        if not terrain_map:
            return None
            
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
        
    def _serialize_fog_of_war(self, fog_of_war):
        """Serialize fog of war data"""
        if not fog_of_war:
            return None
            
        fog_data = {
            'width': fog_of_war.width,
            'height': fog_of_war.height,
            'num_players': fog_of_war.num_players,
            'visibility_maps': {}
        }
        
        # Save visibility state for each player
        for player_id, vis_map in fog_of_war.visibility_maps.items():
            fog_data['visibility_maps'][player_id] = {}
            for coords, state in vis_map.items():
                # Convert tuple key to string for JSON serialization
                key = f"{coords[0]},{coords[1]}"
                fog_data['visibility_maps'][player_id][key] = state.value
                
        return fog_data