#!/usr/bin/env python

import sys
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class WaterfallSpectrogram(QWidget):
    def __init__(self, parent=None, sample_rate=44100, nfft=512, buffer_history=200):
        super().__init__(parent)

        self.sample_rate = sample_rate
        self.nfft = nfft
        self.buffer_history = buffer_history
        self.freq_bins = nfft // 2 + 1

        self.spectrogram_data = np.zeros((buffer_history, self.freq_bins), dtype=np.uint8)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Set dB scale range for high-level input
        self.min_db = -10
        self.min_db = -80
        self.max_db = 40

    def update_spectrogram(self, audio_buffer: np.ndarray):
        if len(audio_buffer) < self.nfft:
            padded = np.zeros(self.nfft)
            padded[:len(audio_buffer)] = audio_buffer
        else:
            padded = audio_buffer[:self.nfft]

        windowed = padded * np.hanning(self.nfft)
        spectrum = np.fft.rfft(windowed)
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-10)

        # Debug print for observing range
        # print(f"Power dB range: min={power_db.min():.2f}, max={power_db.max():.2f}")

        # Normalize to 0-255 within the dB range
        norm_power = ((power_db - self.min_db) / (self.max_db - self.min_db)) * 255
        norm_power = np.clip(norm_power, 0, 255).astype(np.uint8)

        self.spectrogram_data = np.roll(self.spectrogram_data, -1, axis=0)
        self.spectrogram_data[-1, :] = norm_power

        self._render_image()

    def _render_image(self):
        height, width = self.spectrogram_data.shape
        img_bytes = self.spectrogram_data.tobytes()
        image = QImage(img_bytes, width, height, width, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)


def OMITget_audio_chunk():
    buffer = np.random.randn(512)
    return buffer

def get_audio_chunk():
    fs = 44100  # 44100 samples per second
    dur = .4
    freq = 440
    gain = .2

    t = np.linspace(0, dur, int(dur * fs), False)   # Generate array with dur*sample_rate steps, ranging between 0 and dur (in seconds)
    note = gain * np.sin(freq * t * 2 * np.pi)    # Generate a sin wave of freq frequency in hz

    audio = note * (2**15 - 1)          # Scale -1 to 1 to 16 bits
    # audio = audio.astype(np.int16)      # Convert to 16-bit data
    return audio



if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = WaterfallSpectrogram()
    widget.resize(800, 600)
    widget.show()

    if False:
        # Simulate periodic updates with random noise
        import threading
        import time
    
        def generate_audio():
            while True:
                buffer = np.random.randn(512)
                widget.update_spectrogram(buffer)
                time.sleep(0.1)
    
        threading.Thread(target=generate_audio, daemon=True).start()

    else:
        timer = QTimer()
        timer.timeout.connect(lambda: widget.update_spectrogram(get_audio_chunk()))
        timer.start(50)  # every 50 ms

    sys.exit(app.exec())

