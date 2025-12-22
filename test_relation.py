from pyecs import EntityID, World, Schedule, Component
from dataclasses import dataclass


@dataclass
class Edge(Component):
    from_: EntityID
    to: EntityID


@dataclass
class Person(Component):
    name: str


@dataclass
class Love(Component):
    pass


w = World()
s = Schedule()
john = w.spawn(Person("John"))
alice = w.spawn(Person("Alice"))
bob = w.spawn(Person("Bob"))
w.spawn(Edge(john, alice), Love())
w.spawn(Edge(alice, bob), Love())

for edge_id in w.query(Edge, Love):
    edge = w.get_component(edge_id, Edge)
    from_p = w.get_component(edge.from_, Person)
    to_p = w.get_component(edge.to, Person)
    print(f"{from_p.name} -love-> {to_p.name}")
