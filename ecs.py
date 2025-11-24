from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable, Type, Dict, TypeVar, cast, Iterable, Any


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
class EventBuffer():
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
class World:
    entitys: Dict[EntityID, Dict[Type[Component],
                                 Component]] = field(default_factory=dict)
    _next_id: int = 0
    resources: Dict[Type[Any], Any] = field(default_factory=dict)

    def spawn(self, *components: Component):
        e_id = EntityID(self._next_id)
        self._next_id += 1
        components_dict = {
            type(component): component for component in components}

        self.entitys[e_id] = components_dict
        return e_id

    def despawn(self, entity: EntityID):
        self.entitys.pop(entity)

    def query(self, *withs: Type[Component], withous: Iterable[Type[Component]] = ()):
        for entity in self.entitys:
            has_all_withs = all(
                component_type in self.entitys[entity].keys()
                for component_type in withs
            )

            has_none_withous = all(
                component_type not in self.entitys[entity].keys()
                for component_type in withous
            )

            if has_all_withs and has_none_withous:
                yield entity

    def insert_resource(self, resource):
        self.resources[type(resource)] = resource

    def get_resource(self, t: Type[R]) -> R:
        return self.resources[t]

    def remove_resource(self, t: Type[R]):
        self.resources.pop(t)

    def get_component(self, entity: EntityID, component_type: Type[C]) -> C:
        return cast(C, self.entitys[entity][component_type])

    def add_component(self, entity: EntityID, component: Component):
        self.entitys[entity][type(component)] = component

    def remove_component(self, entity: EntityID, component_type: Type[C]):
        self.entitys[entity].pop(component_type)
    def has_component(self, entity: EntityID, component_type: Type[C]) -> bool:
        return component_type in self.entitys[entity].keys()

System = Callable[[World,EventBuffer], None]


@dataclass
class Schedule:
    systems: List[System] = field(default_factory=list)
    events: EventBuffer = field(default_factory=EventBuffer)

    def add(self, *system: System):
        self.systems.extend(system)

    def run(self, world: World):
        for system in self.systems:
            system(world,self.events)
        self.events.update()
