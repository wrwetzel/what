#!/usr/bin/env python

import sys
import numpy as np
from scipy.signal import butter, lfilter
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QSlider, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt
import sounddevice as sd


def band_limited_noise(lowcut, highcut, fs, duration):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(N=4, Wn=[low, high], btype='band')
    white = np.random.normal(0, 1, int(duration * fs))
    filtered = lfilter(b, a, white)
    filtered = filtered / np.max(np.abs(filtered))  # Normalize to [-1, 1]
    return filtered


class NoiseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Band-limited White Noise Generator")
        self.fs = 44100
        self.duration = 2.0  # seconds

        self.lowcut = 500
        self.highcut = 5000
        self.gain = 500

        # -----------------------------------------------------------

        central = QWidget()
        layout = QVBoxLayout()

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_noise)

        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 1000)
        self.gain_slider.setValue(self.gain)
        self.gain_slider.valueChanged.connect(self.update_gain)

        self.gain_label = QLabel(f"Gain")
        self.low_label = QLabel(f"Low cutoff: {self.lowcut} Hz")
        self.high_label = QLabel(f"High cutoff: {self.highcut} Hz")

        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setRange(20, 20000)
        self.low_slider.setValue(self.lowcut)
        self.low_slider.valueChanged.connect(self.update_lowcut)

        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setRange(20, 20000)
        self.high_slider.setValue(self.highcut)
        self.high_slider.valueChanged.connect(self.update_highcut)

        layout.addWidget(self.gain_label)
        layout.addWidget(self.gain_slider)
        layout.addWidget(self.low_label)
        layout.addWidget(self.low_slider)
        layout.addWidget(self.high_label)
        layout.addWidget(self.high_slider)
        layout.addWidget(self.play_button)

        central.setLayout(layout)
        self.setCentralWidget(central)

        self.play_noise()

        # -----------------------------------------------------------

    def update_gain( self, value ):
        self.gain = value
        self.play_noise()

    def update_lowcut(self, value):
        self.lowcut = min(value, self.highcut - 1)
        self.low_label.setText(f"Low cutoff: {self.lowcut} Hz")
        self.play_noise()

    def update_highcut(self, value):
        self.highcut = max(value, self.lowcut + 1)
        self.high_label.setText(f"High cutoff: {self.highcut} Hz")
        self.play_noise()

    def play_noise(self):
        noise = band_limited_noise(self.lowcut, self.highcut, self.fs, self.duration) * self.gain/1000
        sd.stop()
        sd.play(noise, self.fs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NoiseApp()
    window.resize(400, 200)
    window.show()
    sys.exit(app.exec())
