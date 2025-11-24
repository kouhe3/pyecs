from ecs import (
    EventBuffer,
    Event,
    Component,
    EntityID,
    World,
    Schedule,
    Resource,
    System
)
from typing import Type, TypeVar, Generic, Dict, List, Callable, Any, Iterable, cast, Union, Tuple
from dataclasses import dataclass, field
import pygame


@dataclass
class Node(Component):
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 50.0


@dataclass
class Text(Component):
    content: str = ""


@dataclass
class Interaction(Component):
    hover: bool = False
    click: bool = False


@dataclass
class Button(Component):
    pass


@dataclass
class ClickEvent(Event):
    entity: EntityID


@dataclass
class HelloWorldButton(Component):
    counter = 0


@dataclass
class State:
    running: bool = True
    clicked_pos: Tuple[float, float] = (0, 0)


pygame.init()
font = pygame.font.SysFont("arial", 20)
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()
state = State()
s = Schedule()
world = World()
mybutton = world.spawn(Node(0, 0, 100, 50), Text(
    "Hello World"), Button(), Interaction(), HelloWorldButton())


def render_system(world: World, e: EventBuffer):
    screen.fill('white')
    for entity in world.query(Node, Text):
        node = world.get_component(entity, Node)
        nx, ny = state.clicked_pos
        node.x = (nx+node.x-50)/2
        node.y = (ny+node.y-25)/2
        pygame.draw.rect(
            screen, 'blue', (node.x, node.y, node.width, node.height))
        txt = world.get_component(entity, Text)
        surf = font.render(txt.content, True, 'white')
        screen.blit(surf, (node.x, node.y))
    pygame.display.flip()


def mouse_system(world: World, e: EventBuffer):
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            state.running = False
        if ev.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            state.clicked_pos = (x, y)
            for entity in world.query(Button, Node):
                node = world.get_component(entity, Node)
                if x > node.x and x < node.x + node.width and y > node.y and y < node.y + node.height:
                    e.write(ClickEvent(entity))


def event_system(world: World, e: EventBuffer):
    for click_event in e.read(ClickEvent):
        world.get_component(click_event.entity, Interaction).click = True
        print("Clicked on entity", click_event.entity.id)
        if world.has_component(click_event.entity, HelloWorldButton):
            counter = world.get_component(
                click_event.entity, HelloWorldButton).counter
            counter += 1
            world.get_component(click_event.entity,
                                HelloWorldButton).counter = counter
            world.get_component(click_event.entity,
                                Text).content = f"{counter}"


s.add(render_system, mouse_system, event_system)
while state.running:
    s.run(world)
    clock.tick(60)
pygame.quit()
