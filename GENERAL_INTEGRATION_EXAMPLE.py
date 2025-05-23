"""Example of how to integrate generals into the existing game"""

# In game_state.py, add general UI components:
"""
from game.ui.general_display import GeneralDisplay, GeneralActionMenu

class GameState:
    def __init__(self, vs_ai=True):
        # ... existing init code ...
        
        # Add general UI components
        self.general_display = GeneralDisplay(
            self.screen.get_width() - 320, 
            60,  # Below turn counter
            300, 
            250
        )
        self.general_action_menu = GeneralActionMenu()
"""

# In renderer.py, add general display rendering:
"""
def render(self, game_state):
    # ... existing rendering ...
    
    # Render general display if unit selected
    if game_state.selected_knight:
        game_state.general_display.show(game_state.selected_knight)
    else:
        game_state.general_display.hide()
        
    game_state.general_display.render(self.screen)
    game_state.general_action_menu.render(self.screen)
"""

# In input_handler.py, add general ability handling:
"""
def handle_event(self, event, game_state):
    if event.type == pygame.MOUSEBUTTONDOWN:
        x, y = event.pos
        
        # Check general action menu first
        if game_state.general_action_menu.visible:
            result = game_state.general_action_menu.handle_click(x, y)
            if result:
                general, ability = result
                unit = game_state.selected_knight
                ability_result = unit.execute_general_ability(general, ability)
                if ability_result['success']:
                    game_state.add_message(ability_result.get('message', 'Ability activated!'))
                return
        
        # Right click for general abilities
        if event.button == 3 and game_state.selected_knight:
            game_state.general_action_menu.show(game_state.selected_knight, x, y)
            return
"""

# In context_menu.py, add general abilities option:
"""
def get_options(self, knight, game_state):
    options = []
    
    # ... existing options ...
    
    # Add general abilities if available
    if knight.generals.get_active_abilities(knight):
        options.append('general_abilities')
        
    return options
"""

# Example of using generals in combat:
"""
# In attack animation, check for triggered abilities
def apply_damage(self):
    # Check defender's countercharge
    context = {'being_charged': self.attacker.knight_class == KnightClass.CAVALRY}
    triggered = self.target.generals.check_all_triggered_abilities(self.target, context)
    
    for ability_info in triggered:
        if ability_info['ability'].name == "Countercharge":
            # Apply countercharge bonus
            counter_damage = int(counter_damage * 1.5)
            game_state.add_message(ability_info['result']['message'])
"""

# Creating pre-configured armies with generals:
"""
def create_elite_army(player_id):
    units = []
    
    # Elite Cavalry with 3 generals
    cavalry = UnitFactory.create_cavalry("Royal Guard", 5, 5)
    cavalry.player_id = player_id
    
    # Add third general
    cavalry.generals.add_general(
        GeneralFactory.create_general("Berserker Lord", level=3)
    )
    
    # Level up existing generals
    for general in cavalry.generals.generals:
        general.gain_experience(200)  # Level 3
    
    units.append(cavalry)
    
    return units
"""

# Save/Load general data:
"""
def save_unit_data(unit):
    return {
        'name': unit.name,
        'class': unit.unit_class.value,
        'position': (unit.x, unit.y),
        'soldiers': unit.soldiers,
        'morale': unit.morale,
        'will': unit.will,
        'generals': [
            {
                'name': gen.name,
                'title': gen.title,
                'level': gen.level,
                'experience': gen.experience,
                'abilities': [ability.name for ability in gen.abilities]
            }
            for gen in unit.generals.generals
        ]
    }
"""