#!/usr/bin/env python

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QRadioButton, QButtonGroup,
    QHBoxLayout, QApplication
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys


class AudioDisplayPopup(QWidget):
    def __init__(self, buffer, samplerate=44100):
        super().__init__()
        self.setWindowTitle("Audio Viewer")
        self.buffer = buffer
        self.samplerate = samplerate

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)

        # Radio buttons
        self.radio_waveform = QRadioButton("Waveform")
        self.radio_spectrum = QRadioButton("Spectrum")
        self.radio_waveform.setChecked(True)

        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.radio_waveform)
        self.radio_group.addButton(self.radio_spectrum)

        self.radio_waveform.toggled.connect(self.update_plot)
        self.radio_spectrum.toggled.connect(self.update_plot)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.radio_waveform)
        button_layout.addWidget(self.radio_spectrum)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.plot_waveform()

    def update_plot(self):
        if self.radio_waveform.isChecked():
            self.plot_waveform()
        else:
            self.plot_spectrum()

    def plot_waveform(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        t = np.linspace(0, len(self.buffer) / self.samplerate, num=len(self.buffer))
        ax.plot(t, self.buffer)
        ax.set_title("Waveform")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        self.canvas.draw()

    def plot_spectrum(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        fft = np.fft.rfft(self.buffer)
        freq = np.fft.rfftfreq(len(self.buffer), 1 / self.samplerate)
        magnitude = np.abs(fft)
        ax.semilogx(freq, 20 * np.log10(magnitude + 1e-12))  # avoid log(0)
        ax.set_title("Spectrum")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.set_xlim(20, self.samplerate / 2)
        self.canvas.draw()


# Test harness for standalone popup
if __name__ == "__main__":
    app = QApplication(sys.argv)
    sr = 44100
    noise = np.random.normal(0, 1, sr).astype(np.float32)
    viewer = AudioDisplayPopup(noise, samplerate=sr)
    viewer.resize(600, 400)
    viewer.show()
    sys.exit(app.exec())

