from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable, Type, Dict, TypeVar, Iterable, Any


class Component:
    pass


class Event:
    pass


class Resource:
    pass


C = TypeVar('C', bound=Component)
E = TypeVar('E', bound=Event)
R = TypeVar('R', bound=Resource)


@dataclass(slots=True, frozen=True)
class EntityID:
    id: int


@dataclass
class EventBuffer:
    current: List[Event] = field(default_factory=list)
    next: List[Event] = field(default_factory=list)

    def read(self, t: Type[E]):
        return [event for event in self.current if isinstance(event, t)]

    def write(self, *events: Event):
        self.next.extend(events)

    def update(self):
        self.current = self.next.copy()
        self.next.clear()


@dataclass
class Observer:
    event_type: Type[Event]
    callback: Callable[[Event, World], None]


@dataclass
class World:
    entities: Dict[EntityID, Dict[Type[Component],
    Component]] = field(default_factory=dict)
    _next_id: int = 0
    resources: Dict[Type[Any], Any] = field(default_factory=dict)
    observers: List[Observer] = field(default_factory=list)

    def spawn(self, *components: Component):
        e_id = EntityID(self._next_id)
        self._next_id += 1
        components_dict = {
            type(component): component for component in components}

        self.entities[e_id] = components_dict
        return e_id

    def despawn(self, entity: EntityID):
        self.entities.pop(entity)

    def query(self, *withs: Type[Component], without: Iterable[Type[Component]] = ()):
        for entity in self.entities:
            has_all_withs = all(
                component_type in self.entities[entity].keys()
                for component_type in withs
            )

            has_none_without = all(
                component_type not in self.entities[entity].keys()
                for component_type in without
            )

            if has_all_withs and has_none_without:
                yield entity

    def insert_resource(self, resource):
        self.resources[type(resource)] = resource

    def get_resource(self, t: Type[R]) -> R:
        return self.resources[t]

    def remove_resource(self, t: Type[R]):
        self.resources.pop(t)

    def get_component(self, entity: EntityID, component_type: Type[C]) -> C:
        return self.entities[entity][component_type]

    def add_component(self, entity: EntityID, component: Component):
        self.entities[entity][type(component)] = component

    def remove_component(self, entity: EntityID, component_type: Type[C]):
        self.entities[entity].pop(component_type)

    def has_component(self, entity: EntityID, component_type: Type[C]) -> bool:
        return component_type in self.entities[entity].keys()

    def add_observer(self, event_type: Type[E], callback: Callable[[E, World], None]):
        observer = Observer(event_type, callback)
        self.observers.append(observer)

    def trigger(self, event: Event):
        for observer in self.observers:
            if isinstance(event, observer.event_type):
                observer.callback(event, self)


System = Callable[[World, EventBuffer], None]


@dataclass
class Schedule:
    systems: List[System] = field(default_factory=list)
    events: EventBuffer = field(default_factory=EventBuffer)

    def add(self, *system: System):
        self.systems.extend(system)

    def run(self, world: World):
        for system in self.systems:
            system(world, self.events)
        self.events.update()
