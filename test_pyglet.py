from __future__ import annotations
from dataclasses import dataclass
import pyglet

# 假设 ecs 模块保持不变（你已定义）
from ecs import (
    EventBuffer,
    Event,
    Component,
    EntityID,
    World,
    Schedule, EntityEvent
)


# --- Components and Events (unchanged) ---
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
    x: int = 0
    y: int = 0


@dataclass
class ClickOnEntityEvent(EntityEvent):
    entity: EntityID


@dataclass
class HelloWorldButton(Component):
    counter: int = 0  # <-- 注意：必须加类型注解，否则类变量！


window = pyglet.window.Window(width=600, height=600, caption="Hello World")


# --- Systems ---
def render_system(w: World, e: EventBuffer):
    window.clear()
    for entity in w.query(Node, Text):
        node = w.get_component(entity, Node)
        text_comp = w.get_component(entity, Text)

        # 绘制矩形（Pyglet 没有直接 draw_rect，需用 OpenGL 或 shapes）
        x, y, w_, h = node.x, node.y, node.width, node.height
        pyglet.shapes.Rectangle(x, y, w_, h, color=(0, 0, 255)).draw()

        # 绘制文字
        label = pyglet.text.Label(
            text_comp.content,
            font_name='Arial',
            font_size=20,
            x=x,
            y=y,
            color=(255, 255, 255, 255)
        )
        label.draw()


def find_who_clicked(w: World, e: EventBuffer):
    for event in e.read(ClickEvent):
        for entity in w.query(Button, Node):
            node = w.get_component(entity, Node)
            if node.x < event.x < node.x + node.width and node.y < event.y < node.y + node.width:
                e.write(ClickOnEntityEvent(entity))


def handle_hello_world_button(w: World, e: EventBuffer):
    for event in e.read(ClickOnEntityEvent):
        if w.has_component(event.entity, HelloWorldButton):
            hello_button = w.get_component(event.entity, HelloWorldButton)
            hello_button.counter += 1
            w.get_component(event.entity, Text).content = str(hello_button.counter)


@dataclass
class State:
    x: int = 0
    y: int = 0
    running: bool = True


state = State()
world = World()
# 创建按钮实体
my_button = world.spawn(
    Node(300, 300, 100, 50),
    Text("Hello World"),
    Button(),
    HelloWorldButton(),
)
s = Schedule()
s.add(find_who_clicked, handle_hello_world_button, render_system)


@window.event
def on_draw():
    s.run(world)


@window.event
def on_mouse_press(x, y, button, modifiers):
    print("mouse press")
    if button == pyglet.window.mouse.LEFT:
        s.events.write(ClickEvent(x, y))


@window.event
def on_close():
    state.running = False
    pyglet.app.exit()


pyglet.app.run()
