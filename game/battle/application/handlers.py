"""Battle command handlers."""
from __future__ import annotations

from game.battle.domain.events import AttackResolved, ChargeResolved, UnitMoved
from game.battle.domain.services.movement_rules import MovementRules
from game.entities.knight import KnightClass
from game.hex_utils import HexGrid


class MoveUnitHandler:
    def __init__(self, game_state, event_sink):
        if game_state is None:
            raise ValueError("game_state is required for MoveUnitHandler")
        if event_sink is None:
            raise ValueError("event_sink is required for MoveUnitHandler")
        self._game_state = game_state
        self._event_sink = event_sink

    def handle(self, command) -> bool:
        if command is None:
            raise ValueError("command is required for MoveUnitHandler")

        unit = self._game_state.get_unit_by_id(command.unit_id)
        if unit is None:
            raise ValueError(f"unit_id not found: {command.unit_id}")

        move_result = MovementRules.resolve_move(
            unit,
            command.to_x,
            command.to_y,
            self._game_state,
        )
        if not move_result:
            return False

        unit.action_points -= move_result['ap_spent']
        unit.has_moved = True

        from_x, from_y = unit.x, unit.y
        path = move_result['path']
        event = UnitMoved(
            unit_id=id(unit),
            from_x=from_x,
            from_y=from_y,
            to_x=command.to_x,
            to_y=command.to_y,
            path=path,
            ap_spent=move_result['ap_spent'],
            final_face_target=move_result['final_face_target'],
            use_path_animation=move_result['use_path_animation'],
        )
        self._event_sink.publish(event)
        return True


class AttackUnitHandler:
    def __init__(self, game_state, event_sink):
        if game_state is None:
            raise ValueError("game_state is required for AttackUnitHandler")
        if event_sink is None:
            raise ValueError("event_sink is required for AttackUnitHandler")
        self._game_state = game_state
        self._event_sink = event_sink

    def handle(self, command) -> bool:
        if command is None:
            raise ValueError("command is required for AttackUnitHandler")

        attacker = self._game_state.get_unit_by_id(command.attacker_id)
        if attacker is None:
            raise ValueError(f"attacker_id not found: {command.attacker_id}")

        target = self._game_state.get_unit_at(command.target_x, command.target_y)
        if target is None or target.player_id == attacker.player_id:
            return False

        hex_grid = HexGrid()
        attacker_hex = hex_grid.offset_to_axial(attacker.x, attacker.y)
        target_hex = hex_grid.offset_to_axial(command.target_x, command.target_y)
        distance = attacker_hex.distance_to(target_hex)
        attack_range = 1 if attacker.knight_class != KnightClass.ARCHER else 3
        if distance > attack_range:
            return False

        if hasattr(attacker, 'behaviors') and 'attack' in attacker.behaviors:
            attack_behavior = attacker.behaviors['attack']
            if command.enforce_visibility:
                valid_targets = attack_behavior.get_valid_targets(attacker, self._game_state)
                if target not in valid_targets:
                    return False
            result = attack_behavior.execute(attacker, self._game_state, target)
            if not result.get('success'):
                return False

            event = AttackResolved(
                attacker_id=id(attacker),
                target_id=id(target),
                damage=result['damage'],
                counter_damage=result.get('counter_damage', 0),
                attack_angle=result.get('attack_angle'),
                extra_morale_penalty=result.get('extra_morale_penalty', 0),
                extra_cohesion_penalty=result.get('extra_cohesion_penalty', 0),
                should_check_routing=result.get('should_check_routing', False),
            )
            self._event_sink.publish(event)
            return True

        attacker_terrain = self._game_state.terrain_map.get_terrain(attacker.x, attacker.y)
        target_terrain = self._game_state.terrain_map.get_terrain(target.x, target.y)

        damage = attacker.calculate_damage(target, attacker_terrain, target_terrain)
        attacker.consume_attack_ap()

        counter_damage = 0
        if distance == 1:
            counter_damage = target.calculate_counter_damage(
                attacker,
                attacker_terrain,
                target_terrain,
            )

        event = AttackResolved(
            attacker_id=id(attacker),
            target_id=id(target),
            damage=damage,
            counter_damage=counter_damage,
            attack_angle=None,
            extra_morale_penalty=0,
            extra_cohesion_penalty=0,
            should_check_routing=False,
        )
        self._event_sink.publish(event)
        return True


class ChargeUnitHandler:
    def __init__(self, game_state, event_sink):
        if game_state is None:
            raise ValueError("game_state is required for ChargeUnitHandler")
        if event_sink is None:
            raise ValueError("event_sink is required for ChargeUnitHandler")
        self._game_state = game_state
        self._event_sink = event_sink

    def handle(self, command) -> bool:
        if command is None:
            raise ValueError("command is required for ChargeUnitHandler")

        attacker = self._game_state.get_unit_by_id(command.attacker_id)
        if attacker is None:
            raise ValueError(f"attacker_id not found: {command.attacker_id}")

        target = self._game_state.get_unit_at(command.target_x, command.target_y)
        if target is None or target.player_id == attacker.player_id:
            return False

        attacker_from = (attacker.x, attacker.y)
        target_start = (target.x, target.y)
        success, message = attacker.execute_charge(target, self._game_state)
        if not success:
            return False

        attacker_to = None
        if (target.x, target.y) != target_start:
            attacker_to = target_start

        event = ChargeResolved(
            attacker_id=id(attacker),
            target_id=id(target),
            attacker_from=attacker_from,
            attacker_to=attacker_to,
            message=message,
        )
        self._event_sink.publish(event)
        return True
