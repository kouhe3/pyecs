from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generic, List, Callable, Type, Dict, TypeVar, Iterable, Any, FrozenSet, Set, cast


class Component:
    """Base class for all components in the ECS architecture."""
    pass


class Event:
    """Base class for all events in the ECS system."""
    pass


class EntityEvent(Event):
    """An event associated with a specific entity.

    Attributes:
        entity (EntityID): The ID of the entity that triggered or is related to this event.
    """
    entity: EntityID


class Resource:
    """Base class for global resources accessible across systems."""
    pass


C = TypeVar('C', bound=Component)
E = TypeVar('E', bound=Event)
R = TypeVar('R', bound=Resource)
EntityID = int


@dataclass
class EventBuffer(Resource):
    """Buffers events across two phases: current and next.

    Used to ensure systems process only events from the previous tick,
    while new events are queued for the next tick.
    """
    current: Dict[Type[Event], List[Event]] = field(default_factory=dict)
    next: Dict[Type[Event], List[Event]] = field(default_factory=dict)

    def read(self, t: Type[E]) -> List[E]:
        """Returns all events of type `t` from the current buffer.

        Args:
            t: The event type to retrieve.

        Returns:
            A list of events of the specified type. Returns an empty list if none exist.
        """
        if t in self.current:
            return cast(List[E], self.current[t])
        return []

    def write(self, *events: Event):
        """Queues one or more events into the next buffer.

        Args:
            *events: Variable-length list of events to queue.
        """
        for ev in events:
            t = type(ev)
            if t not in self.next:
                self.next[t] = []
            self.next[t].append(ev)

    def update(self):
        """Moves all queued events from 'next' to 'current' and clears 'next'.

        Called at the end of each tick to prepare for the next frame.
        """
        self.current = self.next.copy()
        self.next.clear()


@dataclass(frozen=True, slots=True)
class Observer(Generic[E]):
    """Represents a listener for a specific event type.

    Attributes:
        event_type (Type[Event]): The type of event this observer listens to.
        callback (Callable[[Event, World], None]): Function called when the event occurs.
    """
    event_type: Type[E]
    callback: Callable[[E, World], None]


@dataclass(slots=True, frozen=True)
class Archetype(Generic[C]):
    """A grouping of entities that share the exact same set of component types.

    Enables efficient querying by avoiding per-entity component checks.

    Attributes:
        components (FrozenSet[Type[Component]]): Set of component types defining this archetype.
        entities (List[EntityID]): List of entity IDs belonging to this archetype.
    """
    components: FrozenSet[Type[C]]
    entities: List[EntityID] = field(default_factory=list)


