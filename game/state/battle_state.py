"""Core battle state: units, terrain, and rules without UI concerns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from game.components.facing import FacingDirection
from game.entities.castle import Castle
from game.entities.knight import KnightClass
from game.entities.unit_factory import UnitFactory
from game.interfaces.game_state import IGameState
from game.state.victory_manager import VictoryManager
from game.terrain import TerrainMap
from game.visibility import FogOfWar


@dataclass(frozen=True)
class EndTurnResult:
    """Outcome data for UI/animation handling after end turn."""
    rallied_units: list
    castle_attacks: list


class BattleState(IGameState):
    """Pure battle state with no UI, rendering, or input handling."""

    def __init__(self, battle_config: dict):
        if battle_config is None:
            raise ValueError("battle_config is required")
        if not isinstance(battle_config, dict):
            raise ValueError("battle_config must be a dict")
        if 'board_size' not in battle_config:
            raise ValueError("battle_config['board_size'] is required")
        if 'knights' not in battle_config:
            raise ValueError("battle_config['knights'] is required")
        if 'castles' not in battle_config:
            raise ValueError("battle_config['castles'] is required")

        board_size = battle_config['board_size']
        if (
            not isinstance(board_size, (tuple, list))
            or len(board_size) != 2
            or not all(isinstance(value, int) for value in board_size)
        ):
            raise ValueError("battle_config['board_size'] must be a tuple/list of two ints")

        self.board_width = board_size[0]
        self.board_height = board_size[1]
        self.knights_per_player = battle_config['knights']
        self.castles_per_player = battle_config['castles']

        self.is_campaign_battle = bool(battle_config.get('campaign_battle', False))
        self.attacker_army = battle_config.get('attacker_army')
        self.defender_army = battle_config.get('defender_army')
        self.attacker_country = battle_config.get('attacker_country')
        self.defender_country = battle_config.get('defender_country')
        self.battle_intro_message: Optional[str] = None

        if self.is_campaign_battle and (self.attacker_army is None or self.defender_army is None):
            raise ValueError("campaign_battle requires attacker_army and defender_army")

        self.castles = []
        self.knights = []
        self.current_player = 1
        self.player_count = 2
        self.turn_number = 1

        self.victory_manager = VictoryManager()

        self.terrain_map = TerrainMap(self.board_width, self.board_height)
        self.fog_of_war = FogOfWar(self.board_width, self.board_height, self.player_count)

        self._init_game()

    def _init_game(self) -> None:
        if self.is_campaign_battle and self.attacker_army and self.defender_army:
            self._init_campaign_battle()
            return

        castle_spacing = self.board_height // (self.castles_per_player + 1)
        for i in range(self.castles_per_player):
            y_pos = castle_spacing * (i + 1)
            self.castles.append(Castle(2, y_pos, 1))
            self.castles.append(Castle(self.board_width - 3, y_pos, 2))

        knight_names_p1 = [
            "Sir Lancelot",
            "Robin Hood",
            "Sir Galahad",
            "Sir Kay",
            "Sir Gawain",
            "Sir Percival",
            "Sir Tristan",
            "Sir Bedivere",
        ]
        knight_names_p2 = [
            "Black Knight",
            "Dark Archer",
            "Shadow Rider",
            "Dark Mage",
            "Iron Lord",
            "Death Knight",
            "Void Walker",
            "Night Hunter",
        ]
        knight_classes = [
            KnightClass.WARRIOR,
            KnightClass.ARCHER,
            KnightClass.CAVALRY,
            KnightClass.MAGE,
        ]

        knight_spacing = self.board_height // (self.knights_per_player + 1)
        for i in range(self.knights_per_player):
            y_pos = knight_spacing * (i + 1)
            x_pos = 4 if i % 2 == 0 else 5

            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos is None:
                print(f"Warning: Could not find valid position for player 1 knight {i}")
                continue

            x_pos, y_pos = valid_pos
            knight_class = knight_classes[i % len(knight_classes)]
            knight = UnitFactory.create_unit(
                knight_names_p1[i % len(knight_names_p1)],
                knight_class,
                x_pos,
                y_pos,
            )
            knight.player_id = 1
            knight.game_state = self
            if hasattr(knight, 'facing'):
                knight.facing.facing = FacingDirection.EAST
            self.knights.append(knight)

        for i in range(self.knights_per_player):
            y_pos = knight_spacing * (i + 1)
            x_pos = self.board_width - 5 if i % 2 == 0 else self.board_width - 6

            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos is None:
                print(f"Warning: Could not find valid position for player 2 knight {i}")
                continue

            x_pos, y_pos = valid_pos
            knight_class = knight_classes[i % len(knight_classes)]
            knight = UnitFactory.create_unit(
                knight_names_p2[i % len(knight_names_p2)],
                knight_class,
                x_pos,
                y_pos,
            )
            knight.player_id = 2
            knight.game_state = self
            if hasattr(knight, 'facing'):
                knight.facing.facing = FacingDirection.WEST
            self.knights.append(knight)

        from game.entities.unit_helpers import check_cavalry_disruption_for_terrain

        for knight in self.knights:
            check_cavalry_disruption_for_terrain(knight, self)

        self.update_all_fog_of_war()

    def _init_campaign_battle(self) -> None:
        attacker_names = [
            "Captain",
            "Lieutenant",
            "Sergeant",
            "Corporal",
            "Soldier",
            "Warrior",
            "Fighter",
            "Guardian",
            "Defender",
            "Champion",
        ]
        defender_names = [
            "Commander",
            "Major",
            "Knight",
            "Veteran",
            "Elite",
            "Protector",
            "Sentinel",
            "Warden",
            "Keeper",
            "Marshal",
        ]

        unit_count = 0
        y_start = self.board_height // 4

        for _ in range(self.attacker_army.knights):
            y_pos = y_start + (unit_count % (self.board_height // 2))
            x_pos = 3 + (unit_count // (self.board_height // 2))
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos:
                x_pos, y_pos = valid_pos
                knight = UnitFactory.create_unit(
                    attacker_names[unit_count % len(attacker_names)],
                    KnightClass.WARRIOR,
                    x_pos,
                    y_pos,
                )
                knight.player_id = 1
                knight.game_state = self
                if hasattr(knight, 'facing'):
                    knight.facing.facing = FacingDirection.EAST
                self.knights.append(knight)
                unit_count += 1

        for _ in range(self.attacker_army.archers):
            y_pos = y_start + (unit_count % (self.board_height // 2))
            x_pos = 3 + (unit_count // (self.board_height // 2))
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos:
                x_pos, y_pos = valid_pos
                archer = UnitFactory.create_unit(
                    attacker_names[unit_count % len(attacker_names)],
                    KnightClass.ARCHER,
                    x_pos,
                    y_pos,
                )
                archer.player_id = 1
                archer.game_state = self
                if hasattr(archer, 'facing'):
                    archer.facing.facing = FacingDirection.EAST
                self.knights.append(archer)
                unit_count += 1

        for _ in range(self.attacker_army.cavalry):
            y_pos = y_start + (unit_count % (self.board_height // 2))
            x_pos = 3 + (unit_count // (self.board_height // 2))
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos:
                x_pos, y_pos = valid_pos
                cavalry = UnitFactory.create_unit(
                    attacker_names[unit_count % len(attacker_names)],
                    KnightClass.CAVALRY,
                    x_pos,
                    y_pos,
                )
                cavalry.player_id = 1
                cavalry.game_state = self
                if hasattr(cavalry, 'facing'):
                    cavalry.facing.facing = FacingDirection.EAST
                self.knights.append(cavalry)
                unit_count += 1

        unit_count = 0

        for _ in range(self.defender_army.knights):
            y_pos = y_start + (unit_count % (self.board_height // 2))
            x_pos = self.board_width - 4 - (unit_count // (self.board_height // 2))
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos:
                x_pos, y_pos = valid_pos
                knight = UnitFactory.create_unit(
                    defender_names[unit_count % len(defender_names)],
                    KnightClass.WARRIOR,
                    x_pos,
                    y_pos,
                )
                knight.player_id = 2
                knight.game_state = self
                if hasattr(knight, 'facing'):
                    knight.facing.facing = FacingDirection.WEST
                self.knights.append(knight)
                unit_count += 1

        for _ in range(self.defender_army.archers):
            y_pos = y_start + (unit_count % (self.board_height // 2))
            x_pos = self.board_width - 4 - (unit_count // (self.board_height // 2))
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos:
                x_pos, y_pos = valid_pos
                archer = UnitFactory.create_unit(
                    defender_names[unit_count % len(defender_names)],
                    KnightClass.ARCHER,
                    x_pos,
                    y_pos,
                )
                archer.player_id = 2
                archer.game_state = self
                if hasattr(archer, 'facing'):
                    archer.facing.facing = FacingDirection.WEST
                self.knights.append(archer)
                unit_count += 1

        for _ in range(self.defender_army.cavalry):
            y_pos = y_start + (unit_count % (self.board_height // 2))
            x_pos = self.board_width - 4 - (unit_count // (self.board_height // 2))
            valid_pos = self._find_valid_position_near(x_pos, y_pos, max_distance=3)
            if valid_pos:
                x_pos, y_pos = valid_pos
                cavalry = UnitFactory.create_unit(
                    defender_names[unit_count % len(defender_names)],
                    KnightClass.CAVALRY,
                    x_pos,
                    y_pos,
                )
                cavalry.player_id = 2
                cavalry.game_state = self
                if hasattr(cavalry, 'facing'):
                    cavalry.facing.facing = FacingDirection.WEST
                self.knights.append(cavalry)
                unit_count += 1

        from game.entities.unit_helpers import check_cavalry_disruption_for_terrain

        for knight in self.knights:
            check_cavalry_disruption_for_terrain(knight, self)

        self.update_all_fog_of_war()

        attacker_name = (
            self.attacker_army.country
            if hasattr(self.attacker_army, 'country')
            else 'Attacker'
        )
        defender_name = (
            self.defender_army.country
            if hasattr(self.defender_army, 'country')
            else 'Defender'
        )
        self.battle_intro_message = (
            f"{attacker_name.title()} attacks {defender_name.title()}!"
        )

    def _find_valid_position_near(
        self, x: int, y: int, max_distance: int = 3
    ) -> Optional[tuple[int, int]]:
        if self._is_position_valid_for_placement(x, y):
            return (x, y)

        for distance in range(1, max_distance + 1):
            positions_to_check = []

            for dx in range(-distance, distance + 1):
                positions_to_check.append((x + dx, y - distance))
                positions_to_check.append((x + dx, y + distance))

            for dy in range(-distance + 1, distance):
                positions_to_check.append((x - distance, y + dy))
                positions_to_check.append((x + distance, y + dy))

            for new_x, new_y in positions_to_check:
                if (
                    0 <= new_x < self.board_width
                    and 0 <= new_y < self.board_height
                    and self._is_position_valid_for_placement(new_x, new_y)
                ):
                    return (new_x, new_y)

        return None

    def _is_position_valid_for_placement(self, x: int, y: int) -> bool:
        if not (0 <= x < self.board_width and 0 <= y < self.board_height):
            return False

        if self.terrain_map:
            terrain = self.terrain_map.get_terrain(x, y)
            if terrain and not terrain.passable:
                return False

        for knight in self.knights:
            if knight.x == x and knight.y == y:
                return False

        for castle in self.castles:
            if hasattr(castle, 'contains_position') and castle.contains_position(x, y):
                return False

        return True

    def cleanup_dead_knights(self) -> bool:
        had_dead_knights = any(k.soldiers <= 0 for k in self.knights)
        self.knights = [k for k in self.knights if k.soldiers > 0]

        if had_dead_knights:
            self.update_all_fog_of_war()

        return had_dead_knights

    def update_zoc_status(self) -> None:
        from game.systems.engagement import EngagementSystem

        EngagementSystem.update_zoc_and_engagement(self)

    def end_turn(self) -> EndTurnResult:
        rallied_units = []
        for knight in self.knights:
            if knight.player_id == self.current_player:
                knight.end_turn()
                if (
                    hasattr(knight, 'has_rallied_this_turn')
                    and knight.has_rallied_this_turn
                ):
                    rallied_units.append(knight)

        castle_attacks = []
        for castle in self.castles:
            if castle.player_id == self.current_player:
                enemies = castle.get_enemies_in_range(self.knights)
                if enemies:
                    damages = castle.shoot_arrows(enemies)
                    if damages:
                        from game.systems.combat_resolver import CombatResolver

                        for enemy, casualties in damages:
                            CombatResolver.resolve_ranged_casualties(enemy, casualties, self)
                        castle_attacks.append((castle, enemies, damages))

        self.current_player = 2 if self.current_player == 1 else 1
        if self.current_player == 1:
            self.turn_number += 1

        self.fog_of_war.update_player_visibility(self, self.current_player)

        for castle in self.castles:
            if castle.player_id == self.current_player:
                castle.end_turn()

        return EndTurnResult(rallied_units=rallied_units, castle_attacks=castle_attacks)

    def check_victory(self):
        return self.victory_manager.check_victory(self.knights, self.castles)

    def update_all_fog_of_war(self) -> None:
        for player_id in range(1, self.fog_of_war.num_players + 1):
            self.fog_of_war.update_player_visibility(self, player_id)

    def get_knight_at(self, tile_x, tile_y):
        for knight in self.knights:
            if knight.x == tile_x and knight.y == tile_y:
                return knight
        return None

    def get_castle_at(self, tile_x, tile_y):
        for castle in self.castles:
            if castle.contains_position(tile_x, tile_y):
                return castle
        return None

    def get_unit_at(self, x, y):
        return self.get_knight_at(x, y)

    @property
    def units(self):
        return self.knights
