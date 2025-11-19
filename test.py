from ecs import World, Component, Event, Entity, Schedule, Resource
from dataclasses import dataclass


@dataclass
class DamageEvent(Event):
    damage: int
    target: Entity


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


def handle_damage(w: World):
    for damage_event in w.events.read(DamageEvent):
        player = w.get_entity(damage_event.target)
        player.get_component(Player).hp -= damage_event.damage
        game_state = w.get_resource(GameState)
        game_state.total_damage += damage_event.damage


def write_a_damage(w: World):
    for e in w.query(Player):
        w.events.write(DamageEvent(1, e))


def print_gamestate(w: World):
    r = w.get_resource(GameState)
    print(f"Total damage: {r.total_damage}")
    for e in w.query(Player):
        print(f"Player {e.id} hp: {e.get_component(Player).hp}")


def main():
    w = World()
    setup(w)
    s = Schedule()
    s.add(handle_damage)
    s.add(write_a_damage)
    s.add(print_gamestate)
    for _ in range(5):
        s.run(w)


main()
