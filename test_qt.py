from dataclasses import dataclass, field
import sys
from PySide6.QtCore import (
    QObject,
    QEvent,
    QTimer,
    QRectF,
    QRect,
)
from PySide6.QtGui import (
    QCloseEvent,
    QExposeEvent,
    QMouseEvent,
    QColor,
    QResizeEvent,
    QWindow,
    QBackingStore,
    QGuiApplication,
    QPainter,
    QFont,
)
from pyecs import (
    Component, EntityEvent, Schedule,
    System, EntityID, World, EventBuffer, Event,
)


@dataclass
class ClickEvent(Event):
    x: float
    y: float


@dataclass
class ClickEntityEvent(EntityEvent):
    entity: EntityID


@dataclass
class Counter(Component):
    value: int = 0


@dataclass
class Rect(Component):
    x: float = 0
    y: float = 0
    w: float = 100
    h: float = 100
    color: QColor = field(default_factory=lambda: QColor(255, 0, 0))


def find_clicked_entity(w: World):
    for e in w.get_resource(EventBuffer).read(ClickEvent):
        for entity in w.query(Rect):
            rect = w.get_component(entity, Rect)
            if rect.x <= e.x <= rect.x + rect.w and rect.y <= e.y <= rect.y + rect.h:
                w.get_resource(EventBuffer).write(ClickEntityEvent(entity))
                return


def add_counter(w: World):
    for e in w.get_resource(EventBuffer).read(ClickEntityEvent):
        if w.has_component(e.entity, Counter):
            counter = w.get_component(e.entity, Counter)
            counter.value += 1


class MainWindow(QWindow):
    world: World
    backingStore: QBackingStore
    timer: QTimer
    schedule: Schedule

    def __init__(self):
        super().__init__()
        self.setTitle("Hello, World!")
        self.resize(800, 600)
        self.timer = QTimer()
        self.timer.setInterval(1000//60)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        self.backingStore = QBackingStore(self)
        self.world = World()
        self.world.add_resource(EventBuffer())
        self.schedule = Schedule()
        self.schedule.add(find_clicked_entity, add_counter)
        self.world.spawn(
            Rect(100, 100, 100, 100, QColor(255, 0, 0)), Counter())
        self.world.spawn(
            Rect(300, 200, 100, 100, QColor(0, 255, 0)), Counter())

    def update(self):
        self.world.get_resource(EventBuffer).update()
        self.schedule.run(self.world)
        self.render()

    def render(self):
        if not self.isExposed():
            return
        background = QRect(0, 0, self.width(), self.height())
        self.backingStore.beginPaint(background)
        device = self.backingStore.paintDevice()
        painter = QPainter(device)
        painter.fillRect(background, QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 20))
        rect_list = self.world.query(Rect)
        for entity in rect_list:
            rect = self.world.get_component(entity, Rect)
            painter.fillRect(
                QRectF(rect.x, rect.y, rect.w, rect.h), rect.color)
            if self.world.has_component(entity, Counter):
                counter = self.world.get_component(entity, Counter)
                painter.drawText(
                    QRectF(rect.x, rect.y, rect.w, rect.h), str(counter.value)
                )
        painter.end()
        self.backingStore.endPaint()
        self.backingStore.flush(background)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        x = e.position().x()
        y = e.position().y()
        self.world.get_resource(EventBuffer).write(ClickEvent(x, y))
        return super().mousePressEvent(e)

    def resizeEvent(self, e: QResizeEvent) -> None:
        self.backingStore.resize(e.size())
        return super().resizeEvent(e)

    def closeEvent(self, e: QCloseEvent) -> None:
        self.timer.stop()
        return super().closeEvent(e)


def main():
    app = QGuiApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
