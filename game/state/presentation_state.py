"""Presentation/controller state: camera, animations, UI selection, and AI orchestration."""
from __future__ import annotations

from typing import Optional

from game.ai.ai_player import AIPlayer
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

        if (tile_x, tile_y) in self.possible_moves:
            move_behavior = self.selected_knight.behaviors.get('move')
            if move_behavior:
                path = move_behavior.get_path_to(
                    self.selected_knight,
                    self._require_game_state(),
                    tile_x,
                    tile_y,
                )

                if path:
                    total_ap_cost = 0
                    current_pos = (self.selected_knight.x, self.selected_knight.y)
                    for next_pos in path:
                        step_cost = move_behavior.get_ap_cost(
                            current_pos,
                            next_pos,
                            self.selected_knight,
                            self._require_game_state(),
                        )
                        total_ap_cost += step_cost
                        current_pos = next_pos

                    self.selected_knight.action_points -= total_ap_cost
                    self.selected_knight.has_moved = True

                    self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)

                    full_path = [(self.selected_knight.x, self.selected_knight.y)] + path
                    self.movement_history[id(self.selected_knight)] = full_path

                    final_face_target = move_behavior.get_auto_face_target(
                        self.selected_knight,
                        self._require_game_state(),
                        tile_x,
                        tile_y,
                    )

                    anim = PathMoveAnimation(
                        self.selected_knight,
                        path,
                        step_duration=0.25,
                        game_state=self._game_state,
                        final_face_target=final_face_target,
                    )
                    self.animation_coordinator.animation_manager.add_animation(anim)

                    self.possible_moves = []
                    self._fog_update_needed = True
                    return True
            else:
                self.selected_knight.consume_move_ap()
                self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)
                start_x, start_y = self.selected_knight.x, self.selected_knight.y

                self.movement_history[id(self.selected_knight)] = [
                    (start_x, start_y),
                    (tile_x, tile_y),
                ]

                anim = MoveAnimation(
                    self.selected_knight,
                    start_x,
                    start_y,
                    tile_x,
                    tile_y,
                    game_state=self._game_state,
                )
                self.animation_coordinator.animation_manager.add_animation(anim)
                self.possible_moves = []
                self._fog_update_needed = True
                return True
        return False

    def move_selected_knight_hex(self, tile_x, tile_y) -> bool:
        if not self.selected_knight:
            return False

        if (tile_x, tile_y) in self.possible_moves:
            move_behavior = self.selected_knight.behaviors.get('move')
            if move_behavior:
                path = move_behavior.get_path_to(
                    self.selected_knight,
                    self._require_game_state(),
                    tile_x,
                    tile_y,
                )

                if path:
                    total_ap_cost = 0
                    current_pos = (self.selected_knight.x, self.selected_knight.y)
                    for next_pos in path:
                        step_cost = move_behavior.get_ap_cost(
                            current_pos,
                            next_pos,
                            self.selected_knight,
                            self._require_game_state(),
                        )
                        total_ap_cost += step_cost
                        current_pos = next_pos

                    self.selected_knight.action_points -= total_ap_cost
                    self.selected_knight.has_moved = True

                    self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)

                    full_path = [(self.selected_knight.x, self.selected_knight.y)] + path
                    self.movement_history[id(self.selected_knight)] = full_path

                    final_face_target = move_behavior.get_auto_face_target(
                        self.selected_knight,
                        self._require_game_state(),
                        tile_x,
                        tile_y,
                    )

                    anim = PathMoveAnimation(
                        self.selected_knight,
                        path,
                        step_duration=0.25,
                        game_state=self._game_state,
                        final_face_target=final_face_target,
                    )
                    self.animation_coordinator.animation_manager.add_animation(anim)

                    self.possible_moves = []
                    self._fog_update_needed = True
                    return True
            else:
                self.selected_knight.consume_move_ap()
                self.pending_positions[id(self.selected_knight)] = (tile_x, tile_y)
                start_x, start_y = self.selected_knight.x, self.selected_knight.y

                self.movement_history[id(self.selected_knight)] = [
                    (start_x, start_y),
                    (tile_x, tile_y),
                ]

                anim = MoveAnimation(
                    self.selected_knight,
                    start_x,
                    start_y,
                    tile_x,
                    tile_y,
                    game_state=self._game_state,
                )
                self.animation_coordinator.animation_manager.add_animation(anim)
                self.possible_moves = []
                self._fog_update_needed = True
                return True
        return False

    def attack_with_selected_knight_hex(self, tile_x, tile_y) -> bool:
        if not self.selected_knight or not self.selected_knight.can_attack():
            return False

        hex_grid = HexGrid()
        attacker_hex = hex_grid.offset_to_axial(
            self.selected_knight.x,
            self.selected_knight.y,
        )
        target_hex = hex_grid.offset_to_axial(tile_x, tile_y)
        distance = attacker_hex.distance_to(target_hex)
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3

        if distance <= attack_range:
            target = self.battle_state.get_knight_at(tile_x, tile_y)
            if not target or target.player_id == self.current_player:
                return False

            if hasattr(self.selected_knight, 'behaviors') and 'attack' in self.selected_knight.behaviors:
                attack_behavior = self.selected_knight.behaviors['attack']
                valid_targets = attack_behavior.get_valid_targets(
                    self.selected_knight,
                    self._require_game_state(),
                )
                if target not in valid_targets:
                    return False
                result = self.selected_knight.behaviors['attack'].execute(
                    self.selected_knight,
                    self._require_game_state(),
                    target,
                )
                if result['success']:
                    damage = result['damage']
                    counter_damage = result.get('counter_damage', 0)
                    attack_angle = result.get('attack_angle', None)
                    extra_morale_penalty = result.get('extra_morale_penalty', 0)
                    extra_cohesion_penalty = result.get('extra_cohesion_penalty', 0)
                    should_check_routing = result.get('should_check_routing', False)

                    anim = AttackAnimation(
                        self.selected_knight,
                        target,
                        damage,
                        counter_damage,
                        attack_angle=attack_angle,
                        extra_morale_penalty=extra_morale_penalty,
                        extra_cohesion_penalty=extra_cohesion_penalty,
                        should_check_routing=should_check_routing,
                        game_state=self._game_state,
                    )
                    self.animation_coordinator.animation_manager.add_animation(anim)
                else:
                    return False
            else:
                self.selected_knight.has_attacked = True

                damage = max(1, self.selected_knight.soldiers // 10)
                target.take_casualties(damage, self._require_game_state())

                ap_cost = 3
                if hasattr(self.selected_knight, 'unit_class'):
                    if self.selected_knight.unit_class == KnightClass.WARRIOR:
                        ap_cost = 4
                    elif self.selected_knight.unit_class == KnightClass.ARCHER:
                        ap_cost = 2
                    elif self.selected_knight.unit_class == KnightClass.CAVALRY:
                        ap_cost = 3
                    elif self.selected_knight.unit_class == KnightClass.MAGE:
                        ap_cost = 2

                if self.terrain_map:
                    target_terrain = self.terrain_map.get_terrain(target.x, target.y)
                    if target_terrain:
                        terrain_movement_cost = target_terrain.movement_cost
                        if terrain_movement_cost > 1.0:
                            terrain_penalty = int((terrain_movement_cost - 1.0) * 2)
                            ap_cost += terrain_penalty

                self.selected_knight.action_points -= ap_cost

                anim = AttackAnimation(
                    self.selected_knight,
                    target,
                    damage,
                    game_state=self._game_state,
                )
                self.animation_coordinator.animation_manager.add_animation(anim)

            self.attack_targets = []
            return True
        return False

    def charge_with_selected_knight_hex(self, tile_x, tile_y) -> bool:
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return False

        target = self.battle_state.get_knight_at(tile_x, tile_y)
        if target and target.player_id != self.current_player:
            start_x, start_y = self.selected_knight.x, self.selected_knight.y
            target_start_x, target_start_y = target.x, target.y

            success, message = self.selected_knight.execute_charge(
                target,
                self._require_game_state(),
            )
            if success:
                if target.x != target_start_x or target.y != target_start_y:
                    anim = MoveAnimation(
                        self.selected_knight,
                        start_x,
                        start_y,
                        target_start_x,
                        target_start_y,
                        game_state=self._game_state,
                    )
                    self.animation_coordinator.animation_manager.add_animation(anim)
                    self.selected_knight.x = target_start_x
                    self.selected_knight.y = target_start_y

                self.add_message(message, priority=2)
                return True

        return False

    def attack_with_selected_knight(self, x, y) -> bool:
        if not self.selected_knight or not self.selected_knight.can_attack():
            return False

        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)

        hex_grid = HexGrid()
        attacker_hex = hex_grid.offset_to_axial(
            self.selected_knight.x,
            self.selected_knight.y,
        )
        target_hex = hex_grid.offset_to_axial(tile_x, tile_y)
        distance = attacker_hex.distance_to(target_hex)
        attack_range = 1 if self.selected_knight.knight_class != KnightClass.ARCHER else 3

        if distance <= attack_range:
            target = self.battle_state.get_knight_at(tile_x, tile_y)
            if target and target.player_id != self.current_player:
                attacker_terrain = self.terrain_map.get_terrain(
                    self.selected_knight.x,
                    self.selected_knight.y,
                )
                target_terrain = self.terrain_map.get_terrain(target.x, target.y)

                if hasattr(self.selected_knight, 'behaviors') and 'attack' in self.selected_knight.behaviors:
                    result = self.selected_knight.behaviors['attack'].execute(
                        self.selected_knight,
                        self._require_game_state(),
                        target,
                    )
                    if result['success']:
                        damage = result['damage']
                        counter_damage = result.get('counter_damage', 0)
                        attack_angle = result.get('attack_angle', None)
                        extra_morale_penalty = result.get('extra_morale_penalty', 0)
                        extra_cohesion_penalty = result.get('extra_cohesion_penalty', 0)
                        should_check_routing = result.get('should_check_routing', False)

                        anim = AttackAnimation(
                            self.selected_knight,
                            target,
                            damage,
                            counter_damage,
                            attack_angle=attack_angle,
                            extra_morale_penalty=extra_morale_penalty,
                            extra_cohesion_penalty=extra_cohesion_penalty,
                            should_check_routing=should_check_routing,
                            game_state=self._game_state,
                        )
                        self.animation_coordinator.animation_manager.add_animation(anim)
                else:
                    damage = self.selected_knight.calculate_damage(
                        target,
                        attacker_terrain,
                        target_terrain,
                    )
                    self.selected_knight.consume_attack_ap()

                    counter_damage = 0
                    if distance == 1:
                        counter_damage = target.calculate_counter_damage(
                            self.selected_knight,
                            attacker_terrain,
                            target_terrain,
                        )

                    anim = AttackAnimation(
                        self.selected_knight,
                        target,
                        damage,
                        counter_damage,
                        game_state=self._game_state,
                    )
                    self.animation_coordinator.animation_manager.add_animation(anim)

                if counter_damage > 0:
                    self.add_message(
                        f"{self.selected_knight.name} attacks {target.name} for "
                        f"{damage} damage! Takes {counter_damage} in return!"
                    )
                else:
                    self.add_message(
                        f"{self.selected_knight.name} attacks {target.name} for {damage} damage!"
                    )

                return True

        return False

    def charge_with_selected_knight(self, x, y) -> bool:
        if not self.selected_knight or self.selected_knight.knight_class != KnightClass.CAVALRY:
            return False

        tile_x, tile_y = self.hex_layout.pixel_to_hex(x, y)

        target = self.battle_state.get_knight_at(tile_x, tile_y)
        if target and target.player_id != self.current_player:
            start_x, start_y = self.selected_knight.x, self.selected_knight.y
            target_start_x, target_start_y = target.x, target.y

            success, message = self.selected_knight.execute_charge(
                target,
                self._require_game_state(),
            )
            if success:
                if target.x != target_start_x or target.y != target_start_y:
                    anim = MoveAnimation(
                        self.selected_knight,
                        start_x,
                        start_y,
                        target_start_x,
                        target_start_y,
                        game_state=self._game_state,
                    )
                    self.animation_coordinator.animation_manager.add_animation(anim)
                    self.selected_knight.x = target_start_x
                    self.selected_knight.y = target_start_y

                self.add_message(message, priority=2)
                return True

        return False

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
