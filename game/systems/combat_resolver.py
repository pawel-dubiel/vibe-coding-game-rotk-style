"""Combat resolution logic decoupled from animations."""
from typing import Dict, Any


class CombatResolver:
    """Resolve combat effects such as casualties, morale, cohesion, and routing."""

    @staticmethod
    def _validate_game_state(game_state) -> None:
        if game_state is None:
            raise ValueError("game_state is required for combat resolution")

    @staticmethod
    def _validate_unit(unit, name: str) -> None:
        if unit is None:
            raise ValueError(f"{name} is required for combat resolution")
        for attr in ('take_casualties', 'is_routing'):
            if not hasattr(unit, attr):
                raise ValueError(f"{name}.{attr} is required for combat resolution")

    @staticmethod
    def _apply_extra_penalties(unit, extra_morale_penalty: float, extra_cohesion_penalty: float) -> None:
        if extra_morale_penalty > 0:
            unit.morale = max(0, unit.morale - extra_morale_penalty)
        if extra_cohesion_penalty > 0 and hasattr(unit, 'cohesion'):
            unit.cohesion = max(0, unit.cohesion - extra_cohesion_penalty)

    @classmethod
    def resolve_attack(cls,
                       attacker,
                       target,
                       damage: int,
                       game_state,
                       counter_damage: int = 0,
                       extra_morale_penalty: float = 0.0,
                       extra_cohesion_penalty: float = 0.0,
                       should_check_routing: bool = False) -> Dict[str, Any]:
        """Apply attack effects to both target and attacker (counter)."""
        cls._validate_game_state(game_state)
        cls._validate_unit(attacker, "attacker")
        cls._validate_unit(target, "target")

        if damage is None or counter_damage is None:
            raise ValueError("damage and counter_damage are required for combat resolution")
        if damage < 0 or counter_damage < 0:
            raise ValueError("damage values must be non-negative")
        if extra_morale_penalty is None or extra_cohesion_penalty is None:
            raise ValueError("extra penalties must be provided for combat resolution")

        target_was_routing = target.is_routing
        attacker_was_routing = attacker.is_routing
        target_initial_soldiers = target.soldiers
        attacker_initial_soldiers = attacker.soldiers

        if damage > 0:
            target.take_casualties(damage, game_state)

        cls._apply_extra_penalties(target, extra_morale_penalty, extra_cohesion_penalty)

        if should_check_routing and not target.is_routing:
            shock_bonus = extra_morale_penalty + extra_cohesion_penalty
            target.check_routing(game_state, shock_bonus=shock_bonus)

        if counter_damage > 0:
            attacker.take_casualties(counter_damage, game_state)

        if not target_was_routing and target.is_routing and hasattr(game_state, 'add_message'):
            game_state.add_message(f"{target.name} breaks and starts routing!", priority=2)

        if not attacker_was_routing and attacker.is_routing and hasattr(game_state, 'add_message'):
            game_state.add_message(f"{attacker.name} breaks from counter-attack!", priority=2)

        return {
            'target_casualties': max(0, target_initial_soldiers - target.soldiers),
            'attacker_casualties': max(0, attacker_initial_soldiers - attacker.soldiers),
            'target_routed': target.is_routing and not target_was_routing,
            'attacker_routed': attacker.is_routing and not attacker_was_routing,
        }

    @classmethod
    def resolve_ranged_casualties(cls, target, damage: int, game_state) -> Dict[str, Any]:
        """Apply ranged damage without extra penalties."""
        cls._validate_game_state(game_state)
        cls._validate_unit(target, "target")
        if damage is None:
            raise ValueError("damage is required for combat resolution")
        if damage < 0:
            raise ValueError("damage must be non-negative")

        target_was_routing = target.is_routing
        target_initial_soldiers = target.soldiers

        if damage > 0:
            target.take_casualties(damage, game_state)

        if not target_was_routing and target.is_routing and hasattr(game_state, 'add_message'):
            game_state.add_message(f"{target.name} breaks and starts routing!", priority=2)

        return {
            'target_casualties': max(0, target_initial_soldiers - target.soldiers),
            'target_routed': target.is_routing and not target_was_routing,
        }
