import sys
import random
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QKeyEvent
from PySide6.QtCore import Qt, QRectF

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(600, 1000)
        self.points = []

    def add_point(self, x, y):
        self.points.append((x, y))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # Set pen for axes
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        # Draw axes
        painter.drawLine(0, 0, 0, self.height())  # Y axis
        painter.drawLine(0, self.height(), self.width(), self.height())  # X axis

        # Set pen for points
        pen = QPen(QColor(255, 0, 0), 5)
        painter.setPen(pen)

        for x_val, y_val in self.points:
            x_px = self.map_x(x_val)
            y_px = self.map_y(y_val)
            painter.drawPoint(x_px, y_px)

    def map_x(self, x):
        """ Map x from [20, 20000] to pixel range [0, width] """
        return int((x - 20) / (20000 - 20) * self.width())

    def map_y(self, y):
        """ Map y from [0, -80] to pixel range [0, height] (0 at top) """
        return int((0 - y) / 80 * self.height())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Graph")
        self.graph = GraphWidget(self)
        self.setCentralWidget(self.graph)
        self.setFixedSize(600, 1000)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            # Random example data
            import numpy as np
            x = random.uniform(20, 20000)
            y = random.uniform(-80, 0)
            self.graph.add_point(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

