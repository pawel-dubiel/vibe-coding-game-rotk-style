"""Coordinator for battle and presentation state."""
from __future__ import annotations

from typing import Optional

from game.interfaces.game_state import IGameState
from game.state import BattleState, PresentationState, StateSerializer


class GameState(IGameState):
    """Facade that delegates to BattleState and PresentationState."""

    def __init__(self, battle_config: dict, vs_ai: bool = True):
        if battle_config is None:
            raise ValueError("battle_config is required")

        self.battle_state = BattleState(battle_config)
        self.presentation_state = PresentationState(
            self.battle_state,
            vs_ai=vs_ai,
            screen_width=1024,
            screen_height=768,
        )
        self.presentation_state.bind_game_state(self)
        self.state_serializer = StateSerializer()

        if self.battle_state.battle_intro_message:
            self.presentation_state.add_message(
                self.battle_state.battle_intro_message,
                priority=2,
            )

    def __getattr__(self, name):
        if name in {'battle_state', 'presentation_state', 'state_serializer'}:
            raise AttributeError(name)
        if hasattr(self.battle_state, name):
            return getattr(self.battle_state, name)
        if hasattr(self.presentation_state, name):
            return getattr(self.presentation_state, name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in {'battle_state', 'presentation_state', 'state_serializer'}:
            object.__setattr__(self, name, value)
            return
        if 'battle_state' in self.__dict__ and hasattr(self.battle_state, name):
            setattr(self.battle_state, name, value)
            return
        if 'presentation_state' in self.__dict__ and hasattr(self.presentation_state, name):
            setattr(self.presentation_state, name, value)
            return
        object.__setattr__(self, name, value)

    def get_knight_at(self, x: int, y: int):
        return self.battle_state.get_knight_at(x, y)

    def get_castle_at(self, x: int, y: int):
        return self.battle_state.get_castle_at(x, y)

    def end_turn(self) -> None:
        previous_player = self.battle_state.current_player
        next_player = 2 if previous_player == 1 else 1

        new_movement_history = {}
        for unit_id, path in self.presentation_state.movement_history.items():
            unit = None
            for knight in self.battle_state.knights:
                if id(knight) == unit_id:
                    unit = knight
                    break

            if unit and unit.player_id == previous_player:
                new_movement_history[unit_id] = path
            elif unit and unit.player_id == next_player:
                pass

        self.presentation_state.movement_history = new_movement_history

        result = self.battle_state.end_turn()

        self.presentation_state.deselect_knight()

        for knight in result.rallied_units:
            self.presentation_state.add_message(
                f"{knight.name} rallies and stops routing!",
                priority=2,
            )

        for castle, enemies, damages in result.castle_attacks:
            from game.animation import ArrowAnimation

            anim = ArrowAnimation(
                castle,
                enemies,
                [d[1] for d in damages],
                game_state=self,
            )
            self.presentation_state.animation_coordinator.animation_manager.add_animation(anim)

            total_damage = sum(d[1] for d in damages)
            self.presentation_state.add_message(
                f"Castle archers fire! {total_damage} total damage dealt.")

    def check_victory(self):
        return self.battle_state.check_victory()

    def _update_all_fog_of_war(self) -> None:
        self.battle_state.update_all_fog_of_war()

    def prepare_for_save(self) -> None:
        self.state_serializer.prepare_for_save(self)

    def restore_after_load(self, save_data) -> None:
        self.state_serializer.deserialize_game_state(save_data, self)

        self.presentation_state.camera_manager.camera_x = self.presentation_state.camera_x
        self.presentation_state.camera_manager.camera_y = self.presentation_state.camera_y

        self.battle_state.update_all_fog_of_war()
