# PyECS

A lightweight, Python-based implementation of the Entity-Component-System (ECS) architecture pattern.

## Overview

The ECS pattern is a popular architectural design in game development and simulation software.

- **Entities**: Unique IDs that act as containers for components.
- **Components**: Pure data objects that hold state.
- **Systems**: Functions that operate on entities with specific sets of components.
- **Resources**: Global state accessible to systems.
- **Events**: A mechanism for systems to communicate asynchronously.

This framework includes:
- Fast archetype-based entity queries.
- A robust event system with buffering.
- Tick-based change tracking for components.
- Support for global resources.

## Core Concepts

- **World**: The central hub managing all entities, components, resources, and events.
- **Component**: A data class holding state (e.g., `Position`, `Health`).
- **System**: A function that processes entities and their components.
- **Resource**: A globally accessible object (e.g., `GameSettings`, `PlayerInput`).
- **Event**: An object passed between systems for communication (e.g., `PlayerDeathEvent`).
- **Archetype**: A group of entities that share the same set of component types.

## API Reference

### `World`
- `spawn(*components)`: Creates an entity with given components.
- `despawn(entity_id)`: Removes an entity.
- `query(*withs, without=(), changed=())`: Finds entities by component types.
- `get_component(entity_id, component_type)`: Gets a component from an entity.
- `add_component(entity_id, component)`: Adds a component to an entity.
- `remove_component(entity_id, component_type)`: Removes a component.
- `has_component(entity_id, component_type)`: Checks if entity has a component.
- `insert_resource(resource)`: Stores a global resource.
- `get_resource(resource_type)`: Retrieves a global resource.
- `add_observer(event_type, callback)`: Registers an event listener.
- `trigger(event)`: Dispatches an event.

### `Schedule`
- `add(*system)`: Adds systems to the schedule.
- `run(world)`: Executes all systems.

## License

[MIT](https://choosealicense.com/licenses/mit/)
