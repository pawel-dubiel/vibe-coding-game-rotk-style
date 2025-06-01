# Castle Knights - Game Documentation

Welcome to the Castle Knights tactical combat game documentation. This directory contains comprehensive guides covering all major game systems and mechanics.

## Documentation Index

### 📚 Core Game Systems

- **[Routing Mechanism](routing_mechanism.md)** - Complete guide to the morale and routing system
  - How units break and flee under pressure
  - Rally mechanics and recovery
  - Tactical implications and strategies

### 🏗️ Game Architecture

- **[Combat System](../COMBAT_SYSTEM.md)** *(Planned)* - Detailed combat mechanics
- **[Movement System](../MOVEMENT_SYSTEM.md)** *(Planned)* - Movement, pathfinding, and terrain
- **[Visibility System](../VISIBILITY_SYSTEM.md)** *(Planned)* - Fog of war and line of sight
- **[Unit System](../UNIT_SYSTEM.md)** *(Planned)* - Unit types, stats, and behaviors

### 🎯 Tactical Guides

- **[Terrain Effects](../TERRAIN_EFFECTS.md)** *(Planned)* - How terrain affects combat and movement
- **[General Abilities](../GENERAL_ABILITIES.md)** *(Planned)* - Command abilities and strategies
- **[Unit Facing](../UNIT_FACING.md)** *(Planned)* - Facing mechanics and flanking attacks
- **[Zone of Control](../ZONE_OF_CONTROL.md)** *(Planned)* - ZOC rules and tactical positioning

### 🛠️ Technical Documentation

- **[API Reference](../API_REFERENCE.md)** *(Planned)* - Code API documentation
- **[Test Scenarios](../test_scenarios/README.md)** - Available test scenarios for development
- **[Architecture Overview](../ARCHITECTURE.md)** *(Planned)* - High-level system architecture

### 📋 Feature Documentation

- **[Archer Line-of-Sight Feature](../ARCHER_LINE_OF_SIGHT_FEATURE.md)** - Complete implementation guide for archer LOS restrictions

## Quick Start Guides

### For Players
1. Read the [Routing Mechanism](routing_mechanism.md) to understand morale and unit psychology
2. *(More guides coming soon)*

### For Developers
1. Review the [Architecture Overview](../ARCHITECTURE.md) *(Planned)*
2. Check [Test Scenarios](../test_scenarios/README.md) for testing specific features
3. See [API Reference](../API_REFERENCE.md) *(Planned)* for code integration

## Game Overview

Castle Knights is a hex-based tactical combat game featuring:

- **Deep Tactical Combat**: Positioning, facing, and terrain matter
- **Morale System**: Units can break and route under pressure
- **Line of Sight**: Terrain blocks vision and ranged attacks
- **General Abilities**: Command powers that turn the tide of battle
- **Multiple Unit Types**: Each with unique strengths and capabilities

## System Requirements

The game systems documented here include:

### Core Components
- **Units**: Individual combat entities with stats, behaviors, and AI
- **Terrain**: Hexagonal battlefields with varied terrain effects
- **Combat**: Detailed damage calculations with multiple attack modes
- **Visibility**: Fog of war with line-of-sight calculations
- **AI**: Intelligent computer opponents

### Advanced Features
- **Animation System**: Smooth visual feedback for all actions
- **Save/Load**: Persistent game state management
- **Test Scenarios**: Pre-configured battles for testing features
- **Scenario Editor**: JSON-based scenario creation tools

## Contributing to Documentation

When adding new documentation:

1. **Follow the structure**: Use clear headings and code examples
2. **Cross-reference**: Link related systems and mechanics
3. **Include examples**: Show both code snippets and gameplay scenarios
4. **Update this index**: Add new documents to the appropriate sections

### Documentation Standards

- Use Markdown format for all documentation
- Include code examples with proper syntax highlighting
- Provide both technical implementation details and strategic implications
- Reference specific file locations for code elements
- Include visual diagrams where helpful (ASCII art is acceptable)

## Game Balance Philosophy

The systems documented here reflect a design philosophy emphasizing:

- **Realistic Tactics**: Historical military principles apply
- **Meaningful Choices**: Every decision has strategic consequences  
- **Dynamic Battles**: Situations can change rapidly based on morale and positioning
- **Emergent Gameplay**: Complex interactions arise from simple rules
- **Accessibility**: Deep mechanics that are learnable and intuitive

## Version History

- **v1.0** (Current) - Initial documentation covering routing system
- **v0.9** - Archer line-of-sight feature documentation
- **v0.8** - Core game implementation

---

*This documentation is maintained alongside the game code. For the latest updates, see the main repository.*