@dataclass(slots=True)
class World:
    """Central registry of entities, components, resources, and event observers.

    Manages the ECS world state, including entity-component relationships,
    resource storage, and event dispatching.
    """
    archetypes: Dict[FrozenSet[Type[Component]],
                     Archetype] = field(default_factory=dict)
    entity_archetype: Dict[EntityID, Archetype[Component]
                           ] = field(default_factory=dict)
    entity_components: Dict[EntityID, Dict[Type[Component], Component]
                            ] = field(default_factory=dict)
    _next_id: int = 0
    resources: Dict[Type[Resource], Resource] = field(default_factory=dict)
    tick: int = 0
    change_ticks: Dict[EntityID, Dict[Type[Component], int]
                       ] = field(default_factory=dict)

    def spawn(self, *components: Component) -> EntityID:
        """Creates a new entity with the given components.

        Args:
            *components: Initial components to attach to the new entity.

        Returns:
            The unique ID of the newly created entity.
        """
        e_id = EntityID(self._next_id)
        self._next_id += 1
        component_type = frozenset(type(c) for c in components)
        self.change_ticks[e_id] = {type(c): self.tick for c in components}
        self.entity_components[e_id] = {type(c): c for c in components}
        if component_type not in self.archetypes:
            archetype = Archetype(component_type, [e_id])
            self.archetypes[component_type] = archetype
        else:
            archetype = self.archetypes[component_type]
            archetype.entities.append(e_id)
        self.entity_archetype[e_id] = archetype
        return e_id

    def despawn(self, entity: EntityID):
        """Removes an entity and all its components from the world.

        Args:
            entity: The ID of the entity to remove.
        """
        if entity not in self.entity_archetype:
            return
        archetype = self.entity_archetype[entity]
        archetype.entities.remove(entity)
        self.entity_archetype.pop(entity)
        if entity in self.entity_components:
            self.entity_components.pop(entity)
        self.change_ticks.pop(entity, None)

    def query(
            self,
            *withs: Type[C],
            without: Iterable[Type[C]] = (),
            changed: Set[Type[C]] = set()
    ) -> List[EntityID]:
        """Finds entities matching the specified component constraints.

        Args:
            *withs: Component types the entity must have.
            without: Component types the entity must NOT have.
            changed: Only include entities whose listed components changed in the last tick.

        Returns:
            A list of matching entity IDs.
        """
        with_set = frozenset(withs)
        without_set = frozenset(without)
        changed_set = frozenset(changed)
        current_tick = self.tick
        result: List[EntityID] = []
        for archetype_key, archetype in self.archetypes.items():
            if not with_set.issubset(archetype_key):
                continue
            if archetype_key & without_set:
                continue
            if changed_set:
                filter_list = []
                for eid in archetype.entities:
                    if all(
                            self.change_ticks.get(eid, {}).get(
                                comp_type, -1) >= current_tick - 1
                            for comp_type in changed_set
                    ):
                        filter_list.append(eid)
                result.extend(filter_list)
            else:
                result.extend(archetype.entities)
        return result

    def insert_resource(self, resource: R) -> R:
        """Stores a global resource in the world.

        Args:
            resource: The resource instance to store.

        Returns:
            The inserted resource.
        """
        self.resources[type(resource)] = resource
        return resource

    def get_resource(self, t: Type[R]) -> R:
        """Retrieves a stored resource by type.

        Args:
            t: The type of the resource to retrieve.

        Returns:
            The resource instance.

        Raises:
            KeyError: If no resource of the given type exists.
        """
        return cast(R, self.resources[t])

    def remove_resource(self, t: Type[R]) -> R:
        """Removes and returns a stored resource.

        Args:
            t: The type of the resource to remove.

        Returns:
            The removed resource.

        Raises:
            KeyError: If no resource of the given type exists.
        """
        return cast(R, self.resources.pop(t))

    def get_component(self, entity: EntityID, component_type: Type[C]) -> C:
        """Retrieves a specific component from an entity.

        Args:
            entity: The entity ID.
            component_type: The type of component to retrieve.

        Returns:
            The component instance.

        Raises:
            KeyError: If the entity or component does not exist.
        """
        return cast(C, self.entity_components[entity][component_type])

    def add_component(self, entity: EntityID, component: Component):
        """Adds a component to an existing entity.

        Args:
            entity: The entity ID.
            component: The component instance to add.

        Raises:
            ValueError: If the entity does not exist.
        """
        if entity not in self.entity_components:
            raise ValueError(f"Entity {entity} does not exist")
        current_components = self.entity_components[entity]
        comp_type = type(component)
        self.change_ticks[entity][comp_type] = self.tick
        old_archetype = self.entity_archetype[entity]
        current_components[comp_type] = component
        new_component_type = frozenset(
            set(old_archetype.components) | {comp_type})
        old_archetype.entities.remove(entity)
        if new_component_type not in self.archetypes:
            self.archetypes[new_component_type] = Archetype(
                new_component_type, [entity])
        else:
            self.archetypes[new_component_type].entities.append(entity)
        new_archetype = self.archetypes[new_component_type]
        self.entity_archetype[entity] = new_archetype

    def remove_component(self, entity: EntityID, component_type: Type[C]) -> C:
        """Removes a component from an entity.

        Args:
            entity: The entity ID.
            component_type: The type of component to remove.

        Returns:
            The removed component.

        Raises:
            KeyError: If the entity or component does not exist.
        """
        current_components = self.entity_components[entity]
        component_to_remove = current_components.pop(component_type)
        old_archetype = self.entity_archetype[entity]
        new_component_type = frozenset(
            set(old_archetype.components) - {component_type})
        old_archetype.entities.remove(entity)
        if new_component_type not in self.archetypes:
            self.archetypes[new_component_type] = Archetype(
                new_component_type, [entity])
        else:
            self.archetypes[new_component_type].entities.append(entity)
        new_archetype = self.archetypes[new_component_type]
        self.entity_archetype[entity] = new_archetype
        self.change_ticks[entity].pop(component_type, None)
        return cast(C, component_to_remove)

    def has_component(self, entity: EntityID, component_type: Type[C]) -> bool:
        """Checks whether an entity has a specific component.

        Args:
            entity: The entity ID.
            component_type: The component type to check.

        Returns:
            True if the entity exists and has the component; False otherwise.
        """
        if entity not in self.entity_components:
            return False
        return component_type in self.entity_components[entity]

    def get_entities(self) -> List[EntityID]:
        """Returns a list of all active entity IDs.

        Returns:
            A list of entity IDs currently in the world.
        """
        return list(self.entity_archetype.keys())


System = Callable[[World], None]


@dataclass(slots=True)
class Schedule:
    """Manages and executes a sequence of systems each tick.

    Systems are functions that operate on the world and event buffer.
    """
    systems: List[System] = field(default_factory=list)

    def add(self, *system: System):
        """Registers one or more systems to be run in order.

        Args:
            *system: One or more system functions.
        """
        self.systems.extend(system)

    def run(self, world: World):
        """Executes all registered systems in sequence.

        Increments the world tick before running systems.

        Args:
            world: The world context to pass to each system.
        """
        world.tick += 1
        for system in self.systems:
            system(world)
