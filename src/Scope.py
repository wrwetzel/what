#!/usr/bin/env python3
# -------------------------------------------------------------------------------
#   WRW 27-June-2025 - One little bit of eye candy.
# -------------------------------------------------------------------------------

import sys
import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter # , QTransform, QFontMetrics, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFrame,
    QSlider, QLabel, QDoubleSpinBox, QPushButton, QSizePolicy
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# -------------------------------------------------------------------------------

class VerticalLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
      # self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font())

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(-90)
        painter.translate(-self.height() / 2, -self.width() / 2)

        rect = self.rect()
        rect.setWidth(self.height())
        rect.setHeight(self.width())
        painter.drawText(rect, Qt.AlignCenter, self.text())

# -------------------------------------------------------------------------

class ScopeDialog(QDialog):
    def __init__(self, on_closed =None ):
        super().__init__()
        self.setWindowTitle("Waveform Viewer")
        self.on_closed = on_closed              # WRW 28-June-2025 - Added
        self.signal = np.zeros(44100)           # Placeholder for signal data
        self.siglen = len( self.signal )
        self.start = 0
        self.length = 100
        self.sample_rate = 44100
        self.scale = 1.0

        # ------------------------------------------------------------
        # Layout setup

        layout = QVBoxLayout(self)
        # layout.setContentsMargins(0, 0, 0, 0)    # removes padding.
        # layout.setSpacing(0)                     # eliminates space between widgets.

        # -------------------------------------------
        #   Plot

        plot_layout = QHBoxLayout()
        # plot_layout.setContentsMargins(0, 0, 0, 0)
        # plot_layout.setSpacing(0)
        plot_layout.setAlignment(Qt.AlignLeft)

        vlabel = VerticalLabel("Y-Scale")
        plot_layout.addWidget(vlabel)

        self.scale_slider = QSlider(Qt.Vertical)
        self.scale_slider.setMinimum( 0.0)
        self.scale_slider.setMaximum( 8.0)
        self.scale_slider.setTickInterval( 1 )
        self.scale_slider.setValue(0)
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.scale_slider.valueChanged.connect(self.set_scale)
        plot_layout.addWidget(self.scale_slider)

        # Plotting
        self.figure = Figure()
        self.figure.subplots_adjust(left=0.1, right=0.98, top=0.95, bottom=0.2)

        # self.figure.tight_layout()
        # self.figure = Figure(constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ax = self.figure.add_subplot(111)
        # self.ax.margins(x=0, y=0)  # Remove auto-margins

        plot_layout.addWidget(self.canvas)

        # -------------------------------------------

        # Controls
        controls = QHBoxLayout()

        controls.addWidget(QLabel("Offset:"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)                              
        self.slider.valueChanged.connect(self.set_start)
        controls.addWidget(self.slider)

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)
        vline.setLineWidth(2)
        vline.setStyleSheet("background-color: #a0a0a0;")  # Line color
        controls.addWidget(vline)

        controls.addWidget(QLabel("Length:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(0)                          
        self.zoom_slider.setMaximum(1000)                      
        self.zoom_slider.setValue( 100 )
        self.zoom_slider.valueChanged.connect(self.set_length )
        controls.addWidget(self.zoom_slider)

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)
        vline.setLineWidth(2)
        vline.setStyleSheet("background-color: #a0a0a0;")  # Line color
        controls.addWidget(vline)

        close = QPushButton( "Close" )
        controls.addWidget( close )
        close.clicked.connect( self.close )

        layout.addLayout(plot_layout)
        layout.addLayout(controls)

        # layout.setAlignment(Qt.AlignLeft)
        self.update_plot()


    # ------------------------------------------------------------------------

    def set_scale(self, value):
        self.scale = .1**((value*10)/20)
        self.update_plot()

    def set_start(self, value):
        self.start = value
        self.update_plot()

    def set_length( self, value):
        self.length = value
        self.update_plot()

    def update_signal(self, signal):
        self.signal = signal
        self.siglen = len( signal )
        self.update_plot()

    # -----------------------------------------------------

    def update_plot(self):

        self.ax.clear()

        length = self.siglen * self.length/1000
        length = max( .001 * self.sample_rate, length )          # Show min of .001 second of signal
        length = int( round( length ))

        start = int( round( (self.siglen * self.start/1000) ))
        start = min( start, self.siglen - length )
        start = int( round( start ))

        end = start + length
        end = min( end, self.siglen )
        time_axis = np.arange( start, end ) / self.sample_rate

        segment = self.signal[start:end]            

        self.ax.plot(time_axis, segment, linewidth=1.0 )
        self.ax.set_xlabel("Time (sec)" )
        self.ax.set_ylabel("Amplitude")

        self.ax.set_ylim( -self.scale * 1.2, self.scale * 1.2)

        self.ax.grid(True)
        self.canvas.draw()

    def closeEvent(self, event):                    # Override closeEvent()
        if self.on_closed:
            self.on_closed()
        event.accept()
        super().closeEvent(event)

# -----------------------------------------------------
#   Example usage as standalone test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ScopeDialog()

    # Simulate a signal: 1 sec of 440 Hz sine wave
    t = np.linspace(0, 1, 44100, endpoint=False)
    signal = 1.0 * np.sin(2 * np.pi * 1000 * t)
    signal *= .5
    dialog.update_signal(signal)

    dialog.resize(1000, 300)
    dialog.show()
    sys.exit(app.exec())

