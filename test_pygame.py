from dataclasses import dataclass
from typing import Tuple

import pygame

from pyecs import (
    EventBuffer,
    Event,
    Component,
    EntityID,
    World,
    Schedule
)


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


@dataclass
class MoveToTarget(Component):
    x: float = 0.0
    y: float = 0.0


pygame.init()
font = pygame.font.SysFont("arial", 20)
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()
state = State()
s = Schedule()
world = World()
my_button = world.spawn(
    Node(300, 300, 100, 50),
    Text("Hello World"),
    Button(),
    HelloWorldButton(),
    MoveToTarget()
)


def render_system(w: World):
    screen.fill('white')
    for entity in w.query(Node, Text):
        node = w.get_component(entity, Node)
        pygame.draw.rect(
            screen, 'blue', (node.x, node.y, node.width, node.height))
        txt = w.get_component(entity, Text)
        surf = font.render(txt.content, True, 'white')
        screen.blit(surf, (node.x, node.y))
    pygame.display.flip()


def mouse_system(w: World):
    buf = w.get_resource(EventBuffer)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            state.running = False
        if ev.type == pygame.MOUSEBUTTONDOWN:

            x, y = pygame.mouse.get_pos()
            state.clicked_pos = (x, y)
            for entity in w.query(Button, Node):
                node = w.get_component(entity, Node)
                if node.x < x < node.x + node.width and node.y < y < node.y + node.height:
                    buf.write(ClickEvent(entity))
            for entity in w.query(MoveToTarget):
                move_target = w.get_component(entity, MoveToTarget)
                move_target.x = x
                move_target.y = y


def handle_hello_world_button(w: World):
    buf = w.get_resource(EventBuffer)
    for event in buf.read(ClickEvent):
        if w.has_component(event.entity, HelloWorldButton):
            hello_button = w.get_component(event.entity, HelloWorldButton)
            hello_button.counter += 1
            w.get_component(event.entity, Text).content = str(
                hello_button.counter)


def move_system(w: World):
    for entity in w.query(Node, MoveToTarget):
        node = w.get_component(entity, Node)
        move_target = w.get_component(entity, MoveToTarget)
        dx = move_target.x - node.x
        dy = move_target.y - node.y
        node.x += (dx - node.width / 2) / 5
        node.y += (dy - node.height / 2) / 5


def setup(w: World):
    x, y = pygame.mouse.get_pos()
    for entity in w.query(Node, MoveToTarget):
        move_target = w.get_component(entity, MoveToTarget)
        move_target.x = x
        move_target.y = y
    w.insert_resource(EventBuffer())


def swap_eventbuffer(w: World):
    buf = w.get_resource(EventBuffer)
    buf.update()


s.add(mouse_system, handle_hello_world_button,
      move_system, render_system, swap_eventbuffer)
setup(world)
while state.running:
    s.run(world)
    clock.tick(60)
pygame.quit()
