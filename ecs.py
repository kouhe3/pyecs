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
R = TypeVar('R',bound=Resource)


@dataclass(slots=True)
class Entity:
    id: int
    components: Dict[Type[Component], Component]

    def __repr__(self) -> str:
        formatted = {k.__name__: v for k, v in self.components.items()}
        return f"Entity(id={self.id}, components={formatted!r})"

    def get_component(self, component_type: Type[C]) -> C:
        return cast(C, self.components[component_type])

@dataclass
class EventBuffer():
    current: List[Any] = field(default_factory=list)
    next: List[Any] = field(default_factory=list)
    def read(self,t:Type[E]):
        for e in self.current:
            if isinstance(e,t):
                yield e
    def write(self,events:Event):
        self.next.append(events)
    def update(self):
        self.current = self.next.copy()
        self.next.clear()
@dataclass
class World:
    entitys: List[Entity] = field(default_factory=list)
    _next_id: int = 0
    events: EventBuffer = field(default_factory=EventBuffer)
    resources: Dict[Type[Any], Any] = field(default_factory=dict)

    def spawn(self, *components: Component):
        e_id = self._next_id
        self._next_id += 1
        components_dict = {
            type(component): component for component in components}
        e = Entity(e_id, components_dict)
        self.entitys.append(e)
        return e

    def despawn(self, entity: Entity):
        self.entitys.remove(entity)

    def query(self, *withs: Type[Component], withous: Iterable[Type[Component]] = ()):
        for entity in self.entitys:
            has_all_withs = all(
                component_type in entity.components
                for component_type in withs
            )

            has_none_withous = all(
                component_type not in entity.components
                for component_type in withous
            )

            if has_all_withs and has_none_withous:
                yield entity

    def get_entity(self, entity: Entity) -> Entity:
        return self.entitys[entity.id]

    def insert_resource(self, resource):
        self.resources[type(resource)] = resource

    def get_resource(self, t: Type[R]) -> R:
        return self.resources[t]

    def remove_resource(self,t:Type[R]):
        self.resources.pop(t)
System = Callable[[World], None]


@dataclass
class Schedule:
    systems: List[System] = field(default_factory=list)

    def add(self, system: System):
        self.systems.append(system)

    def run(self, world: World):
        for system in self.systems:
            system(world)
        world.events.update()
