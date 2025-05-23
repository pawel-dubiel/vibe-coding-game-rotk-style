"""Test IGameState interface implementations"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.interfaces.game_state import IGameState
from game.test_utils.mock_game_state import MockGameState
from game.entities.unit_factory import UnitFactory

def test_mock_game_state_implements_interface():
    """Test that MockGameState properly implements IGameState"""
    # Create instance
    mock_state = MockGameState(board_width=15, board_height=10)
    
    # Verify it's an instance of IGameState
    assert isinstance(mock_state, IGameState), "MockGameState should implement IGameState"
    
    # Verify required attributes exist
    assert hasattr(mock_state, 'board_width'), "Missing board_width"
    assert hasattr(mock_state, 'board_height'), "Missing board_height"
    assert hasattr(mock_state, 'knights'), "Missing knights"
    assert hasattr(mock_state, 'castles'), "Missing castles"
    assert hasattr(mock_state, 'terrain_map'), "Missing terrain_map"
    assert hasattr(mock_state, 'current_player'), "Missing current_player"
    
    # Verify values
    assert mock_state.board_width == 15
    assert mock_state.board_height == 10
    assert mock_state.current_player == 1
    assert len(mock_state.knights) == 0
    assert len(mock_state.castles) == 0
    assert mock_state.terrain_map is not None
    
    print("✓ MockGameState implements IGameState correctly")

def test_mock_game_state_methods():
    """Test MockGameState methods"""
    mock_state = MockGameState()
    
    # Test add_knight
    knight = UnitFactory.create_archer("Test Archer", 5, 5)
    knight.player_id = 1
    mock_state.add_knight(knight)
    
    assert len(mock_state.knights) == 1
    assert mock_state.knights[0] == knight
    
    # Test get_knight_at
    found_knight = mock_state.get_knight_at(5, 5)
    assert found_knight == knight
    
    # Test not found
    not_found = mock_state.get_knight_at(10, 10)
    assert not_found is None
    
    print("✓ MockGameState methods work correctly")

def test_interface_with_multiple_implementations():
    """Test that we can use different IGameState implementations interchangeably"""
    
    def process_game_state(game_state: IGameState):
        """Function that works with any IGameState implementation"""
        # Should work with any implementation
        width = game_state.board_width
        height = game_state.board_height
        knights = game_state.knights
        
        # Add a knight
        knight = UnitFactory.create_warrior("Test", width // 2, height // 2)
        knight.player_id = game_state.current_player
        
        if hasattr(game_state, 'add_knight'):
            game_state.add_knight(knight)
        else:
            game_state.knights.append(knight)
        
        # Find knight
        found = game_state.get_knight_at(width // 2, height // 2)
        return found is not None
    
    # Test with MockGameState
    mock_state = MockGameState()
    result = process_game_state(mock_state)
    assert result == True
    
    print("✓ Interface allows polymorphic usage")

if __name__ == "__main__":
    print("Testing IGameState interface...\n")
    
    test_mock_game_state_implements_interface()
    test_mock_game_state_methods()
    test_interface_with_multiple_implementations()
    
    print("\nAll interface tests passed!")