from ecs import World, Component, Event, EntityID, Schedule, Resource, EventBuffer
from dataclasses import dataclass


@dataclass
class DamageEvent(Event):
    damage: int
    target: EntityID


@dataclass
class Player(Component):
    hp: int


@dataclass
class GameState(Resource):
    total_damage: int = 0


def setup(w: World):
    w.insert_resource(GameState())
    w.spawn(Player(10))
    # w.events.write(DamageEvent(1, player1))


def handle_damage(w: World, e: EventBuffer):
    for damage_event in e.read(DamageEvent):
        player = damage_event.target
        w.get_component(player, Player).hp -= damage_event.damage
        game_state = w.get_resource(GameState)
        game_state.total_damage += damage_event.damage


def write_a_damage(w: World, e: EventBuffer):
    for entity in w.query(Player):
        e.write(DamageEvent(1, entity))


def print_gamestate(w: World, e: EventBuffer):
    r = w.get_resource(GameState)
    print(f"Total damage: {r.total_damage}")
    for entity in w.query(Player):
        print(f"Player {entity.id} hp: {w.get_component(entity, Player).hp}")


def main():
    w = World()
    setup(w)
    s = Schedule()
    s.add(handle_damage, write_a_damage, print_gamestate)
    for _ in range(5):
        s.run(w)


main()
