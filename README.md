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

## Example

check examples in test

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
- `add_observer(event_type, callback)`: Add and observer.
- `trigger(event)`: Trigger observers immediately.

### `Schedule`

- `add(*system)`: Adds systems to the schedule.
- `run(world)`: Executes all systems.

### `EventBuffer`

- `read(event_type)`:  
  Returns a list of all events of the specified type from the **current** buffer (i.e., events that were queued during
  the previous tick). If no such events exist, returns an empty list.

- `write(*events)`:  
  Queues one or more events into the **next** buffer. These events will become visible to systems only after the next
  call to `update()`—typically at the end of the current tick.

- `update()`:  
  Finalizes the current tick by moving all events from the **next** buffer to the **current** buffer and clearing the *
  *next** buffer. This ensures that systems always process events that were emitted in the prior tick, preventing race
  conditions or missed events within a single frame.

> **Note**: The `EventBuffer` is designed to support **deferred event processing**, which is essential for deterministic
> and consistent behavior in ECS-based simulations or games. Systems receive the buffer as an argument and should
> generally **read** from it (via `read`) and **write** new events (via `write`), while `update()` is called automatically
> by the `Schedule.run()` method.

## License

[MIT](https://choosealicense.com/licenses/mit/)
