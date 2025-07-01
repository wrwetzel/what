#!/usr/bin/env python
# -------------------------------------------------------------------------------------
#   WRW 10-June-2025
#   Graphical display for a hearing test.
#   Bill Wetzel

#   WRW 12-June-2025 - Conversation with Damian at Miracle Ear.
#   He tested me starting at 250 Hz.
#   250 -> 2000 was ok, moderate loss. After 2000 moderate to severe loss.
#   10 dB at 1000 in left, 15 dB at 1000 in right.

#   The audiogram shows hearing loss on the Y-axis, i.e. the gain required to bring the tone
#   up to normal hearing, 0 dB reference level.

#   The LCD display and internal gain_db variable is gain as an engineer would see it, 0 for
#   loud, -80 for quiet.  Quite a headache going between the two, hearing loss for display, 
#   gain_db for all else.

#   From Chat:

#    0 dB HL (top of the chart) = normal hearing
#       The person can hear a tone at the softest volume expected for normal ears.
#
#    +20 dB HL = mild hearing loss
#       The tone must be 20 dB louder than normal for the person to hear it.
#
#    +40-60 dB HL = moderate to severe loss
#       The person needs that much gain at that frequency.
#
#    80+ dB HL (bottom of chart) = profound loss
#       The person may not hear even loud tones.

# -------------------------------------------------------------------------------------
#   Standard audiogram:
#       Frequencies tested: 125 Hz, 250 Hz, 500 Hz, 1000 Hz, 2000 Hz, 3000Hz, 4000 Hz, and 8000 Hz.
#       Loss -10 to 120
#       Right ear - Red 'o'
#       Left ear - Blue 'x'

#   This does not conform to that standard.

# -------------------------------------------------------------------------------------

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import random
import re
import math
import datetime
import sounddevice as sd
from collections import defaultdict
from enum import IntEnum
from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal, Slot, QRect, QFile, QTextStream, QSettings
from PySide6.QtCore import QStandardPaths

from PySide6.QtGui import QPainter, QPen, QColor, QFont, QKeyEvent, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QSizePolicy, QLabel, QPushButton, QRadioButton, QGroupBox, QLineEdit
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtWidgets import QMenuBar, QMenu, QDialog, QFormLayout, QDialogButtonBox
from PySide6.QtWidgets import QTextBrowser, QTextEdit 

from Player import Player
import what_version

# -------------------------------------------------------------------------------------
#   Some constants
#   18-June-2025 - Just discovered IntEnum for reverse mapping from int value to name. Thanks, chat.

class SM( IntEnum ):
    S_Start = 0         # States
    S_Wait = 1
    S_ClickWait = 2
    S_Accepted = 3
    S_ClickAccepted = 4
    S_Rejected = 5
    S_ClickRejected = 6
    S_Complete = 7
    
class IM( IntEnum ):
    I_Play = 0         # Inputs
    I_Accept = 1
    I_Reject = 2
    I_Repeat = 3
    I_Click = 4

class Const():
    pointDiameter = 4
    markerDiameter = 30
    markerPen = 2
    graphBG = '#26313d'
    graphBG = '#e0e0ff'
    License = 'License.txt'
    stdConfig = QStandardPaths.standardLocations(QStandardPaths.AppConfigLocation)[0]
    Settings_Config_File = 'what.settings.conf'
    Copyright = f"Copyright \xa9 2025 Bill Wetzel"

# -------------------------------------------------------------------------------------
#   _type: list, dict, int, more?

def nested_dict(n, _type):
    if n == 1:
        return defaultdict(_type)
    else:
        return defaultdict(lambda: nested_dict(n-1, _type))

# -------------------------------------------------------------------------------------

