"""Presentation/controller state: camera, animations, UI selection, and AI orchestration."""
from __future__ import annotations

from typing import Optional

from game.ai.ai_player import AIPlayer
from game.battle.adapters.battle_context import BattleContextAdapter
from game.battle.application.commands import AttackUnitCommand, ChargeUnitCommand, MoveUnitCommand
from game.battle.application.handlers import AttackUnitHandler, ChargeUnitHandler, MoveUnitHandler
from game.battle.domain.events import AttackResolved, ChargeResolved, UnitMoved
from game.behaviors.movement_service import MovementService
from game.entities.knight import KnightClass
from game.hex_layout import HexLayout
from game.hex_utils import HexGrid
from game.state.animation_coordinator import AnimationCoordinator
from game.state.camera_manager import CameraManager
from game.state.message_system import MessageSystem
from game.ui.context_menu import ContextMenu
from game.visibility import VisibilityState
from game.animation import MoveAnimation, AttackAnimation, ArrowAnimation, PathMoveAnimation


class PresentationState:
    """UI/controller state with no ownership of core battle data."""

    def __init__(self, battle_state, vs_ai: bool, screen_width: int, screen_height: int):
        if battle_state is None:
            raise ValueError("battle_state is required")
        if vs_ai is None:
            raise ValueError("vs_ai is required")
        if screen_width is None or screen_height is None:
            raise ValueError("screen_width and screen_height are required")

        self._game_state = None
        self.battle_state = battle_state
        self.vs_ai = vs_ai
        self._battle_context = BattleContextAdapter(
            self.battle_state,
            fog_view_player=self.fog_view_player,
        )

        self.tile_size = 64
        self.screen_width = screen_width
        self.screen_height = screen_height

        world_width = self.board_width * self.tile_size * 2
        world_height = self.board_height * self.tile_size * 2
        self.camera_manager = CameraManager(
            self.screen_width,
            self.screen_height,
            world_width,
            world_height,
        )
        self.message_system = MessageSystem()
        self.animation_coordinator = AnimationCoordinator()
        self.movement_service = MovementService()

        self.context_menu = ContextMenu()
        self.current_action = None
        self.attack_targets = []
        self.enemy_info_unit = None
        self.terrain_info = None

        self.selected_knight = None
        self.possible_moves = []
        self.pending_positions = {}

        self.ai_player = AIPlayer(2, 'medium') if vs_ai else None
        self.ai_thinking = False
        self.ai_turn_delay = 0

        self.show_coordinates = False
        self.show_enemy_paths = True
        self.movement_history = {}

        self.hex_layout = HexLayout(hex_size=36)

        self.messages = []
        self.message_duration = 3.0

        self.camera_x = 0
        self.camera_y = 0

        self._center_camera_on_player_start()

        if hasattr(self, 'camera_manager'):
            self.camera_manager.camera_x = self.camera_x
            self.camera_manager.camera_y = self.camera_y

    def bind_game_state(self, game_state) -> None:
        self._game_state = game_state

    def _require_game_state(self):
        if self._game_state is None:
            raise ValueError("PresentationState is not bound to GameState")
        return self._game_state

    def publish(self, event) -> None:
        if isinstance(event, UnitMoved):
            self._handle_unit_moved(event)
            return
        if isinstance(event, AttackResolved):
            self._handle_attack_resolved(event)
            return
        if isinstance(event, ChargeResolved):
            self._handle_charge_resolved(event)
            return
        raise ValueError(f"Unsupported event type: {type(event).__name__}")

    def _get_unit_by_id(self, unit_id: int):
        for unit in self.battle_state.knights:
            if id(unit) == unit_id:
                return unit
        raise ValueError(f"unit_id not found: {unit_id}")

    def _handle_unit_moved(self, event: UnitMoved) -> None:
        unit = self._get_unit_by_id(event.unit_id)
        if event.use_path_animation and not event.path:
            raise ValueError("UnitMoved requires path for path animation")
        self.pending_positions[event.unit_id] = (event.to_x, event.to_y)

        if event.path:
            full_path = event.path
            if full_path[0] != (event.from_x, event.from_y):
                full_path = [(event.from_x, event.from_y)] + full_path
        else:
            full_path = [(event.from_x, event.from_y), (event.to_x, event.to_y)]

        self.movement_history[event.unit_id] = full_path

        if event.use_path_animation:
            anim = PathMoveAnimation(
                unit,
                event.path,
                step_duration=0.25,
                game_state=self._game_state,
                final_face_target=event.final_face_target,
            )
        else:
            anim = MoveAnimation(
                unit,
                event.from_x,
                event.from_y,
                event.to_x,
                event.to_y,
                game_state=self._game_state,
            )
        self.animation_coordinator.animation_manager.add_animation(anim)
        self.possible_moves = []
        self._fog_update_needed = True

    def _handle_attack_resolved(self, event: AttackResolved) -> None:
        attacker = self._get_unit_by_id(event.attacker_id)
        target = self._get_unit_by_id(event.target_id)

        anim = AttackAnimation(
            attacker,
            target,
            event.damage,
            event.counter_damage,
            attack_angle=event.attack_angle,
            extra_morale_penalty=event.extra_morale_penalty,
            extra_cohesion_penalty=event.extra_cohesion_penalty,
            should_check_routing=event.should_check_routing,
            game_state=self._game_state,
        )
        self.animation_coordinator.animation_manager.add_animation(anim)
        self.attack_targets = []

    def _handle_charge_resolved(self, event: ChargeResolved) -> None:
        attacker = self._get_unit_by_id(event.attacker_id)
        if event.attacker_to:
            anim = MoveAnimation(
                attacker,
                event.attacker_from[0],
                event.attacker_from[1],
                event.attacker_to[0],
                event.attacker_to[1],
                game_state=self._game_state,
            )
            self.animation_coordinator.animation_manager.add_animation(anim)
            attacker.x = event.attacker_to[0]
            attacker.y = event.attacker_to[1]

        self.add_message(event.message, priority=2)

    @property
    def board_width(self) -> int:
        return self.battle_state.board_width

    @property
    def board_height(self) -> int:
        return self.battle_state.board_height

    @property
    def knights(self):
        return self.battle_state.knights

    @property
    def castles(self):
        return self.battle_state.castles

    @property
    def terrain_map(self):
        return self.battle_state.terrain_map

    @property
    def fog_of_war(self):
        return self.battle_state.fog_of_war

    @property
    def current_player(self) -> int:
        return self.battle_state.current_player

    @current_player.setter
    def current_player(self, value: int) -> None:
        self.battle_state.current_player = value

    @property
    def turn_number(self) -> int:
        return self.battle_state.turn_number

    @turn_number.setter
    def turn_number(self, value: int) -> None:
        self.battle_state.turn_number = value

    @property
    def fog_view_player(self) -> int:
        return 1 if self.vs_ai else self.current_player

    def _center_camera_on_player_start(self) -> None:
        if self.knights:
            player1_knights = [k for k in self.knights if k.player_id == 1]
            if player1_knights:
                avg_x = sum(k.x for k in player1_knights) / len(player1_knights)
                avg_y = sum(k.y for k in player1_knights) / len(player1_knights)
                self.center_camera_on_tile(int(avg_x), int(avg_y))

    def add_message(self, message, priority=1) -> None:
        self.message_system.add_message(message, priority)
        import time

        self.messages.append((message, time.time(), priority))

    def update_messages(self, dt) -> None:
        self.message_system.update(dt)
        import time

        current_time = time.time()
        self.messages = [
            (msg, timestamp, priority)
            for msg, timestamp, priority in self.messages
            if current_time - timestamp < self.message_duration * priority
        ]

    def update(self, dt) -> None:
        self.animation_coordinator.update(dt)
        self.message_system.update(dt)

        self._sync_hex_layout_with_zoom()
        self.update_messages(dt)

        self.battle_state.cleanup_dead_knights()
        self.battle_state.update_zoc_status()

        if self.animation_coordinator.is_animating():
            return

        if hasattr(self, '_fog_update_needed'):
            self.battle_state.update_all_fog_of_war()
            self._fog_update_needed = False

        if self.vs_ai and self.current_player == 2 and not self.ai_thinking:
            self.ai_thinking = True
            self.ai_turn_delay = 0.1

        if self.ai_thinking:
            self.ai_turn_delay -= dt
            if self.ai_turn_delay <= 0:
                self._execute_ai_turn()
                self.ai_thinking = False

    def _execute_ai_turn(self) -> None:
        if self.ai_player is None:
            raise ValueError("AI player is not configured")
        if self._game_state is None:
            raise ValueError("PresentationState is not bound to GameState")

        print(
            f"AI Turn Start (Player {self.ai_player.player_id}, "
            f"Difficulty: {self.ai_player.difficulty})"
        )
        self.ai_player.execute_turn(self._game_state)
        print("AI Turn End")
        self._game_state.end_turn()

    def set_camera_position(self, x, y) -> None:
        if hasattr(self, 'camera_manager'):
            self.camera_manager.set_camera_position(x, y)
            self.camera_x = self.camera_manager.camera_x
            self.camera_y = self.camera_manager.camera_y
        else:
            effective_tile_size = self.tile_size * 2
            max_camera_x = max(0, self.board_width * effective_tile_size - self.screen_width)
            max_camera_y = max(0, self.board_height * effective_tile_size - self.screen_height)

            self.camera_x = max(0, min(x, max_camera_x))
            self.camera_y = max(0, min(y, max_camera_y))

    def move_camera(self, dx, dy) -> None:
        if hasattr(self, 'camera_manager'):
            self.camera_manager.move_camera(dx, dy)
            self.camera_x = self.camera_manager.camera_x
            self.camera_y = self.camera_manager.camera_y
        else:
            self.set_camera_position(self.camera_x + dx, self.camera_y + dy)

    def center_camera_on_tile(self, tile_x, tile_y) -> None:
        pixel_x = tile_x * self.tile_size + self.tile_size // 2
        pixel_y = tile_y * self.tile_size + self.tile_size // 2

        camera_x = pixel_x - self.screen_width // 2
        camera_y = pixel_y - self.screen_height // 2

        self.set_camera_position(camera_x, camera_y)

    def screen_to_world(self, screen_x, screen_y):
        if hasattr(self, 'camera_manager'):
            return self.camera_manager.screen_to_world(screen_x, screen_y)

        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        return world_x, world_y

    def world_to_screen(self, world_x, world_y):
        if hasattr(self, 'camera_manager'):
            return self.camera_manager.world_to_screen(world_x, world_y)

        screen_x = world_x - self.camera_x
        screen_y = world_y - self.camera_y
        return screen_x, screen_y

    def select_knight(self, x, y) -> bool:
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size

        for knight in self.knights:
            if (
                knight.x == tile_x
                and knight.y == tile_y
                and knight.player_id == self.current_player
            ):
                if knight.is_routing:
                    self.add_message(f"{knight.name} is routing and cannot be controlled.", priority=1)
                    self.deselect_knight()
                    return False
                self.selected_knight = knight
                knight.selected = True
                if knight.can_move():
                    self.possible_moves = knight.get_possible_moves(
                        self.board_width,
                        self.board_height,
                        self.terrain_map,
                        self._require_game_state(),
                    )
                    self.possible_moves = self._filter_valid_moves(self.possible_moves)
                return True

        self.deselect_knight()
        return False

    def deselect_knight(self) -> None:
        if self.selected_knight:
            self.selected_knight.selected = False
        self.selected_knight = None
        self.possible_moves = []
        self.current_action = None
        self.attack_targets = []
        self.context_menu.hide()

    def _filter_valid_moves(self, moves):
        return self.movement_service._filter_valid_moves(
            moves,
            self.selected_knight,
            self._require_game_state(),
        )

    def _is_position_occupied(self, x, y, exclude_knight=None):
        return self.movement_service._is_position_occupied(
            x,
            y,
            exclude_knight,
            self._require_game_state(),
        )

    def move_selected_knight(self, x, y) -> bool:
        if not self.selected_knight:
            return False

        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
        return self._execute_move_command(tile_x, tile_y)

    def move_selected_knight_hex(self, tile_x, tile_y) -> bool:
        if not self.selected_knight:
            return False

        return self._execute_move_command(tile_x, tile_y)

    def _execute_move_command(self, tile_x: int, tile_y: int) -> bool:
        if not self.selected_knight:
            return False
        if (tile_x, tile_y) not in self.possible_moves:
            return False

        self._battle_context.fog_view_player = self.fog_view_player
        handler = MoveUnitHandler(self._battle_context, self)
        command = MoveUnitCommand(
            unit_id=id(self.selected_knight),
            to_x=tile_x,
            to_y=tile_y,
        )
        return handler.handle(command)

    def _execute_attack_command(self, tile_x: int, tile_y: int, enforce_visibility: bool) -> bool:
        if not self.selected_knight:
            return False

        self._battle_context.fog_view_player = self.fog_view_player
        handler = AttackUnitHandler(self._battle_context, self)
        command = AttackUnitCommand(
            attacker_id=id(self.selected_knight),
            target_x=tile_x,
            target_y=tile_y,
            enforce_visibility=enforce_visibility,
        )
        return handler.handle(command)

    def _execute_charge_command(self, tile_x: int, tile_y: int) -> bool:
        if not self.selected_knight:
            return False

        self._battle_context.fog_view_player = self.fog_view_player
        handler = ChargeUnitHandler(self._battle_context, self)
        command = ChargeUnitCommand(
            attacker_id=id(self.selected_knight),
            target_x=tile_x,
            target_y=tile_y,
        )
        return handler.handle(command)

    def attack_with_selected_knight_hex(self, tile_x, tile_y) -> bool:
        if not self.selected_knight or not self.selected_knight.can_attack():
            return False
        return self._execute_attack_command(tile_x, tile_y, enforce_visibility=True)

    def charge_with_selected_knight_hex(self, tile_x, tile_y) -> bool:
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return False
        return self._execute_charge_command(tile_x, tile_y)

    def attack_with_selected_knight(self, x, y) -> bool:
        if not self.selected_knight or not self.selected_knight.can_attack():
            return False

        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
        return self._execute_attack_command(tile_x, tile_y, enforce_visibility=False)

    def charge_with_selected_knight(self, x, y) -> bool:
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return False

        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)
        return self._execute_charge_command(tile_x, tile_y)

    def set_action_mode(self, action) -> None:
        if action == 'move' and self.selected_knight and self.selected_knight.can_move():
            self.current_action = 'move'
            self.possible_moves = self.movement_service.get_possible_moves(
                self.selected_knight,
                self._require_game_state(),
            )
        elif action == 'attack' and self.selected_knight and self.selected_knight.can_attack():
            self.current_action = 'attack'
            self.attack_targets = self._get_attack_targets()
            self.add_message(
                f"Attack mode: {len(self.attack_targets)} targets available",
                priority=1,
            )
        elif action == 'charge' and self.selected_knight:
            self.current_action = 'charge'
            self.attack_targets = self._get_charge_targets()
        elif action == 'enter_garrison':
            self._enter_garrison()
        elif action == 'exit_garrison':
            self._exit_garrison()
        elif action == 'rotate_cw':
            self._rotate_selected_knight('clockwise')
        elif action == 'rotate_ccw':
            self._rotate_selected_knight('counter_clockwise')
        elif action == 'cancel':
            self.deselect_knight()

    def _enter_garrison(self) -> None:
        if not self.selected_knight or self.selected_knight.is_garrisoned:
            return

        for castle in self.castles:
            for tile_x, tile_y in castle.occupied_tiles:
                if abs(self.selected_knight.x - tile_x) + abs(self.selected_knight.y - tile_y) <= 1:
                    if castle.add_unit_to_garrison(self.selected_knight):
                        self.deselect_knight()
                        return

    def _exit_garrison(self) -> None:
        if not self.selected_knight or not self.selected_knight.is_garrisoned:
            return

        castle = self.selected_knight.garrison_location
        if castle:
            for tile_x, tile_y in castle.occupied_tiles:
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_x, new_y = tile_x + dx, tile_y + dy
                    if (
                        0 <= new_x < self.board_width
                        and 0 <= new_y < self.board_height
                        and not self._is_position_occupied(new_x, new_y)
                    ):
                        castle.remove_unit_from_garrison(self.selected_knight)
                        self.selected_knight.x = new_x
                        self.selected_knight.y = new_y
                        return

    def _rotate_selected_knight(self, direction) -> None:
        if not self.selected_knight:
            return

        if hasattr(self.selected_knight, 'behaviors') and 'rotate' in self.selected_knight.behaviors:
            rotate_behavior = self.selected_knight.behaviors['rotate']
            result = rotate_behavior.execute(self.selected_knight, self._require_game_state(), direction)

            if result['success']:
                self.add_message(result['message'])
            else:
                self.add_message(f"Cannot rotate: {result['reason']}")

    def _get_attack_targets(self):
        if not self.selected_knight:
            return []

        targets = []
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3
        hex_grid = HexGrid()
        attacker_hex = hex_grid.offset_to_axial(self.selected_knight.x, self.selected_knight.y)

        for knight in self.knights:
            if knight.player_id != self.current_player:
                if hasattr(self, 'fog_of_war'):
                    visibility = self.fog_of_war.get_visibility_state(
                        self.fog_view_player,
                        knight.x,
                        knight.y,
                    )
                    if visibility != VisibilityState.VISIBLE:
                        continue

                target_hex = hex_grid.offset_to_axial(knight.x, knight.y)
                distance = attacker_hex.distance_to(target_hex)
                if distance <= attack_range:
                    targets.append((knight.x, knight.y))

        return targets

    def _get_charge_targets(self):
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return []

        targets = []
        hex_grid = HexGrid()
        cavalry_hex = hex_grid.offset_to_axial(
            self.selected_knight.x,
            self.selected_knight.y,
        )

        neighbors = cavalry_hex.get_neighbors()
        for neighbor_hex in neighbors:
            check_x, check_y = hex_grid.axial_to_offset(neighbor_hex)

            for knight in self.knights:
                if (
                    knight.player_id != self.current_player
                    and knight.x == check_x
                    and knight.y == check_y
                    and not knight.is_garrisoned
                ):
                    if hasattr(self, 'fog_of_war'):
                        visibility = self.fog_of_war.get_visibility_state(
                            self.fog_view_player,
                            knight.x,
                            knight.y,
                        )
                        if visibility != VisibilityState.VISIBLE:
                            continue

                    can_charge, _ = self.selected_knight.can_charge(
                        knight,
                        self._require_game_state(),
                    )
                    if can_charge:
                        targets.append((check_x, check_y))
                    break

        return targets

    def get_charge_info_at(self, tile_x, tile_y):
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return None

        target = self.battle_state.get_knight_at(tile_x, tile_y)
        if not target or target.player_id == self.current_player:
            return {
                'can_charge': False,
                'reason': 'No enemy target at this position',
                'type': 'no_target',
            }

        if hasattr(self, 'fog_of_war'):
            visibility = self.fog_of_war.get_visibility_state(
                self.fog_view_player,
                tile_x,
                tile_y,
            )
            if visibility != VisibilityState.VISIBLE:
                return {
                    'can_charge': False,
                    'reason': 'Target not visible through fog of war',
                    'type': 'not_visible',
                }

        can_charge, reason = self.selected_knight.can_charge(
            target,
            self._require_game_state(),
        )

        failure_type = 'unknown'
        if 'will' in reason.lower():
            failure_type = 'insufficient_will'
        elif 'adjacent' in reason.lower():
            failure_type = 'not_adjacent'
        elif 'hills' in reason.lower():
            failure_type = 'terrain_restriction'
        elif 'special' in reason.lower():
            failure_type = 'already_used'
        elif 'routing' in reason.lower():
            failure_type = 'routing'
        elif 'cavalry' in reason.lower():
            failure_type = 'not_cavalry'

        return {
            'can_charge': can_charge,
            'reason': reason,
            'type': failure_type,
            'target': target,
        }

    def _sync_hex_layout_with_zoom(self) -> None:
        if hasattr(self, 'camera_manager'):
            base_hex_size = 36
            expected_hex_size = int(base_hex_size * self.camera_manager.zoom_level)

            if self.hex_layout.hex_size != expected_hex_size:
                self.hex_layout = HexLayout(hex_size=expected_hex_size)

                hl = self.hex_layout
                board_pixel_width = (
                    (self.board_width - 1) * hl.col_spacing
                    + hl.hex_width
                    + (hl.row_offset if self.board_height > 1 else 0)
                )
                board_pixel_height = (
                    (self.board_height - 1) * hl.row_spacing + hl.hex_height
                )

                world_width = int(board_pixel_width * 2)
                world_height = int(board_pixel_height * 2)
                self.camera_manager.set_world_bounds(world_width, world_height)
                self.camera_manager.set_camera_position(
                    self.camera_manager.camera_x,
                    self.camera_manager.camera_y,
                )
