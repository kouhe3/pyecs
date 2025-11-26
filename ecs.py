from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable, Type, Dict, TypeVar, Iterable, Any, FrozenSet


class Component:
    pass


class Event:
    pass


class EntityEvent(Event):
    entity: EntityID


class Resource:
    pass


C = TypeVar('C', bound=Component)
E = TypeVar('E', bound=Event)
R = TypeVar('R', bound=Resource)

EntityID = int


@dataclass
class EventBuffer:
    current: Dict[Type[Event], List[Event]] = field(default_factory=dict)
    next: Dict[Type[Event], List[Event]] = field(default_factory=dict)

    def read(self, t: Type[E]) -> List[E]:
        if t in self.current:
            return self.current[t]
        return []

    def write(self, *events: E):
        for ev in events:
            t = type(ev)
            if t not in self.next:
                self.next[t] = []
            self.next[t].append(ev)

    def update(self):
        self.current = self.next.copy()
        self.next.clear()


@dataclass(frozen=True, slots=True)
class Observer:
    event_type: Type[Event]
    callback: Callable[[Event, World], None]


@dataclass(slots=True, frozen=True)
class Archetype:
    components: FrozenSet[Type[Component]]
    entities: List[EntityID] = field(default_factory=list)


@dataclass(slots=True)
class World:
    archetypes: Dict[FrozenSet[Type[Component]], Archetype] = field(default_factory=dict)
    entity_archetype: Dict[EntityID, Archetype] = field(default_factory=dict)
    entity_components: Dict[EntityID, Dict[Type[Component], Component]] = field(default_factory=dict)
    _next_id: int = 0
    resources: Dict[Type[Any], Any] = field(default_factory=dict)
    observers: List[Observer] = field(default_factory=list)
    tick: int = 0  # 新增：当前 tick
    change_ticks: Dict[EntityID, Dict[Type[Component], int]] = field(default_factory=dict)  # 新增：变化 tick
    event_buffer: EventBuffer = field(default_factory=EventBuffer)
    def spawn(self, *components: Component):
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
        if entity not in self.entity_archetype:
            return
        archetype = self.entity_archetype[entity]
        archetype.entities.remove(entity)
        self.entity_archetype.pop(entity)
        if entity in self.entity_components:
            self.entity_components.pop(entity)
        self.change_ticks.pop(entity, None)

    def query(self,
              *withs: Type[Component],
              without: Iterable[Type[Component]] = (),
              changed: set[Type[Component]] = ()):
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
                            self.change_ticks.get(eid, {}).get(comp_type, -1) >= current_tick - 1
                            for comp_type in changed_set
                    ):
                        filter_list.append(eid)
                result.extend(filter_list)
            else:
                result.extend(archetype.entities)
        return result

    def insert_resource(self, resource: R) -> R:
        self.resources[type(resource)] = resource
        return resource

    def get_resource(self, t: Type[R]) -> R:
        return self.resources[t]

    def remove_resource(self, t: Type[R]) -> R:
        return self.resources.pop(t)

    def get_component(self, entity: EntityID, component_type: Type[C]) -> C:
        return self.entity_components[entity][component_type]

    def add_component(self, entity: EntityID, component: C):
        if entity not in self.entity_components:
            raise ValueError(f"Entity {entity} does not exist")
        current_components = self.entity_components[entity]
        comp_type = type(component)
        self.change_ticks[entity][comp_type] = self.tick
        old_archetype = self.entity_archetype[entity]
        current_components[type(component)] = component
        new_component_type = frozenset(set(old_archetype.components) | {type(component)})
        old_archetype.entities.remove(entity)
        if new_component_type not in self.archetypes:
            self.archetypes[new_component_type] = Archetype(new_component_type, [entity])
        else:
            self.archetypes[new_component_type].entities.append(entity)
        new_archetype = self.archetypes[new_component_type]
        self.entity_archetype[entity] = new_archetype

    def remove_component(self, entity: EntityID, component_type: Type[C]) -> C:
        current_components = self.entity_components[entity]
        component_to_remove = current_components.pop(component_type)
        old_archetype = self.entity_archetype[entity]
        new_component_type = frozenset(set(old_archetype.components) - {component_type})
        old_archetype.entities.remove(entity)
        if new_component_type not in self.archetypes:
            self.archetypes[new_component_type] = Archetype(new_component_type, [entity])
        else:
            self.archetypes[new_component_type].entities.append(entity)
        new_archetype = self.archetypes[new_component_type]
        self.entity_archetype[entity] = new_archetype
        self.change_ticks[entity].pop(component_type, None)
        return component_to_remove

    def has_component(self, entity: EntityID, component_type: Type[C]) -> bool:
        if entity not in self.entity_components:
            return False
        else:
            return component_type in self.entity_components[entity]

    def add_observer(self, event_type: Type[E], callback: Callable[[E, World], None]):
        observer = Observer(event_type, callback)
        self.observers.append(observer)

    def trigger(self, event: Event):
        for observer in self.observers:
            if isinstance(event, observer.event_type):
                observer.callback(event, self)

    def get_entities(self) -> List[EntityID]:
        return list(self.entity_archetype.keys())


System = Callable[[World, EventBuffer], None]


@dataclass(slots=True)
class Schedule:
    systems: List[System] = field(default_factory=list)

    def add(self, *system: System):
        self.systems.extend(system)

    def run(self, world: World):
        world.tick += 1
        for system in self.systems:
            system(world, world.event_buffer)
        world.event_buffer.update()
