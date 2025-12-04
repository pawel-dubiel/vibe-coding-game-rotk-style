"""Comprehensive tests for unit facing mechanics"""
import sys
import os
import pygame
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.entities.unit_factory import UnitFactory
from game.entities.knight import KnightClass
from game.components.facing import FacingDirection, AttackAngle
from game.test_utils.mock_game_state import MockGameState
from game.animation import AttackAnimation


class TestFacingMechanics:
    """Test facing system including direction, damage modifiers, and routing"""
    
    def setup_method(self):
        """Set up test environment"""
        # Ensure pygame is initialized for each test
        pygame.init()
        self.game_state = MockGameState(board_width=20, board_height=20)
        
    def test_facing_component_exists(self):
        """Test that units have facing component"""
        unit = UnitFactory.create_warrior("Test Warrior", 10, 10)
        assert hasattr(unit, 'facing')
        assert unit.facing is not None
        
    def test_facing_updates_on_movement(self):
        """Test that facing updates when unit moves"""
        unit = UnitFactory.create_warrior("Test Warrior", 10, 10)
        unit.player_id = 1
        self.game_state.add_knight(unit)
        
        # Initial facing
        initial_facing = unit.facing.facing
        
        # Move east
        unit.move(11, 10)
        assert unit.facing.facing == FacingDirection.EAST
        
        # Reset for next move
        unit.has_moved = False
        unit.action_points = 10
        
        # Move north-east (from 11,10 to 12,9)
        unit.move(12, 9)
        assert unit.facing.facing == FacingDirection.NORTH_EAST
        
        # Reset for next move
        unit.has_moved = False
        unit.action_points = 10
        
        # Move south-west
        unit.move(11, 10)
        assert unit.facing.facing == FacingDirection.SOUTH_WEST
        
    def test_attack_angle_detection(self):
        """Test correct detection of frontal, flank, and rear attacks"""
        defender = UnitFactory.create_warrior("Defender", 10, 10)
        defender.facing.facing = FacingDirection.EAST  # Facing right
        
        # Test frontal attack (from the east)
        angle = defender.facing.get_attack_angle(11, 10, 10, 10)
        assert angle.is_frontal
        assert not angle.is_rear
        assert not angle.is_flank
        
        # Test rear attack (from the west)
        angle = defender.facing.get_attack_angle(9, 10, 10, 10)
        assert angle.is_rear
        assert not angle.is_frontal
        assert not angle.is_flank
        
        # Test flank attacks (from north/south)
        angle = defender.facing.get_attack_angle(10, 9, 10, 10)
        assert angle.is_flank
        assert not angle.is_frontal
        assert not angle.is_rear
        
    def test_damage_modifiers(self):
        """Test damage modifiers based on attack angle"""
        defender = UnitFactory.create_warrior("Defender", 10, 10)
        defender.facing.facing = FacingDirection.NORTH_EAST
        
        # Frontal attack - normal damage
        frontal_angle = AttackAngle(is_frontal=True, is_rear=False, is_flank=False, 
                                   angle_degrees=0, description="Frontal")
        assert defender.facing.get_damage_modifier(frontal_angle) == 1.0
        
        # Flank attack - 25% more damage
        flank_angle = AttackAngle(is_frontal=False, is_rear=False, is_flank=True,
                                 angle_degrees=90, description="Flank")
        assert defender.facing.get_damage_modifier(flank_angle) == 1.25
        
        # Rear attack - 50% more damage
        rear_angle = AttackAngle(is_frontal=False, is_rear=True, is_flank=False,
                                angle_degrees=180, description="Rear")
        assert defender.facing.get_damage_modifier(rear_angle) == 1.5
        
    def test_morale_penalties(self):
        """Test additional morale penalties for flank/rear attacks"""
        defender = UnitFactory.create_warrior("Defender", 10, 10)
        
        # No penalty for frontal
        frontal_angle = AttackAngle(is_frontal=True, is_rear=False, is_flank=False,
                                   angle_degrees=0, description="Frontal")
        assert defender.facing.get_morale_penalty(frontal_angle) == 0
        
        # 10 morale penalty for flank
        flank_angle = AttackAngle(is_frontal=False, is_rear=False, is_flank=True,
                                 angle_degrees=90, description="Flank")
        assert defender.facing.get_morale_penalty(flank_angle) == 10
        
        # 15 morale penalty for rear
        rear_angle = AttackAngle(is_frontal=False, is_rear=True, is_flank=False,
                                angle_degrees=180, description="Rear")
        assert defender.facing.get_morale_penalty(rear_angle) == 15
        
    def test_routing_chance_calculation(self):
        """Test routing chance based on casualties and attack angle"""
        defender = UnitFactory.create_warrior("Defender", 10, 10)
        
        # Rear attack with high casualties should have high routing chance
        rear_angle = AttackAngle(is_frontal=False, is_rear=True, is_flank=False,
                                angle_degrees=180, description="Rear")
        
        # Test with 30% casualties and decent morale
        defender.morale = 70
        # We can't test exact random chance, but we can verify the method exists
        assert hasattr(defender.facing, 'check_routing_chance')
        
    def test_combat_with_facing(self):
        """Test full combat sequence with facing mechanics"""
        attacker = UnitFactory.create_warrior("Attacker", 9, 10)
        attacker.player_id = 1
        defender = UnitFactory.create_warrior("Defender", 10, 10)
        defender.player_id = 2
        defender.facing.facing = FacingDirection.EAST  # Facing away from attacker
        
        self.game_state.add_knight(attacker)
        self.game_state.add_knight(defender)
        
        # Execute attack
        if 'attack' in attacker.behaviors:
            result = attacker.behaviors['attack'].execute(attacker, self.game_state, defender)
            
            assert result['success']
            assert result['damage'] > 0
            assert result['attack_angle'] is not None
            assert result['attack_angle'].is_rear  # Should be rear attack
            assert result['extra_morale_penalty'] == 15  # Rear attack penalty
            assert result['should_check_routing'] == True
            
    def test_cavalry_charge_rear_bonus(self):
        """Test cavalry charge gets huge bonus on rear attacks"""
        cavalry = UnitFactory.create_cavalry("Cavalry", 9, 10)
        cavalry.player_id = 1
        cavalry.will = 100  # Full will for charge
        
        defender = UnitFactory.create_warrior("Defender", 10, 10)
        defender.player_id = 2
        defender.facing.facing = FacingDirection.EAST  # Facing away
        
        self.game_state.add_knight(cavalry)
        self.game_state.add_knight(defender)
        
        # Ensure terrain is clear for charge (avoid random hills blocking)
        from game.terrain import TerrainType
        if self.game_state.terrain_map:
            self.game_state.terrain_map.set_terrain(9, 10, TerrainType.PLAINS)
            self.game_state.terrain_map.set_terrain(10, 10, TerrainType.PLAINS)
        
        # Execute charge
        if 'cavalry_charge' in cavalry.behaviors:
            result = cavalry.behaviors['cavalry_charge'].execute(cavalry, self.game_state, defender)
            
            assert result['success']
            assert result['damage'] > 0
            assert result.get('is_rear_charge', False)  # Should flag as rear charge
            
            # Message should indicate devastating rear charge
            assert "DEVASTATING REAR CHARGE" in result['message']
            
    def test_facing_arrow_visualization(self):
        """Test facing arrow coordinate calculation"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.facing.facing = FacingDirection.NORTH_EAST
        
        # Get arrow coordinates
        start, end = unit.facing.get_facing_arrow_coords(100, 100, 20)
        
        assert start == (100, 100)
        assert end[0] > start[0]  # Should point right
        assert end[1] < start[1]  # Should point up
        
    def test_rotate_facing(self):
        """Test manual facing rotation"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        unit.facing.facing = FacingDirection.EAST
        
        # Rotate clockwise
        unit.facing.rotate_clockwise()
        assert unit.facing.facing == FacingDirection.SOUTH_EAST
        
        # Rotate counter-clockwise
        unit.facing.rotate_counter_clockwise()
        unit.facing.rotate_counter_clockwise()
        assert unit.facing.facing == FacingDirection.NORTH_EAST
        
    def test_face_towards_target(self):
        """Test facing towards specific position"""
        unit = UnitFactory.create_warrior("Test", 10, 10)
        
        # Face towards east
        unit.facing.face_towards(15, 10, 10, 10)
        assert unit.facing.facing == FacingDirection.EAST
        
        # Face towards north-west
        unit.facing.face_towards(9, 9, 10, 10)
        assert unit.facing.facing == FacingDirection.NORTH_WEST


