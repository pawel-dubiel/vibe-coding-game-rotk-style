"""Test script for save/load functionality"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame
from game.save_manager import SaveManager
from game.game_state import GameState
from game.entities.knight import KnightClass


def test_save_load():
    """Test save and load functionality"""
    print("Testing Save/Load System...")
    
    # Initialize pygame (needed for GameState)
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Create save manager
    save_manager = SaveManager()
    
    # Create a game state
    print("\n1. Creating test game state...")
    battle_config = {
        'board_size': (16, 12),
        'knights': 3,
        'castles': 1
    }
    game_state = GameState(battle_config, vs_ai=True)
    
    # Modify game state to test persistence
    game_state.turn_number = 5
    game_state.current_player = 2
    
    # Move a knight
    if game_state.knights:
        knight = game_state.knights[0]
        print(f"   - Knight '{knight.name}' at ({knight.x}, {knight.y})")
        knight.x += 1
        knight.y += 1
        knight.has_moved = True
        knight.action_points = 2
        print(f"   - Moved to ({knight.x}, {knight.y})")
    
    # Test save
    print("\n2. Saving game to slot 1...")
    game_state.prepare_for_save()
    save_result = save_manager.save_game(game_state, 1, "Test Save")
    print(f"   - {save_result['message']}")
    
    # Test save metadata
    print("\n3. Checking save slots...")
    slots = save_manager.get_save_slots()
    for i, slot in enumerate(slots):
        if slot:
            print(f"   - Slot {i+1}: {slot.save_name} (Turn {slot.turn_number}, {slot.knight_count} units)")
        else:
            print(f"   - Slot {i+1}: Empty")
    
    # Test load
    print("\n4. Loading game from slot 1...")
    load_result = save_manager.load_game(1)
    if load_result['success']:
        print(f"   - {load_result['message']}")
        
        # Create new game state and restore
        new_game_state = GameState(battle_config, vs_ai=False)
        new_game_state.restore_after_load(load_result['data'])
        
        # Verify loaded data
        print("\n5. Verifying loaded data...")
        print(f"   - Turn number: {new_game_state.turn_number} (expected: 5)")
        print(f"   - Current player: {new_game_state.current_player} (expected: 2)")
        print(f"   - Knight count: {len(new_game_state.knights)}")
        
        if new_game_state.knights:
            knight = new_game_state.knights[0]
            print(f"   - Knight '{knight.name}' at ({knight.x}, {knight.y})")
            print(f"   - Has moved: {knight.has_moved}")
            print(f"   - Action points: {knight.action_points}")
    else:
        print(f"   - Load failed: {load_result['message']}")
    
    # Test overwrite
    print("\n6. Testing overwrite...")
    game_state.turn_number = 10
    save_result = save_manager.save_game(game_state, 1, "Overwritten Save")
    print(f"   - {save_result['message']}")
    
    # Test delete
    print("\n7. Testing delete...")
    delete_result = save_manager.delete_save(1)
    print(f"   - {delete_result['message']}")
    
    # Verify deletion
    slots = save_manager.get_save_slots()
    if slots[0] is None:
        print("   - Slot 1 is now empty (correct)")
    else:
        print("   - ERROR: Slot 1 still has data")
    
    print("\nTest complete!")
    
    # Cleanup pygame
    pygame.quit()


if __name__ == "__main__":
    test_save_load()