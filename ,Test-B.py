#!/usr/bin/env python

import sys
import random
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QKeyEvent
from PySide6.QtCore import Qt

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(1000, 600)
        self.points = []
        self.x_min = 20
        self.x_max = 20000
        self.y_min = -80
        self.y_max = 0

    def add_point(self, x, y):
        self.points.append((x, y))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()

        # Background
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # Draw grid lines
        grid_pen = QPen(QColor(200, 200, 200), 1, Qt.DashLine)
        painter.setPen(grid_pen)

        # Horizontal grid lines and labels
        y_steps = 9
        for i in range(y_steps + 1):
            y_value = self.y_min + i * (self.y_max - self.y_min) / y_steps
            y_pixel = self.map_y(y_value)
            painter.drawLine(0, y_pixel, width, y_pixel)
            painter.setPen(Qt.black)
            painter.drawText(5, y_pixel - 2, f"{y_value:.0f}")
            painter.setPen(grid_pen)

        # Vertical grid lines and labels
        x_ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
        for x_val in x_ticks:
            x_pixel = self.map_x(x_val)
            painter.drawLine(x_pixel, 0, x_pixel, height)
            painter.setPen(Qt.black)
            painter.drawText(x_pixel + 2, height - 5, f"{x_val}")
            painter.setPen(grid_pen)

        # Draw axes
        axis_pen = QPen(Qt.black, 2)
        painter.setPen(axis_pen)
        painter.drawLine(0, 0, 0, height)  # Y axis
        painter.drawLine(0, height - 1, width, height - 1)  # X axis

        # Draw points
        point_pen = QPen(QColor(255, 0, 0), 6)
        painter.setPen(point_pen)
        for x_val, y_val in self.points:
            x_px = self.map_x(x_val)
            y_px = self.map_y(y_val)
            painter.drawPoint(x_px, y_px)

    def map_x(self, x):
        return int((x - self.x_min) / (self.x_max - self.x_min) * self.width())

    def map_y(self, y):
        return int((self.y_max - y) / (self.y_max - self.y_min) * self.height())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Graph with Axes and Grid")
        self.graph = GraphWidget(self)
        self.setCentralWidget(self.graph)
        self.setFixedSize(600, 1000)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            x = random.uniform(20, 20000)
            y = random.uniform(-80, 0)
            self.graph.add_point(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

