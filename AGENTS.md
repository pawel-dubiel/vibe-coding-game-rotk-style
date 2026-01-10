## Architecture Notes

This project is moving toward a headless, client/server-friendly architecture with
clear domain boundaries. Campaign rules are separate from battle rules.

### Current Battle Split (Minimal Slice)

- **Battle application layer**: command handlers orchestrate moves and emit events.
  - Commands: `game/battle/application/commands.py`
  - Handlers: `game/battle/application/handlers.py`
- **Battle domain events**: data-only events for presentation or server adapters.
  - Events: `game/battle/domain/events.py`
- **Battle rules**: movement rules are now centralized.
  - Rules: `game/battle/domain/services/movement_rules.py`
- **Adapters**: existing battle state is wrapped via a context adapter.
  - Adapter: `game/battle/adapters/battle_context.py`
- **Presentation**: consumes `UnitMoved` events and renders animations.
  - Integration: `game/state/presentation_state.py`

### Why This Split

- Domain logic should not depend on UI or Pygame.
- Command/event flow enables headless simulation and networked clients.
- Explicit context interfaces prevent a "god object" state from leaking everywhere.

### Next Steps

1) Add attack and charge commands/events and route existing logic through handlers.
2) Introduce a headless battle adapter that applies moves immediately (no animations).
3) Replace `GameState` dynamic facade with explicit adapters/interfaces.
4) Split campaign domain/application/infrastructure and enforce fail-fast init.