class ParameterDialog( QDialog ):
    def __init__(self, ppd, start_freq, end_freq, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Parameters")
        layout = QFormLayout(self)

        self.start_freq_edit = QLineEdit( str( start_freq ))
        self.end_freq_edit = QLineEdit( str( end_freq ))
        self.ppd_edit = QLineEdit( str(ppd) )

        layout.addRow("Start Frequency:", self.start_freq_edit)
        layout.addRow("End Frequency:", self.end_freq_edit)
        layout.addRow("Points per Octave:", self.ppd_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            int(self.ppd_edit.text()),
            int(self.start_freq_edit.text()),
            int(self.end_freq_edit.text())
        )

# -------------------------------------------------------------------------------------

class ColorIndicator(QLabel):
    def __init__(self, size=27, parent=None):       # Size to match height of lcd
        super().__init__(parent)
        self._size = size
        self.setFixedSize(QSize(size, size))
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.setAlignment(Qt.AlignCenter)
        self.setColor( '#c0c0c0' )

    def setColor(self, color):
        self.setStyleSheet(f"background-color: {color}; border: 1px solid black;")

# -------------------------------------------------------------------------------------

class LCDLabel( QLabel ):
    def __init__(self, digit_count=6, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setDigitCount(digit_count)
        font = QFont("Courier", 20, QFont.Bold)  # monospaced + large
        self.setFont(font)
        self.setStyleSheet("background-color: black; color: lime; padding: -3px 2px;")
        self.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )

    def setDigitCount( self, n):
        self.digit_count = n
        self.setText("0".rjust(n))

    def display(self, value):
        self.setText(str(value).rjust(self.digit_count))

# -------------------------------------------------------------------------------------
#   0, 0 is upper left.

class GraphWidget( QWidget ):
    pointClicked = Signal(float, float)  # freq, gain_db

    def __init__(self, loss_db_min, loss_db_max, parent=None ):
        super().__init__(parent)
        self.points = []
        self.margin_x = 40              # Margin in the X-direction on the Y-axis
        self.margin_y = 30              # Margin in the Y-direction on the X-axis
        self.loss_db_min = loss_db_min
        self.loss_db_max = loss_db_max
        self.marker = None              # WRW 16-June-2025 - Show marker where tone is being played.

    def set_parameters( self, start_freq, end_freq ):   # WRW 19-June-2025 - separate from __init__()
        self.start_freq = start_freq    
        self.end_freq = end_freq

    def add_point( self, x, y, color ):
        self.points.append((x, y, color))
        self.update()

    def clear_points( self ):
        self.points = []
        self.update()

    def set_marker( self, x, y, color ):
        self.marker = (x, y, color )
        self.update()

    def clear_marker( self ):
        self.marker = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()

        self.graph_width = width - 2 * self.margin_x
        graph_height = height - 2 * self.margin_y

        # --------------------------------------------------
        # Draw background

        painter.fillRect(self.rect(), QColor(Const.graphBG))

        # --------------------------------------------------
        # Set pen for grid lines

        grid_pen = QPen(QColor(128, 128, 128), 1, Qt.DashLine)
        # grid_pen = QPen(QColor(128, 128, 128), 1, Qt.DotLine)
        painter.setPen(grid_pen)

        # --------------------------------------------------
        # Horizontal grid lines and labels for Y axis

        y_steps = 8
        for i in range(y_steps + 1):
            y_value = self.loss_db_min + i * (self.loss_db_max - self.loss_db_min) / y_steps
            y_pixel = self.margin_y + (y_value - self.loss_db_min) / (self.loss_db_max - self.loss_db_min) * graph_height

            painter.drawLine(self.margin_x, y_pixel, width - self.margin_x, y_pixel)
            painter.setPen(Qt.black)
            painter.drawText( 15, y_pixel +2 , f"{y_value:.0f}")      # +2 to center text relative to line
            painter.setPen(grid_pen)

        # --------------------------------------------------
        # Vertical grid lines and labels (log scale) for X axis
        #   WRW 17-June-2025 - Originally a built in array, now generate.
        #       freqs = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]

        # ---------------------------------------------------------------
        #   Generate a bunch of frequencies from 1 to 100000, then pick out the range we want.

        base_freqs = [1, 2, 5]
        decade = 1
        freqs = []

        while True:
            for freq in base_freqs:
                new_freq = freq * decade 
                freqs.append( new_freq )

            if new_freq > 100000:
                break

            decade *= 10

        freqs = [t for t in freqs if self.start_freq <= t <= self.end_freq ]

        # ---------------------------------------------------------------
        #   Draw vertical lines and label the X axis

        for freq in freqs:
            painter.setPen(grid_pen)

            x_pixel = self.map_freq(freq, self.graph_width)
            painter.drawLine(x_pixel, self.margin_y, x_pixel, height - self.margin_y)

            painter.setPen(Qt.black)

            txt = f"{freq:,}"
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(txt)

            painter.drawText( x_pixel - text_width//2, height-self.margin_y+20, txt )   # // integer div to avoid blurry text on some platforms

        # --------------------------------------------------
        # Draw axes

        axis_pen = QPen(Qt.black, 2)
        painter.setPen(axis_pen)
        painter.drawLine(self.margin_x, self.margin_y, self.margin_x, height - self.margin_y)  # Y axis
        painter.drawLine(self.margin_x, height - self.margin_y, width - self.margin_x, height - self.margin_y)  # X axis

        # --------------------------------------------------
        # Draw points

        for x_val, y_val, color in self.points:
            dia = Const.pointDiameter
            painter.setPen(QPen(QColor(color), dia ))
            x_px = self.map_freq(x_val, self.graph_width)
            y_px = self.margin_y + (y_val - self.loss_db_min) / (self.loss_db_max - self.loss_db_min) * graph_height
            # painter.drawPoint( x_px - dia/2, y_px - dia/2)
            rect = QRect( x_px-dia/2, y_px-dia/2, dia, dia)
            painter.drawEllipse(rect)

        # --------------------------------------------------
        #   Draw marker, if any.

        if self.marker:
            x_val = self.marker[0]
            y_val = self.marker[1]
            color = self.marker[2]
            dia = Const.markerDiameter
            pen = QPen( QColor(color), Const.markerPen )
            painter.setPen( pen )
            painter.setBrush(Qt.transparent )
            x_px = self.map_freq(x_val, self.graph_width)
            y_px = self.margin_y + (y_val - self.loss_db_min) / (self.loss_db_max - self.loss_db_min) * graph_height
            rect = QRect( x_px-dia/2, y_px-dia/2, dia, dia)
            painter.drawEllipse(rect)

        # if hasattr(self, "last_click"):             # For debugging int() roundoff problems
        #     x, y = self.last_click
        #     painter.setPen(QPen(Qt.red, 1))
        #     painter.drawLine(x - 5, y, x + 5, y)
        #     painter.drawLine(x, y - 5, x, y + 5)

    # --------------------------------------------------
    #   Convert linear frequency to point on graph in log scale.

    def map_freq(self, freq, graph_width ):
        log_min = math.log10(self.start_freq)
        log_max = math.log10(self.end_freq)
        log_freq = math.log10(freq)
        return (log_freq - log_min) / (log_max - log_min) * graph_width + self.margin_x

    # --------------------------------------------------------

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:
            x = round( event.position().x())
            y = round( event.position().y())
            self.handle_click(x, y)

    def handle_click(self, x_px, y_px):
        # self.last_click = (x_px, y_px)        # For debugging int() roundoff problems
        # self.update()

        width = self.width() - 2 * self.margin_x
        height = self.height() - 2 * self.margin_y
    
        # Ensure click is inside plot area
        if not (self.margin_x <= x_px <= self.width() - self.margin_x and
                self.margin_y <= y_px <= self.height() - self.margin_y):
            return
    
        # Convert X (log scale)
        x_ratio = (x_px - self.margin_x) / width
        freq = self.start_freq * (self.end_freq / self.start_freq) ** x_ratio
    
        # Convert Y (audiogram: 0 dB at top)
        y_ratio = (y_px - self.margin_y) / height
        hearing_loss = self.loss_db_min + (self.loss_db_max - self.loss_db_min) * y_ratio
        loss_db = -hearing_loss
    
        self.pointClicked.emit( freq, loss_db )

# -------------------------------------------------------------------------------------

#   Test points
#   20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240, 20480
#        10 octaves,
#        48 points at 4 points/octave
#        30 points at 3 points/octave

#   20, 200, 2000, 20000
#         3 decades,
#         48 points at 16 points/decade
#         30 points at 10 points/decade

# -------------------------------------------------------------------------------------

class MainWindow( QMainWindow ):
    def __init__(self ):
        super().__init__()

        # ------------------------------------------------------------------

        self.windowTitle = "What? (Bill's Hearing Test)"
        self.setup_menus()

        # ------------------------------------------------------------------
        #   Set up the player and test tones. Reused Player developed several years ago.

        self.p = Player()
        self.p.set_waveshape( 'sin' )       # 'sin' (default), 'sawtooth', 'square', 'triangle'.

        self.dur = .20                      # Test tone total duration: attack + release + sustain. Repeated 3 times.
        trans = .01                         # Attack and release time to prevent sharp edge
        geom_flg = False                    # False for linear attack and release, True for geometric
        self.p.set_envelope( adsr = [[0, 1, trans, geom_flg],           # Attack. Initial gain, final gain, duration, geometric
                                    [1, 1, 0, geom_flg ],               # Decay
                                    [1, 1, self.dur, geom_flg],         # Sustain
                                    [1, 0, trans, geom_flg]] )          # Release

        # ------------------------------------------------------------------
        #   No need to make gain range a parameter yet.

        self.loss_db_min = 0
        self.loss_db_max = 80    
        self.gain_db_min = -80
        self.gain_db_max = 0
        self.reference_level = -80      # For hearing-loss conversion

        # ------------------------------------------------------------------
        #   Set up the UI

        self.status = self.statusBar()
        self.stateLabel = QLabel( "Current-state, Input --> fsm-function() --> Next-state" )

        self.status.addPermanentWidget(self.stateLabel)

        self.setWindowTitle( self.windowTitle )

        self.graph = GraphWidget( self.loss_db_min, self.loss_db_max, self )
        self.graph.pointClicked.connect( self.pointClick )

        self.playing = ColorIndicator( )

        self.gain_lcd = LCDLabel()
        self.gain_lcd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gain_lcd.setDigitCount(6)
        self.gain_lcd.adjustSize()

        self.freq_lcd = LCDLabel()
        self.freq_lcd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.freq_lcd.setDigitCount(8)
        self.freq_lcd.adjustSize()

        self.completed_lcd = LCDLabel()
        self.completed_lcd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.completed_lcd.setDigitCount(6)
        self.completed_lcd.adjustSize()

        self.user_text_box = QLineEdit()
        self.user_text_box.setPlaceholderText("Name:")
        self.user_text_box.setFixedWidth(100)
        self.user_text_box.returnPressed.connect( self.return_pressed )
        self.user_text_box.setFocusPolicy(Qt.ClickFocus)

        tone_button = QPushButton( "Test Tone" )
        tone_button.clicked.connect( self.play_test_tone )
        tone_button.setFocusPolicy(Qt.NoFocus)

        save_button = QPushButton( "Save" )
        save_button.clicked.connect( self.do_save )
        save_button.setFocusPolicy(Qt.NoFocus)

        clear_button = QPushButton( "Reset" )
        clear_button.clicked.connect( lambda: self.reset() )
        clear_button.setFocusPolicy(Qt.NoFocus)

        exit_button = QPushButton( "Exit" )
        exit_button.clicked.connect( QApplication.quit )
        exit_button.setFocusPolicy(Qt.NoFocus)

        # -----------------------------------------------

        self.radio1 = QRadioButton("Binaural")
        self.radio2 = QRadioButton("Left")
        self.radio3 = QRadioButton("Right")
        self.radio1.setChecked(True)  # default selection

        self.radio1.setFocusPolicy(Qt.NoFocus)
        self.radio2.setFocusPolicy(Qt.NoFocus)
        self.radio3.setFocusPolicy(Qt.NoFocus)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio1)
        radio_layout.addWidget(self.radio2)
        radio_layout.addWidget(self.radio3)

        radio_group = QGroupBox()
        radio_group.setLayout(radio_layout)
        radio_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        radio_group.setFocusPolicy(Qt.NoFocus)

        # -----------------------------------------------
        control_layout = QHBoxLayout()
        control_layout.setSpacing(6)
        control_layout.setContentsMargins(0, 0, 0, 0)       # Left, Top, Right, Bottom

        control_layout.addWidget( self.playing, alignment=Qt.AlignLeft )
        control_layout.addWidget( self.gain_lcd, alignment=Qt.AlignLeft )
        control_layout.addWidget( self.freq_lcd, alignment=Qt.AlignLeft )
        control_layout.addWidget( self.completed_lcd, alignment=Qt.AlignLeft )
        control_layout.addWidget( self.user_text_box, alignment=Qt.AlignLeft )
        control_layout.addWidget( radio_group, alignment=Qt.AlignLeft  )
        control_layout.addWidget( tone_button, alignment=Qt.AlignLeft )
        control_layout.addWidget( save_button, alignment=Qt.AlignLeft )
        control_layout.addWidget( clear_button, alignment=Qt.AlignLeft )
        control_layout.addWidget( exit_button, alignment=Qt.AlignLeft )
        control_layout.addStretch()

        instructions_layout = QVBoxLayout()
        txt = """<b>Play next tone:</b> Space / Down-Arrow. <b>Play specific tone:</b> Click in graph.
                 <b>Accept tone:</b> Right-Arrow. <b>Reject tone:</b> Left-Arrow. <b>Repeat tone:</b> Up-Arrow."""
        txt = re.sub( r'\s+', ' ', txt )    # Remove newlines and extra space.

        instructions = QLabel( txt )
        instructions.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        instructions_layout.addWidget( instructions )

        self.done_label = QLabel( "All done" )
        self.done_label.setStyleSheet("font-size: 18px;")
        self.done_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.done_label.hide()
        instructions_layout.addWidget( self.done_label )

        container = QWidget()
        outer_layout = QVBoxLayout( container )
        outer_layout.addLayout( control_layout )
        outer_layout.addLayout( instructions_layout )
        outer_layout.addWidget( self.graph )

        outer_layout.setSpacing(6)                          # Spacing between elements of outer_layout: control, instructions, graph
        outer_layout.setContentsMargins(10, 10, 10, 10)     # Left, Top, Right, Bottom

        self.setLayout(outer_layout)
        self.setCentralWidget( container )

        # -----------------------------------------

        self.init_state_machine()

        # -----------------------------------------
        #   Restore saved settings

        settings = QSettings( str( Path( Const.stdConfig, Const.Settings_Config_File )), QSettings.IniFormat )
        # points_per_decade = settings.value("points_per_decade" )
        points_per_octave = settings.value("points_per_octave" )
        start_freq = settings.value("start_freq" )
        end_freq = settings.value("end_freq" )

        if (points_per_octave is not None) and (start_freq is not None) and (end_freq is not None):
            self.set_parameters( int(points_per_octave), int(start_freq), int(end_freq) )

        else:
            self.set_default_parameters()

    # -------------------------------------------------------------------------------------

    def set_default_parameters( self ):
        self.set_parameters( 16, 20, 20000 )

    # -------------------------------------------------------------------------------------
    #   Count and range parameters for test tones and graph.
    #   Started with octaves but switched to decades.

    def set_parameters( self, points_per_octave, start_freq, end_freq ):

        self.graph.set_parameters( start_freq, end_freq )                                                 

        #   Primary parameters

        self.points_per_octave = points_per_octave
        self.start_freq = start_freq
        self.end_freq = end_freq

        #   Derived parameters

        # self.decades = math.log10( self.end_freq / self.start_freq )
        # self.points_total = math.ceil( self.decades * self.points_per_decade )

        self.points_per_octave = points_per_octave = 3
        self.octaves = math.log2( self.end_freq / self.start_freq )
        self.points_total = math.ceil( self.octaves * self.points_per_octave )

        # ------------------------------------------------------------------
        #   Generate test frequecies - randomize to test in random order.
        #   Base 2 and base 10 with log2 and log10 produced identical results.
        #   Keep base 2 as now switched to octaves.

        # self.test_freqs = np.logspace( np.log10(self.start_freq), np.log10(self.end_freq), num=self.points_total+1 )
        # print( "base 10", self.test_freqs )

        self.test_freqs = np.logspace( np.log2(self.start_freq), np.log2(self.end_freq), num=self.points_total+1, base=2 )
        self.test_freqs = np.round( self.test_freqs )
        random.shuffle( self.test_freqs )

        # -----------------------------------------
        #   Generate test gains - not randomized, test in order from lowest to highest.
        #   Accept at first heard to short-circuit test to avoid obvious results from louder tones.

        self.test_gains_db = []
        self.gindex = 0
        for gain_db in range( self.gain_db_min, self.gain_db_max + 10, 10 ):            # -80 to 0
            self.test_gains_db.append( gain_db )

        self.reset()

    # -------------------------------------------------------------------------------------

    @Slot()
    def reset( self ):
        self.saved_flag = False
        self.sm_state = SM.S_Start
        self.findex = 0
        self.gindex = 0
        self.current_freq = self.test_freqs[ self.findex ]
        self.current_gain_db = self.test_gains_db[ self.gindex ]

        self.current_ck_freq = None                 # Bug catcher
        self.current_ck_gain_db = None              # Bug catcher

        self.results = nested_dict( 2, int )        # Index by freq, gain to get results: True or False
        self.graph.clear_points()
        self.graph.clear_marker()
        self.done_label.hide()
        self.freq_lcd.display( 'Pitch' )
        self.gain_lcd.display( 'Gain' )
        self.completed_lcd.display( 'Step' )
        self.status.showMessage( "Play next tone or click in graph.")
        self.stateStack = None

    # ==============================================================================
    #   
    #   S_Start     -       At beinning of test, only action is play tone.
    #   S_Wait      -       After tone played, waiting for accept or reject
    #   S_ClickWait      -  After tone played, waiting for accept or reject
    #   S_Accepted  -       After accept, user may change mind and reject, repeat, play next
    #   S_ClickAccepted  -  After accept, user may change mind and reject, repeat, play next
    #   S_Rejected  -       After reject, user may change mind and accept, repeat, play next
    #   S_ClickRejected  -  After reject, user may change mind and accept, repeat, play next
    #   S_Complete  -       At end of test, all tones played, no further action
    #
    # ------------------------------------------------------------------------------
    #   WRW 16-June-2025 - The user interactions were getting a bit awkward and the
    #       code a bit messy. Try a FSM approach. Looks great. Haven't used this   
    #       structure since probably 1984 or 1985. 40 years ago, ouch!
    #       The matrix contains the function that is executed for a given state / input pair.
    #       The function returns the next stat or None to remain in current state.

    #       Issue when mixing clicks and next. The if the click is accepted then
    #       the play-next advances to next freq in list. If click is not accepted then play-next
    #       advances to next gain in list. I believe the click should not interfere with list/play-next at all
    #       but still needs to be accepted and added to results or rejected.

    #   WRW 17-June-2025 - Try to resolve with self.clickSubState flag instead of doubling the state matrix.
    #       Yes, a kludge but should be OK.

    #   WRW 18-June-2025 - No, add S_Click* states instead for explicit control.
    #       Enter S_Click* states with mouse click. Exit with Space/Down to play next tone in sequence.
    #       I sure hope the ability to interrupt the current tone sequence with a click is useful, it
    #       took a lot to do it right: additional states and a stack to save the non-click state when
    #       enter the click state. Not really a stack but like one with a depth of one.
    #       The state machine made this relatively easy to do.

    def init_state_machine( self ):
        # ------------------------------------------------------------------------------------------------------------------
        # State: S_Start         S_Wait           S_ClickWait        S_Accepted               S_ClickAccepted          S_Rejected               S_ClickRejected           S_Complete
                                                                                                                                                                                     #   Input:
        self.state_matrix= [                                                                                                                                                         #   --------
            [   self.sm_play,    self.sm_play,    self.sm_play,      self.sm_play_next_freq,  self.sm_play,            self.sm_play_next_gain,  self.sm_play,             None,  ],  #   I_Play
            [   None,            self.sm_accept,  self.sm_ckaccept,  self.sm_accept,          self.sm_ckaccept,        self.sm_accept,          self.sm_ckaccept,         None,  ],  #   I_Accept
            [   None,            self.sm_reject,  self.sm_ckreject,  self.sm_reject,          self.sm_ckreject,        self.sm_reject,          self.sm_ckreject,         None,  ],  #   I_Reject
            [   None,            self.sm_repeat,  self.sm_ckrepeat,  self.sm_repeat,          self.sm_ckrepeat,        self.sm_repeat,          self.sm_ckrepeat,         None,  ],  #   I_Repeat
            [   self.sm_ckplay,  self.sm_ckplay,  self.sm_ckplay,    self.sm_ckplay,          self.sm_ckplay,          self.sm_ckplay,          self.sm_ckplay,           None,  ],  #   I_Click
        ]

    # --------------------------------------------------------
    #   User clicked a point on the graph. Y-axis on graph
    #   is hearing loss. Convert to gain_db for tone
    #   to be heard at that loss.

    @Slot( float, float )
    def pointClick( self, freq, hearing_loss ):
        gain_db = self.reference_level - hearing_loss
        self.sm_proc_input( IM.I_Click, freq=freq, gain_db=gain_db )

    # --------------------------------------------------------
    #   User pressed a key

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.sm_proc_input( IM.I_Play )

        elif event.key() == Qt.Key_Right:
            self.sm_proc_input( IM.I_Accept )

        elif event.key() == Qt.Key_Left:
            self.sm_proc_input( IM.I_Reject )

        elif event.key() == Qt.Key_Down:
            self.sm_proc_input( IM.I_Play )

        elif event.key() == Qt.Key_Up:
            self.sm_proc_input( IM.I_Repeat )

        else:
            super().keyPressEvent(event)    # Pass all else along

    # -------------------------------------------------------------------------
    #   Dispatch state-machine function from state-matrix, input, current state.
    #   Update current state with function return if not None.

    def sm_proc_input( self, input, **kwargs ):
        currentState = self.sm_state
        kwargs[ 'currentState' ] = currentState

        fcn = self.state_matrix[ input ][ self.sm_state ]
        if fcn:
            nextState = fcn( kwargs )
            if nextState:
                self.sm_state = nextState
                self.stateLabel.setText( f"{currentState.name}, {input.name} --> {fcn.__name__}() --> {nextState.name}" )
            else:
                self.stateLabel.setText( f"{currentState.name}, {input.name} --> {fcn.__name__}() --> {currentState.name}" )

    # =========================================================================
    #   State machine functions. Returns next state or None to stay in current state.
    # -------------------------------------------------------------------------
    #   Play tone at current frequency / gain.

    def sm_play( self, kwargs ):
        freq = self.current_freq
        gain_db = self.current_gain_db
        self.completed_lcd.display( f"{self.findex+1}/{len(self.test_freqs)}" )
        self.status.showMessage("Playing tone.")
        self.play_test_tones_alt( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")

        if self.stateStack:             # Returning from one of the SM_Click* states.
            t = self.stateStack
            self.stateStack = None
            return t
        return SM.S_Wait

    # ------------------------------------------------
    #   Play tone at frequency / gain selected by mouse click or current ck frequency / gain.

    def sm_ckplay( self, kwargs ):
        if not self.stateStack:         # Entering the SM_ClickWait state, save non-click state.
            self.stateStack = kwargs[ 'currentState' ]

        if kwargs:
            freq = kwargs[ 'freq' ]
            gain_db = kwargs[ 'gain_db' ]
            self.current_ck_freq = freq
            self.current_ck_gain_db = gain_db
        else:
            freq = self.current_ck_freq
            gain_db = self.current_ck_gain_db

        self.completed_lcd.display( "User" )
        self.status.showMessage("Playing tone.")
        self.play_test_tones_alt( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")
        return SM.S_ClickWait

    # ---------------------------------------------------------------------
    #   Play tone at current frequency / gain, don't change state.

    def sm_repeat( self, kwargs ):
        freq = self.current_freq
        gain_db = self.current_gain_db
        self.status.showMessage("Playing tone.")
        self.play_test_tones_alt( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")
        return None

    # ------------------------------------------------
    #   Play tone at current ck frequency / gain, don't change state.

    def sm_ckrepeat( self, kwargs ):
        freq = self.current_ck_freq
        gain_db = self.current_ck_gain_db
        self.status.showMessage("Playing tone.")
        self.play_test_tones_alt( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")
        return None

    # ---------------------------------------------------------------------
    #   Play tone at next frequency, starting gain, stop at last frequency

    def sm_play_next_freq( self, kwargs  ):

        self.findex += 1

        if self.findex == len( self.test_freqs ):
            self.done_label.show()
            self.status.showMessage("Test Complete.")
            return SM.S_Complete

        self.gindex = 0

        self.completed_lcd.display( f"{self.findex+1}/{len(self.test_freqs)}" )
        freq = self.test_freqs[ self.findex ]
        gain_db = self.test_gains_db[ self.gindex ]
        self.status.showMessage("Playing tone.")
        self.current_freq = freq
        self.current_gain_db = gain_db
        self.play_test_tones_alt( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")
        return SM.S_Wait

    # ---------------------------------------------------------------------
    #   Play tone at next gain, to next freq at last gain, stop at last frequency

    def sm_play_next_gain( self, kwargs  ):

        self.gindex += 1
        if self.gindex == len( self.test_gains_db ):
            self.gindex = 0
            self.findex += 1

            if self.findex == len( self.test_freqs ):
                self.done_label.show()
                self.status.showMessage("Test Complete.")
                return SM.S_Complete

        freq = self.test_freqs[ self.findex ]
        gain_db = self.test_gains_db[ self.gindex ]

        self.completed_lcd.display( f"{self.findex+1}/{len(self.test_freqs)}" )
        self.status.showMessage("Playing tone.")
        self.current_freq = freq
        self.current_gain_db = gain_db
        self.play_test_tones_alt( freq, gain_db )
        self.status.showMessage( "Waiting for Accept / Reject.")
        return SM.S_Wait

    # ---------------------------------------------------------------------
    #   User accepted tone

    def sm_accept( self, kwargs ):
        hearing_loss = self.current_gain_db - self.reference_level
        self.graph.add_point( self.current_freq, hearing_loss, '#0000ff' )
        self.results[ self.current_freq ][ hearing_loss ] = True
        self.status.showMessage("Accepted. Play next tone or click in graph.")
        return SM.S_Accepted

    # ------------------------------------------------
    #   User accepted tone from mouse click

    def sm_ckaccept( self, kwargs ):
        hearing_loss = self.current_ck_gain_db - self.reference_level
        self.graph.add_point( self.current_ck_freq, hearing_loss, '#0000ff' )
        self.results[ self.current_ck_freq ][ hearing_loss ] = True
        self.status.showMessage("Accepted. Play next tone or click in graph.")
        return SM.S_ClickAccepted

    # ---------------------------------------------------------------------
    #   User rejected tone

    def sm_reject( self, kwargs  ):
        hearing_loss = self.current_gain_db - self.reference_level
        self.graph.add_point( self.current_freq, hearing_loss, '#ff4040' )
        self.results[ self.current_freq ][ hearing_loss ] = False
        self.status.showMessage("Rejected. Play next tone or click in graph.")
        return SM.S_Rejected

    # ------------------------------------------------
    #   User rejected tone from mouse click

    def sm_ckreject( self, kwargs  ):
        hearing_loss = self.current_ck_gain_db - self.reference_level
        self.graph.add_point( self.current_ck_freq, hearing_loss, '#ff4040' )
        self.results[ self.current_ck_freq ][ hearing_loss ] = False
        self.status.showMessage("Rejected. Play next tone or click in graph.")
        return SM.S_ClickRejected

    # =========================================================================

    def play_test_tone( self ):
        test_freq = 1000
        test_gain_db = 0
        test_gain = 10 ** (test_gain_db/20)

        self.playing.setColor( '#00ff00' )
        self.freq_lcd.display( f"{int(test_freq )} Hz")
        self.gain_lcd.display( f"{int(test_gain_db )} dB")
        QApplication.processEvents()
        tone = self.gen_tone_alt( test_freq, .75, test_gain )     # play tone for .75 seconds           
        self.play_tone_alt( tone )    
        self.playing.setColor( '#c0c0c0' )

    # ------------------------------------------------------------------------------
    #   Alt functions generate the entire three tone/silence sequence before starting
    #   playback. When switched to sounddevice got buffer underruns when doing each separately.

    def play_test_tones_alt( self, freq, gain_db ):
        # self.freq_lcd.display( int(freq) )      # int() here OK. Needed to limit number of digits
        # self.gain_lcd.display( int(gain_db) )
        self.freq_lcd.display( f"{int(freq)} Hz")
        self.gain_lcd.display( f"{int(gain_db )} dB")
        self.playing.setColor( '#00ff00' )
        loss = gain_db - self.reference_level
        self.graph.set_marker( freq, loss, '#00c000' )
        QApplication.processEvents()            # To give lcd and label a chance to change.

        gain = 10 ** (gain_db/20)

        tones = []
        for j in range( 3 ):                            # repeat tone three times
            tone = self.gen_tone_alt( freq, self.dur, gain )     # make tone
            silence = self.gen_tone_alt( freq, self.dur, 0 )     # make silence
            tones = np.concatenate( [tones, tone, silence] )              # combine in one buffer

        self.play_tone_alt( tones )
        self.playing.setColor( '#808080' )

    # --------------------------------------------------------
    #   simpleaudio.play_buffer(audio_data, num_channels, bytes_per_sample, sample_rate)
    #   Works fine without tobytes() but chat says better to include it.

    def gen_tone_alt( self, freq, dur, gain, show=False ):
        audio = self.p.make_wave_from_freq_dur( freq, dur, show ) * gain  # freq in hz, dur in seconds.
        return audio

    # --------------------------------------------------------
    def play_tone_alt( self, audio ):
        self.fs = 44100

        if self.radio1.isChecked():         # Binaural
            sd.play( audio, self.fs )

        #   Left-only: [L, R, L, R, ...] = [tone, 0, tone, 0, ...]
        elif self.radio2.isChecked():               
            right = np.zeros_like(audio)
            audio = np.column_stack((audio, right)).astype(np.float32)
            sd.play( audio, self.fs )

        #   Right-only: [L, R, L, R, ...] = [0, tone, 0, tone, ...]
        elif self.radio3.isChecked():                
            left = np.zeros_like(audio)
            audio = np.column_stack((left, audio)).astype(np.float32)
            sd.play( audio, self.fs )

        sd.wait()

    # ------------------------------------------------------------------------------

    def OMIT_play_test_tones( self, freq, gain_db ):
        self.current_freq = freq
        self.current_gain_db = gain_db

        self.gain_lcd.display( int(gain_db) )
        self.freq_lcd.display( int(freq) )
        self.playing.setColor( '#00ff00' )

        QApplication.processEvents()            # To give lcd and label a chance to change.

        gain = 10 ** (gain_db/20)

        for j in range( 3 ):                            # repeat tone three times
            self.play_tone( freq, self.dur, gain, False )    # play tone
            self.play_tone( freq, self.dur, 0, False )       # play silence

        self.playing.setColor( '#808080' )

    # --------------------------------------------------------
    #   simpleaudio.play_buffer(audio_data, num_channels, bytes_per_sample, sample_rate)
    #   Works fine without tobytes() but chat says better to include it.

    def OMIT_play_tone( self, freq, dur, gain, show ):
        self.fs = 44100

        fs = 44100  # 44100 samples per second
    
        audio = self.p.make_wave_from_freq_dur( freq, dur, show ) * gain  # freq in hz, dur in seconds.
        # print( len( audio), np.min( audio ), np.max( audio ))
    
        if self.radio1.isChecked():         # Binaural
            sd.play( audio, self.fs )

        #   Left-only: [L, R, L, R, ...] = [tone, 0, tone, 0, ...]
        elif self.radio2.isChecked():               
            right = np.zeros_like(audio)
            audio = np.column_stack((audio, right)).astype(np.float32)
            sd.play( audio, self.fs )

        #   Right-only: [L, R, L, R, ...] = [0, tone, 0, tone, ...]
        elif self.radio3.isChecked():                
            left = np.zeros_like(audio)
            audio = np.column_stack((left, audio)).astype(np.float32)
            sd.play( audio, self.fs )

        sd.wait()

    # ------------------------------------------------------------------------------
    #   Override closeEvent() to prompt user to save results, if any.

    def closeEvent(self, event):
        if self.results and not self.saved_flag:

            reply = QMessageBox.question(
                self,
                self.windowTitle,
                "You have test results that have not been saved.\nAre you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # default
            )

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

        settings = QSettings( str( Path( Const.stdConfig, Const.Settings_Config_File )), QSettings.IniFormat )
        settings.setValue("points_per_octave", self.points_per_octave )
        settings.setValue("start_freq", self.start_freq )
        settings.setValue("end_freq", self.end_freq )
        settings.setValue("geometry", self.saveGeometry())

    # --------------------------------------------------------
    #   Give graph focus after user hit return

    Slot()
    def return_pressed(self):
        self.graph.setFocus()

    # ------------------------------------------------------------------------------
    #   Sort by ascending frequency, user may test frequencies out of order, test frequencies certainly are.
    #   WRW 16-June-2025 - select the least loss that has been accepted, i.e. value of True.
    #   self.results[ freq ][ loss ] is True or False
    #   audiogram: [ (freq, gain_db), (freq, gain_db) ]

    @Slot()
    def do_save( self ):
        if not self.results:
            QMessageBox.information( self, self.windowTitle, "No results to save" )
            return     

        audiogram = []
        freqs = sorted(round(freq) for freq in self.results.keys())
        for freq in freqs:
            losses = sorted( self.results[ freq ].keys() )      # Sort inner dict
            for loss in losses:
                if self.results[ freq ][ loss ]:
                    audiogram.append( ( freq, loss ))           # Only show accepted points
                    break
            # else:                                             # Don't show any rejected points, even the last
            #     audiogram.append( ( freq, loss ))

        # --------------------------------------------------------------------

        user = self.user_text_box.text()
        if not user:
            user = 'User'

        if self.radio1.isChecked():
            mode = "Both ears"
            smode = "B"
        elif self.radio2.isChecked():
            mode = "Left ear"
            smode = "L"
        elif self.radio3.isChecked():                
            mode = "Right ear"
            smode = "R"

        now = datetime.datetime.now()
        title_timestamp = now.strftime('%a, %d-%b-%Y, %H:%M:%S')
        title = f"{self.windowTitle}- Audiogram for: {user}, {mode}, {title_timestamp}"

        file_timestamp = now.strftime('%d-%b-%Y_%H-%M-%S')
        ofile = f"Audiogram-{user}-{smode}-{file_timestamp}.png"

        # Show folder picker dialog
        path = QFileDialog.getExistingDirectory( self, "Select Output Folder")
    
        if path:
            fpath = os.path.join( path, ofile)
        else:
            QMessageBox.information( self, "Cancelled", "No folder selected.")
            return

        ok = self.do_plot( audiogram, title, fpath )
        if ok:
            msg = f"Test results saved in:\n{fpath}"
            QMessageBox.information( self, self.windowTitle, msg )
            self.saved_flag = True

    # --------------------------------------------------------

    def do_plot( self, data: list[tuple[int, int]], title, ofile ):
        # Unpack
        freqs, gains = zip(*data)
    
        # Create figure
        dpi = 72
        width_px, height_px = 800, 600
        fig = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
        ax = fig.add_subplot(1, 1, 1)

        ax.set_title( title )

        # Plot
        ax.plot(freqs, gains, marker='o', linestyle='-', color='blue')
    
        # Axes labels
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Hearing Loss (dB) (hearing aid required gain)")
    
        # Y-axis: 0,80 (0 at top, 80 at bottom)
        ax.set_ylim(self.loss_db_max, self.loss_db_min )
        ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
    
        # X-axis: 20 - 20000, log scale, 1:2:5 ticks per decade
        ax.set_xscale("log")
        ax.set_xlim( self.start_freq, self.end_freq )
    
        def log_tick_positions(start=1, end=100000):
            """Returns 1-2-5 tick pattern across decades"""
            ticks = []
            base_ticks = [1, 2, 5]
            decade = 1
            while True:
                new_ticks = [t * decade for t in base_ticks]
                ticks.extend(new_ticks)
                if max(new_ticks) >= end:
                    break
                decade *= 10
            return [t for t in ticks if start <= t <= end]
    
        ax.set_xticks(log_tick_positions( self.start_freq, self.end_freq ))
        ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
    
        # Grid
        ax.grid(True, which='both', linestyle='--', alpha=0.4)
    
        # Dynamic filename
        fig.tight_layout()
        fig.savefig(ofile)
        plt.close(fig)

        return True
    
    # --------------------------------------------------------------
    #   WRW 17-June-2025 - Need a little feedback for user to indicate expected input

    #   Show a message in the status bar. Timeout in milliseconds. 0 = stay until cleared.
    def set_status( self, msg: str, timeout: int = 0):
        self.status.showMessage(msg, timeout)
    
    #   Clear the status bar
    def clear_status( self ):
        self.status.clearMessage( )

    # --------------------------------------------------------------

    def setup_menus(self):
        menu_bar = self.menuBar()
    
        # File menu
        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(quit_action)
    
        # Parameters menu
        param_menu = menu_bar.addMenu("Parameters")

        param_action = QAction("Edit", self)
        param_action.triggered.connect(self.edit_parameters)
        param_menu.addAction(param_action)

        self.show_points_action = QAction("View", self)
        self.show_points_action.triggered.connect(self.show_parameters)
        param_menu.addAction(self.show_points_action)

        self.set_default_action = QAction("Set Default", self)
        self.set_default_action.triggered.connect(self.set_default_parameters )
        param_menu.addAction(self.set_default_action)
    
        # Help menu
        help_menu = menu_bar.addMenu("Help")

        quick_action = QAction("Quick-Start Guide", self)
        quick_action.triggered.connect(self.show_quickstart)
        help_menu.addAction(quick_action)

        contact_action = QAction("Contact", self)
        contact_action.triggered.connect( self.do_contact)
        help_menu.addAction(contact_action)

        website_action = QAction("What? Website", self)
        website_action.triggered.connect( self.show_website )
        help_menu.addAction(website_action)

        license_action = QAction("License", self)
        license_action.triggered.connect( self.show_license )
        help_menu.addAction(license_action)

        about_action = QAction("About What?", self)
        about_action.triggered.connect(self.show_about )
        help_menu.addAction(about_action)
    
        about_qt_action = QAction("About Qt", self)
        about_qt_action.triggered.connect(QApplication.instance().aboutQt)
        help_menu.addAction(about_qt_action)
    
    # -----------------------------------------------------------------

    def do_contact( self ):
        txt = """To contact me please go to:<br>
        https://what.wrwetzel.com/contact.html<br>    
        """
        txt = re.sub( r'\s+', ' ', txt )    # Remove newlines and extra space.
        txt = txt.replace( "<br>", "\n\n" ) # Add newlines back in where intended.

        QMessageBox.information( self, "Contact What?", txt )

    # -----------------------------------------------------------------

    def edit_parameters(self):
        dialog = ParameterDialog( self.points_per_octave, self.start_freq, self.end_freq, self )
        if dialog.exec():
            points_per_octave, start_freq, end_freq = dialog.values()
            self.set_parameters( points_per_octave, start_freq, end_freq )

    # -----------------------------------------------------------------
    
    def show_parameters( self ):
        dialog = QDialog(self)
        dialog.setWindowTitle("Test Parameters")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
    
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()

        layout.addWidget(browser)
        layout.addWidget(buttons)
    
        freqs = ', '.join( [ f"{x:.0f}" for x in sorted(self.test_freqs) ])
        gains = ', '.join( [ f"{x:.0f}" for x in sorted(self.test_gains_db) ])

        html = f"""
        <h3>Test Parameters</h3>
        <h5>Primary</h5>
        <ul>
            <li><b>Frequency Range:</b> {self.start_freq} Hz to {self.end_freq} Hz</li>
            <li><b>Points / octave:</b> {self.points_per_octave}</li>
        </ul>

        <h5>Derived</h5>
        <ul>
            <li><b>Points</b> {self.points_total+1}</li>
            <li><b>Octaves</b> {self.octaves:.2f}</li>
        </ul>

        <h3>Frequencies</h3>
        {freqs}
        <h3>Gains</h3>
        {gains}

        """
        browser.setHtml(html)
        dialog.resize(640, 480)
        dialog.exec()

    # ---------------------------------------------------------------------------------

    def show_website(self):
        QMessageBox.information(self, "What? Website", "https://what.wrwetzel.com" )

    # --------------------------------------------------------------------------

    def show_license( self ):
    
        file = QFile( Const.License )
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            txt = stream.readAll()
            file.close()
        else:
            txt = f"ERROR-DEV: Can't find license file: '{Const.License}'"
    
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("License")
        msg.setTextFormat(Qt.RichText)
        msg.setText( txt )
        msg.exec()

    # ---------------------------------------------------------------------------------

    def show_about(self):
        txt = f"""                                                                                 
            <p>
            What? is an interactive, tone-based hearing test that
            measures hearing thresholds across a range of frequencies.  Users respond to
            tones using keyboard interaction and results are visualized on a graph and
            optionally saved as an audiogram.
            </p>

            <p>
            What? is written in Python and the user interface is built with the PySide6 GUI toolkit.
            </p>

            <p>
            Version: {what_version.__version__} Build {what_version.__build__}
            </p>

            <p>
            {Const.Copyright}
            </p>

        """

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About What?")
        msg.setTextFormat(Qt.RichText)
        msg.setText( txt )
        msg.exec()

    # ---------------------------------------------------------------------------------

    def show_dialog(self, title, html_text):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(640, 480)

        layout = QVBoxLayout(dialog)

        browser = QTextBrowser()
        browser.setHtml(html_text)
        browser.setOpenExternalLinks(True)  # Optional: enable hyperlinks
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec()

    # ---------------------------------------------------------------------------------

    def show_quickstart(self):
        txt = """
            <body style="margin: 10px;" >

            <h3>What? Quick Start</h3>
            <ul>
            <li>Go to a quiet room and put on a pair of headphones.</li>
            <li>Launch What?</li>
            <li>Press Space.</li>
            <li>Press Right-Arrow if you heard a tone, Left-Arrow if not.</li>
            <li>Repeat prior two steps until <i>All done</i> notice appears.
            <li>Press <i>Save</i> to copy the audiogram to a file.
            </ul>

            <h3>Overview</h3>

            <p>
            What? (Bill's Hearing Test) is a graphical, interactive hearing test. It plays
            a series of tones at random frequencies and increasing volume or as indicated by
            a click on the graph. Reject the tone to go on to the next higher volume
            or accept the tone to go on to the next frequency.
            </p>

            <p>
            Test results are relative, not absolute, because the chain of audio from your
            computer to your headphones to your ears is not calibrated.  They can be used
            to compare hearing between ears and monitor changes over time but not to set
            absolute gain on a hearing device.
            </p>

            <p>
            The gain (amplitude) of tones is shown in dB with 0 dB the maximum volume.
            </p>

            <p>
            The Y-axis of the graph is <i>hearing loss</i> in dB, that is, the gain required 
            for a hearing aid to bring a tone at the indicated frequency to a normal level.
            </p>


            <h3>Display</h3>
            <ul>
            <li><b>Playing</b> Green while a tone is playing</li>
            <li><b>Gain</b> Gain of the current tone in dB. </li>
            <li><b>Pitch</b> The frequency (or pitch) of the current tone in Hz.</li>
            <li><b>Step</b> Shows the progres through the series test frequencies. The position
                in the series is not affected by clicking in the graph.
            </ul>

            <h3>Keyboard</h3>

            <ul>
            <li><b>Space / Down-Arrow</b> <i>Play</i> the next tone of the test sequence.     
            Repeat the current tone on successive presses until the tone is accepted or rejected.</li>

            <li><b>Up-Arrow</b> Repeat the current tone.</li>

            <li><b>Left-Arrow</b> Reject the current tone. Increase the gain on the next <i>Play</i>,
            advance to the next frequency when maximum gain reached. Rejected tones are marked with a red dot.</li>

            <li><b>Right-Arrow</b> Accept the current tone. Advance to the next frequency at the lowest
            gain on the next <i>Play</i>. Accepted tones are marked with a blue dot
            and are saved for the audiogram. </li>
            </ul>

            <p>
            You can change your mind between accept or reject any time before playing the next tone in the sequence
            and you can repeat a tone any time before accept or reject.
            </p>

            <h3>Mouse</h3>
            <ul>
            <li><b>Click</b> in the graph to <i>Play</i> a tone at the indicated frequency and gain.
                Accept or reject the tone or continue in the test sequence using the keyboard as above.
                Use this to make adjustments in test-tone gains near the threshold of hearing for finer
                resolution than 10 dB as used in the test-tone sequence.
            </li>
            </ul>

            <h3>Controls</h3>
            <ul>
                <li><b>Name</b> - Include <i>Name</i> in the title and filename of the audiogram.
                <li><b>Binaural, Left, Right</b> - Select the output channel for the test.</li>
                <li><b>Test Tone</b> - Play a brief 1000 Hz tone at 0 dB.</li>
                <li><b>Save</b> - Save the audiogram shown in the graph to an image file.</li>
                <li><b>Reset</b> - Clear the graph and reset the test-tone sequence to the beginning.</li>
                <li><b>Exit</b> - Exit What?</li>
            </ul>

            <h3>Menus</h3>

            <ul>
                <li><b>File->Quit</b> Exit What?.
            </ul>
            <ul>
                <li><b>Parameters->Edit</b> Change the test parameters: start and end
                        frequencies and number of points per octave.
                        Changes to test parameters are saved between launches.</li>
                <li><b>Parameters->Show</b> Show the test parameters, frequencies, and gains
                        of the test points.</li>
                <li><b>Parameters->Default</b> Set the test parameters: 20 -> 20,000 Hz and
                        3 points/octave.</li>
            </ul>
            <ul>
                <li><b>Help</b> - Self evident.</li>
            </ul>
            </body>

        """

        self.show_dialog( "Quick-Start Guide", txt )

# ------------------------------------------------------------------------------
StyleSheet = """

X-QWidget {
     font-size: 9;
     color: #ffffff;
     background-color: #16212d;
}

X-QPushButton {
     color: #ffffff;
     background-color: #008000;
}

X-QLineEdit {
     color: #000000;
     background-color: #ffffff;
}

QPushButton {
    padding: 8px 10px;
}

QGroupBox {
    padding: -1px;
    color: #000000;
    background-color: #ffffff;
}

"""
# ------------------------------------------------------------------------------

def do_main():

    # ------------------------------------------------------------------
    #   Build the user interface.

    app = QApplication(sys.argv)

    window = MainWindow( )
    window.setStyleSheet( StyleSheet )

    settings = QSettings( str( Path( Const.stdConfig, Const.Settings_Config_File )), QSettings.IniFormat )
    geometry = settings.value( "geometry")

    if geometry is not None:
        window.restoreGeometry(geometry)
    else:
        size = QApplication.primaryScreen().size()
        width = size.width()
        height = size.height()
        width = min( 1800, width )              # /// Don't want it too big on my desktop
        height = width/1.61                     # Golden rectangle ratio
        window.resize( width*.8, height*.8 )

    window.show()
    sys.exit(app.exec())

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    do_main()

# ------------------------------------------------------------------------------
