## Architecture Notes

This project is moving toward a headless, client/server-friendly architecture with
clear domain boundaries. Campaign rules are separate from battle rules.

### Current Battle Split (High Level)

- **Battle application layer**: command handlers orchestrate battle actions and emit domain events.
- **Battle domain events**: data-only events consumed by presentation or headless adapters.
- **Battle rules**: movement/combat/charge rules are centralized in domain services.
- **Adapters**: existing battle state is wrapped by a context adapter.
- **Presentation**: renders animations and UI responses based on events.

### Why This Split

- Domain logic should not depend on UI or Pygame.
- Command/event flow enables headless simulation and networked clients.
- Explicit context interfaces prevent a "god object" state from leaking everywhere.

### Next Steps

1) Introduce a headless battle adapter that applies actions immediately (no animations).
2) Replace `GameState` dynamic facade with explicit adapters/interfaces.
3) Split campaign domain/application/infrastructure and enforce fail-fast init.
