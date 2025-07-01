#!/usr/bin/env python

import sys
import numpy as np
import sounddevice as sd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
)


def generate_white_noise(duration=2.0, fs=44100):
    noise = np.random.normal(0, 1, int(duration * fs))
    return noise / np.max(np.abs(noise))  # normalize to [-1, 1]


def generate_pink_noise(duration=2.0, fs=44100):
    # Voss-McCartney algorithm
    num_samples = int(duration * fs)
    num_rows = 16
    array = np.zeros(num_samples)
    b = np.random.randn(num_rows, num_samples)
    index = np.zeros(num_rows, dtype=int)

    for i in range(num_samples):
        for j in range(num_rows):
            if np.random.rand() < 1 / (2 ** (j + 1)):
                index[j] = np.random.randint(0, num_samples)
            array[i] += b[j, index[j]]

    array /= np.max(np.abs(array))  # normalize to [-1, 1]
    return array


class NoiseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("White & Pink Noise Generator")
        self.fs = 44100
        self.duration = 2.0  # seconds

        layout = QVBoxLayout()
        self.white_button = QPushButton("Play White Noise")
        self.pink_button = QPushButton("Play Pink Noise")

        self.white_button.clicked.connect(self.play_white)
        self.pink_button.clicked.connect(self.play_pink)

        layout.addWidget(self.white_button)
        layout.addWidget(self.pink_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def play_white(self):
        noise = generate_white_noise(self.duration, self.fs)
        sd.stop()
        sd.play(noise, self.fs)

    def play_pink(self):
        noise = generate_pink_noise(self.duration, self.fs)
        sd.stop()
        sd.play(noise, self.fs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NoiseApp()
    window.resize(300, 150)
    window.show()
    sys.exit(app.exec())