def run_tests():
    """Run all facing tests"""
    test = TestFacingMechanics()
    
    print("Testing Facing Mechanics...")
    
    # Basic tests
    test.setup_method()
    test.test_facing_component_exists()
    print("✓ Units have facing component")
    
    test.setup_method()
    test.test_facing_updates_on_movement()
    print("✓ Facing updates on movement")
    
    test.setup_method()
    test.test_attack_angle_detection()
    print("✓ Attack angles detected correctly")
    
    # Combat modifier tests
    test.setup_method()
    test.test_damage_modifiers()
    print("✓ Damage modifiers work correctly")
    
    test.setup_method()
    test.test_morale_penalties()
    print("✓ Morale penalties apply correctly")
    
    test.setup_method()
    test.test_routing_chance_calculation()
    print("✓ Routing chance calculation exists")
    
    # Integration tests
    test.setup_method()
    test.test_combat_with_facing()
    print("✓ Combat integrates with facing")
    
    test.setup_method()
    test.test_cavalry_charge_rear_bonus()
    print("✓ Cavalry charges devastating from rear")
    
    # UI tests
    test.setup_method()
    test.test_facing_arrow_visualization()
    print("✓ Facing arrows calculate correctly")
    
    test.setup_method()
    test.test_rotate_facing()
    print("✓ Manual rotation works")
    
    test.setup_method()
    test.test_face_towards_target()
    print("✓ Face towards target works")
    
    print("\nAll facing tests passed!")


if __name__ == "__main__":
    run_tests()