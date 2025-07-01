#!/usr/bin/env python

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSlider, QLabel, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt


class GainSliderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gain Slider (-80 dB to 0 dB)")
        self.db_value = 0
        self.gain = 1.0

        layout = QVBoxLayout()

        self.label = QLabel(f"dB: {self.db_value} | Gain: {self.gain:.4f}")
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-80, 0)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_gain)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_gain(self, value):
        self.db_value = value
        self.gain = 10 ** (value / 20) if value > -80 else 0.0
        self.label.setText(f"dB: {value} | Gain: {self.gain:.4f}")
        # Now you can use self.gain to scale audio output


if __name__ == \"__main__\":
    app = QApplication(sys.argv)
    window = GainSliderApp()
    window.resize(400, 100)
    window.show()
    sys.exit(app.exec())
