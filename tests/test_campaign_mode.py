import pytest
import pygame
from game.campaign.campaign_state import CampaignState, Faction, Army
from game.campaign.campaign_renderer import CampaignRenderer
from game.ui.campaign_screen import CampaignScreen
from game.hex_utils import HexCoord


class TestCampaignMode:
    
    def test_campaign_state_initialization(self):
        """Test campaign state initializes correctly"""
        state = CampaignState()
        
        # Check initial state
        assert state.current_faction == Faction.POLAND
        assert state.turn_number == 1
        assert len(state.territories) > 0
        assert len(state.armies) > 0
        
        # Check Poland has starting territories
        poland_territories = state.get_faction_territories(Faction.POLAND)
        assert len(poland_territories) == 3  # Krakow, Warsaw, Gniezno
        assert any(t.name == "Krakow" for t in poland_territories)
        
        # Check Poland has starting army
        poland_armies = state.get_faction_armies(Faction.POLAND)
        assert len(poland_armies) == 1
        assert poland_armies[0].knights == 10
        assert poland_armies[0].archers == 5
        assert poland_armies[0].cavalry == 3
        
        # Check enemy armies exist
        assert len(state.armies) > 1  # More than just Poland's army
        teutonic_armies = state.get_faction_armies(Faction.TEUTONIC_ORDER)
        assert len(teutonic_armies) == 1  # Teutonic Order has an army
        
    def test_army_movement(self):
        """Test army movement mechanics"""
        state = CampaignState()
        
        # Get Poland's main army
        army_id = "poland_main"
        army = state.armies[army_id]
        original_pos = army.position
        
        # Test valid movement (1 hex away)
        new_pos = HexCoord(original_pos.q + 1, original_pos.r)
        assert state.move_army(army_id, new_pos) == True
        assert army.position == new_pos
        assert army.movement_points < army.max_movement_points
        
        # Test invalid movement (too far - more than 2 remaining movement points)
        far_pos = HexCoord(original_pos.q + 10, original_pos.r)
        assert state.move_army(army_id, far_pos) == False
        assert army.position == new_pos  # Position unchanged
        
    def test_faction_turn_cycle(self):
        """Test turn cycling through factions"""
        state = CampaignState()
        
        # Record initial faction
        assert state.current_faction == Faction.POLAND
        assert state.turn_number == 1
        
        # Cycle through all factions
        factions = list(Faction)
        for i in range(len(factions)):
            state.end_turn()
            
        # Should be back to Poland, turn 2
        assert state.current_faction == Faction.POLAND
        assert state.turn_number == 2
        
    def test_territory_income(self):
        """Test income collection from territories"""
        state = CampaignState()
        
        # Record initial treasury and income
        initial_gold = state.faction_treasury[Faction.POLAND]
        poland_territories = state.get_faction_territories(Faction.POLAND)
        expected_income = sum(t.income for t in poland_territories)
        
        # Income is collected at the end of each faction's turn
        # End Poland's turn to collect income
        assert state.current_faction == Faction.POLAND
        state.end_turn()
        
        # Poland should have received income exactly once
        # (300 from 3 territories with 100 income each)
        assert state.faction_treasury[Faction.POLAND] == initial_gold + expected_income
        
        # Complete full cycle back to Poland
        num_factions = len(list(Faction))
        for _ in range(num_factions - 1):
            state.end_turn()
            
        # Should be Poland's turn again
        assert state.current_faction == Faction.POLAND
        
        # End Poland's turn again
        state.end_turn()
        
        # Should have received income twice total
        assert state.faction_treasury[Faction.POLAND] == initial_gold + (2 * expected_income)
        
    def test_unit_recruitment(self):
        """Test recruiting new units"""
        state = CampaignState()
        
        # Give Poland extra gold for recruitment
        state.faction_treasury[Faction.POLAND] = 5000
        
        # Recruit units in Krakow
        assert state.recruit_units(Faction.POLAND, "Krakow", 
                                 knights=5, archers=3, cavalry=2) == True
                                 
        # Check cost deducted
        expected_cost = 5 * 100 + 3 * 80 + 2 * 150  # 1040 gold
        assert state.faction_treasury[Faction.POLAND] == 5000 - expected_cost
        
        # Check units added to army
        poland_armies = state.get_faction_armies(Faction.POLAND)
        total_knights = sum(a.knights for a in poland_armies)
        assert total_knights == 15  # 10 original + 5 new
        
    def test_campaign_screen_initialization(self):
        """Test campaign screen setup"""
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        campaign_screen = CampaignScreen(screen)
        
        assert campaign_screen.visible == True
        assert campaign_screen.ready_for_battle == False
        assert campaign_screen.campaign_state.current_faction == Faction.POLAND
        
        pygame.quit()
        
    def test_army_selection(self):
        """Test army selection mechanics"""
        state = CampaignState()
        
        # Select Poland's army
        state.selected_army = "poland_main"
        assert state.selected_army == "poland_main"
        
        # Verify selected army belongs to current faction
        army = state.armies[state.selected_army]
        assert army.faction == state.current_faction
        
    def test_campaign_battle_setup(self):
        """Test battle setup from campaign armies"""
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        campaign_screen = CampaignScreen(screen)
        
        # Simulate armies meeting
        poland_army = campaign_screen.campaign_state.armies["poland_main"]
        teutonic_army = campaign_screen.campaign_state.armies["teutonic_main"]
        
        campaign_screen.ready_for_battle = True
        campaign_screen.battle_armies = {
            'attacker': poland_army,
            'defender': teutonic_army
        }
        
        # Get battle config
        battle_config = campaign_screen.get_battle_config()
        
        assert battle_config is not None
        assert battle_config['campaign_battle'] == True
        assert battle_config['attacker_army'] == poland_army
        assert battle_config['defender_army'] == teutonic_army
        assert battle_config['board_size'] == (20, 20)
        assert battle_config['castles'] == 0
        
        # Create game state from config
        from game.game_state import GameState
        game_state = GameState(battle_config, vs_ai=True)
        
        # Check units were created
        assert len(game_state.knights) > 0
        
        # Check player 1 has units from Poland army
        player1_units = [k for k in game_state.knights if k.player_id == 1]
        total_p1_units = poland_army.knights + poland_army.archers + poland_army.cavalry
        assert len(player1_units) == total_p1_units
        
        # Check player 2 has units from Teutonic army
        player2_units = [k for k in game_state.knights if k.player_id == 2]
        total_p2_units = teutonic_army.knights + teutonic_army.archers + teutonic_army.cavalry
        assert len(player2_units) == total_p2_units
        
        pygame.quit()
        
    def test_hex_movement_distances(self):
        """Test that hex movement correctly calculates distances"""
        state = CampaignState()
        
        # Create a test army
        test_army = Army(
            id="test_army",
            faction=Faction.POLAND,
            position=HexCoord(25, 20),
            knights=5,
            archers=3,
            cavalry=2,
            movement_points=3
        )
        state.armies["test_army"] = test_army
        
        # Test 1-hex movement (distance = 1)
        target1 = HexCoord(26, 20)  # 1 hex east
        assert test_army.position.distance_to(target1) == 1
        assert state.move_army("test_army", target1) == True
        assert test_army.movement_points == 2
        
        # Test 2-hex movement (distance = 2)
        target2 = HexCoord(26, 18)  # 2 hexes northeast
        assert test_army.position.distance_to(target2) == 2
        assert state.move_army("test_army", target2) == True
        assert test_army.movement_points == 0
        
        # Test invalid movement (no movement points left)
        target3 = HexCoord(27, 18)  # 1 hex east
        assert state.move_army("test_army", target3) == False
        assert test_army.position == target2  # Position unchanged