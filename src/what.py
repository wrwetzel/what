#!/usr/bin/env python3
# -------------------------------------------------------------------------------------
#   WRW 10-June-2025
#   Graphical display for a hearing test.
#   Bill Wetzel

# -------------------------------------------------------------------------------------
#   /// RESUME

#   Break up into smaller files?

# -------------------------------------------------------------------------------------

#   WRW 12-June-2025 - Conversation with Damian at Miracle Ear.
#   He tested me starting at 250 Hz.
#   250 -> 2000 was ok, moderate loss. After 2000 moderate to severe loss.
#   10 dB at 1000 in left, 15 dB at 1000 in right.

#   The audiogram shows hearing loss on the Y-axis, i.e. the gain required to bring the tone
#   up to normal hearing, 0 dB reference level.

#   The numeric display and internal gain_db variable is gain as an engineer would see it, 0 for
#   loud, -80 for quiet.  Quite a headache going between the two, hearing loss for display, 
#   gain_db for all else. Numeric display is referred to as 'lcd' because it started with
#   QLCDNumber but discarded it when tried wanted better control of number sizes.

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
#   Test points examples but not as implemented. Settled on octaves after exploring both.

#   20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240, 20480
#        10 octaves,
#        48 points at 4 points/octave
#        30 points at 3 points/octave

#   20, 200, 2000, 20000
#         3 decades,
#         48 points at 16 points/decade
#         30 points at 10 points/decade

# -------------------------------------------------------------------------------------
#   Generate resource file:
#       pyside6-rcc what_resources.qrc -o what_resources_rc.py

# =======================================================================================
#   The imports here up to do_splash_screen() are the minimum required for splash screen.
#   Exclude all others to get splash screen up as quickly as possible. It may be possible
#   to do another type of splash earlier from bundled package but I have not explored it. 
#   Fast enough as is.

import os
import sys

#   Trying to eliminate error message:
#       qt.core.qobject.connect: QObject::connect: No such signal Solid::Backends::Fstab::FstabStorageAccess::checkRequested(QString)
#       qt.core.qobject.connect: QObject::connect: No such signal Solid::Backends::Fstab::FstabStorageAccess::checkDone(Solid::ErrorType, QVariant, QString)
#   from QFileDialog. Chat thinks it may be related to KDE integration. Following worked.

# os.environ["QT_QPA_PLATFORMTHEME"] = 'gtk3'    # "gtk3"  # or unset completely

from PySide6 import QtCore
from PySide6.QtCore import Qt, QStandardPaths, QCoreApplication
from PySide6.QtGui import QFont, QPixmap, QPainter, QFontMetrics, QColor
from PySide6.QtWidgets import QApplication, QSplashScreen, QDialog, QLabel, QVBoxLayout

from Store import Store

#   Need this even though not directly referenced. DON'T Comment Out!
#   Must be imported at least once. Has side effects when imported,
#   calls qRegisterResourceData().

import what_resources_rc
import what_version

# -----------------------------------------------------------
#   Consolidate most constants here in one spot. This has to
#   be above instantiation in do_dialog_splash()

class Const():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        Frozen = True
        Package_Type = 'PyInstaller'                                                    

    else:
        Frozen = False
        Package_Type = 'Development'

    # ---------------------------------------------

    if sys.platform.startswith("win"):
        Platform = 'Windows'
    elif sys.platform.startswith("darwin"):
        Platform = 'macOS'                          # This is an internal designation used only within birdland.
    elif sys.platform.startswith("linux"):
        Platform = 'Linux'
    else:
        Platform = 'Unknown'

    # ---------------------------------------------

    What_Program_Name = "What"      # desktop filename comes from this
    What_Short_Title = 'What?'
    What_Full_Title = "What? (Bill's Hearing Test)"
    What_Desktop =      f"{What_Program_Name}.desktop"

    QCoreApplication.setApplicationName( What_Program_Name )      # Must do this early as used in QStandardPaths below
    stdApplication = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
    stdConfig = QStandardPaths.standardLocations(QStandardPaths.AppConfigLocation)[0]
    Confdir = stdConfig

    Quick_Start = ":quick-start.html"
    What_Splash_Image = ':Images/ear-horn-640.png'
    License = ':License.txt'

    What_Icon_ICO = ":/Images/ear-64.ico"
    What_Icon_PNG = ":/Images/ear-64.png"

    Icon_File_ICO = 'ear-64.ico'
    Icon_File_PNG = 'ear-64.png'

    pointDiameter = 4
    markerDiameter = 30
    markerPen = 2
    graphBG = '#e0e0ff'             # for dark: graphBG = '#26313d'

    Settings_Config_File = 'what.settings.conf'
    Copyright = f"Copyright \xa9 2025 Bill Wetzel"
    plot_width_in = 10
    plot_height_in = 7.5
    Version = f"{what_version.__version__} Build {what_version.__build__}"

    test_gain_points_per_db = 1
    test_points_per_octave = 4
    start_freq = 125
    end_freq = 16000

    graphPointsPerOctave = 5
    graphPointsPer10dB  = 5

    loss_db_min = 0
    loss_db_max = 80
    gain_db_min = -80
    gain_db_max = 0
    reference_level = -80      # For hearing-loss conversion

    def set( self, name, value ):
        setattr( self, name, value )

# -----------------------------------------------------------

#   Splash screen window setup:
#       Qt.Tool: floating window that stays above the main window but doesn't appear in taskbar or Alt+Tab
#       Qt.FramelessWindowHint: removes native window borders and title bar
#       Qt.WA_TranslucentBackground: allows transparent background (if the splash image has alpha)
#       Qt.ApplicationModal: blocks interaction with other windows until splash is dismissed (optional)

class SplashDialog( QDialog):
    def __init__(self, pixmap: QPixmap):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint)
      # self.setWindowModality(Qt.ApplicationModal)
      # self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Splash")

        self.label = QLabel()
        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget( self.label )
        self.setLayout(layout)
        self.setFixedSize( pixmap.size() )

    def getLabel( self ):
        return self.label

# ------------------------------------------------------------------------------

class makeSplashPixmap( QPixmap ):

    def __init__( self, pixmap: QPixmap, title: str, version: str ) -> QPixmap:
        s = Store()                 
        super().__init__( pixmap )

        if pixmap.isNull():
            print( "ERROR-DEV: pixmap is null at makeSplashPixmap()" )
            sys.exit(1)

        self.pixmap = pixmap
        self.size = pixmap.size()             # Returns QSize
        self.width = pixmap.width()           # Returns int
        self.height = pixmap.height()
    
        painter = QPainter( self.pixmap )
        # painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("black"))
    
        xpos = 40            # from left
        ypos = self.height - 60   # From top
    
        self.progress_x = 40
        self.progress_y = 40

        # title_font = QFont("Sans Serif", 18, QFont.Bold)
        title_font = QFont("Arial", 18, QFont.Bold)             # WRW 3-May-2025 - Port to MacOS
        title_metrics = QFontMetrics(title_font)
        title_height = title_metrics.height()
    
        # version_font = QFont("Sans Serif", 12, QFont.Bold)
        version_font = QFont("Arial", 12, QFont.Bold)           # WRW 3-May-2025 - Port to MacOS
        version_metrics = QFontMetrics(version_font)
        version_height = version_metrics.height()
    
        painter.setFont( title_font )
        painter.drawText( xpos, ypos, title)
        ypos += version_height
    
        painter.setFont( version_font )
        painter.drawText( xpos, ypos, version)
        painter.end()

    # -------------------------------------------------------

    def setLabel( self, label ):
        self.label = label

    # -------------------------------------------------------

    def progress( self, txt ):
        s = Store()
        painter = QPainter( self.pixmap )
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("black"))

        # font = QFont("Sans Serif", 10 )
        font = QFont("Arial", 10 )
        height = QFontMetrics(font).height()
        painter.setFont( font )
        painter.drawText( self.progress_x, self.progress_y, txt)
        painter.end()
        self.label.setPixmap( self.pixmap )     # Update label after every draw.
        self.label.repaint()
        QApplication.processEvents()            # WRW 23-June-2025 - added to get prog messages on macOS.

        self.progress_y += height

# ------------------------------------------------------------------------------
#   Do some preliminary initialization and show splash screen.
#   s.Const and s.app defined here

def do_dialog_splash( ):
    s = Store()
    s.Const = Const()                   # Constants, short var name since used a bit.

    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)    
    s.app = QApplication(sys.argv)
    s.originalStyle = s.app.style().objectName()

    s.splash_pix = makeSplashPixmap( QPixmap(s.Const.What_Splash_Image), s.Const.What_Short_Title, s.Const.Version )

    if s.splash_pix.isNull():
        print("ERROR-DEV: Splash image not found or invalid:", s.Const.What_Splash_Image)
        sys.exit(1)

    s.splash = SplashDialog( s.splash_pix.pixmap )
    splash_label = s.splash.getLabel()
    s.splash_pix.setLabel( splash_label )
    s.splash.show()
    s.app.processEvents()       # Force paint before continuing

# ------------------------------------------------------------------------------------
#   Show the splash screen before any further includes and initialization.

do_dialog_splash( )

def do_splash_progress( txt ):      # So don't have to have s as a global.
    s = Store()
    s.splash_pix.progress( txt )

# =======================================================================================
#   Remainder of imports after splash screen. Added progress reports to diagnose
#   delay on macOS, might as well keep. Delay was from importing matplotlib, now deferred
#   until needed for plotting.

do_splash_progress( "Importing numpy" )
import numpy as np

do_splash_progress( "Importing remaining system modules" )
import random
import re
import math
import datetime
import sounddevice as sd
from collections import defaultdict
from collections import OrderedDict
from enum import IntEnum
from pathlib import Path
import traceback
import platform
import ctypes

do_splash_progress( "Importing QtCore" )
from PySide6.QtCore import QSize, Signal, Slot, QRect, QFile, QTextStream, QSettings
from PySide6.QtCore import QStandardPaths, QTimer

do_splash_progress( "Importing QtGui" )
from PySide6.QtGui import QPen, QFontDatabase, QKeyEvent, QAction, QCursor, QIcon, QGuiApplication

do_splash_progress( "Importing QtWidgets" )
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from PySide6.QtWidgets import QSizePolicy, QPushButton, QRadioButton, QGroupBox, QLineEdit
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtWidgets import QMenuBar, QMenu, QFormLayout, QDialogButtonBox
from PySide6.QtWidgets import QTextBrowser, QTextEdit 

from Player import Player
from Scope import ScopeDialog
from make_desktop import make_desktop

do_splash_progress( "Imports done" )

# -------------------------------------------------------------------------------------
#   Some constants for state machine: States and Inputs.
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
    I_Back = 5

# -------------------------------------------------------------------------------------
#   WRW 22-June-2025 - from chat

def get_monospace_font():
    preferred = ["Menlo", "Consolas", "Courier New", "Courier", "Monospace"]
    available = QFontDatabase.families()  # Static call now
    for name in preferred:
        if name in available:
            return name
    # Fallback
    fallback = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
    return fallback
    
# -------------------------------------------------------------------------------------
#   _type: list, dict, int, more?

def nested_dict(n, _type):
    if n == 1:
        return defaultdict(_type)
    else:
        return defaultdict(lambda: nested_dict(n-1, _type))

# -------------------------------------------------------------------------------------
#   Should only be called once but make a singleton.
#   Taken from fb_config.py, greatly reduced.

class Config():
    _instance = None

    def __new__( cls ):
        if cls._instance is None:
            cls._instance = super().__new__( cls )
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self ):
        if hasattr( self, '_initialized' ):     # Chat prefers this over a flag initialized in __new__().
            return                              # No point initializing a singleton twice.
        self._initialized = True

        s = Store()
        self.confdir = s.Const.Confdir

    # ------------------------------------------

    def check_config_directory( self ):
        success = True

        if not Path( self.confdir ).is_dir():
            success = False

        return success

    # --------------------------------------------------------------------------
    #   WRW 20-May-2025 - Rewriting first-start checks and inits to clean up worts.
    #   Config directory does not exist. Make and populate it.

    def initialize_config_directory( self ):
        s = Store()
        path = Path( self.confdir )

        if path.is_file():

            txt = f"""ERROR: A file with the same name as the configuration directory {self.confdir} already exists.<br>
                             Click OK to exit."""
            QMessageBox.critical( None, "Critical error", txt )
            sys.exit(1)

        path.mkdir()
        self.initialize_config_directory_content( )

    # --------------------------------------------------------------------------

    def initialize_config_directory_content( self ):
        s = Store()

        # ----------------------------------------------------------
        #   *** Copy icon file.

        src =  s.Const.What_Icon_ICO
        dest = Path( self.confdir, s.Const.Icon_File_ICO )
        self.copy_qrc_file( src, dest )

        src =  s.Const.What_Icon_PNG
        dest = Path( self.confdir, s.Const.Icon_File_PNG )
        self.copy_qrc_file( src, dest )

    # --------------------------------------------------------------------------

    def copy_qrc_file( self, qrc_path, output_path):

        file = QFile(qrc_path)
        if not file.open(QFile.ReadOnly):
            print( f"ERROR-DEV Open {qrc_path} failed")
            sys.exit(1)
    
        with open(output_path, "wb") as out:
            out.write(file.readAll().data())  # readAll() returns QByteArray
    
        file.close()

# -------------------------------------------------------------------------------------

class ParameterDialog( QDialog ):
    def __init__(self, gain_points_per_10dB, points_per_octave, start_freq, end_freq, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Parameters")
        layout = QFormLayout(self)

        self.gain_points_edit = QLineEdit( str( gain_points_per_10dB ))
        self.start_freq_edit = QLineEdit( str( start_freq ))
        self.end_freq_edit = QLineEdit( str( end_freq ))
        self.points_per_octave_edit = QLineEdit( str(points_per_octave) )

        layout.addRow("Gain Points per 10dB:", self.gain_points_edit )
        layout.addRow("Start Frequency:", self.start_freq_edit)
        layout.addRow("End Frequency:", self.end_freq_edit)
        layout.addRow("FrequencyPoints per Octave:", self.points_per_octave_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            int(self.gain_points_edit.text()),
            int(self.points_per_octave_edit.text()),
            int(self.start_freq_edit.text()),
            int(self.end_freq_edit.text())
        )

# -------------------------------------------------------------------------------------

class ColorIndicator( QLabel ):
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
        s = Store()
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setDigitCount(digit_count)

        preferredFont = get_monospace_font()    # Returns a QFont

        font = QFont( preferredFont, 20, QFont.Bold)  # monospaced + large
        font.setStyleHint(QFont.Monospace)      # Just precaution
        font.setFixedPitch(True)                # Just precaution

        self.setFont(font)

        if s.Const.Platform == 'macOS':
            self.setStyleSheet("background-color: black; color: lime; padding: 0px 2px;")
        else:
            self.setStyleSheet("background-color: black; color: lime; padding: -3px 2px;")

        self.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )

    def setDigitCount( self, n):
        self.digit_count = n
        self.setText("0".rjust(n))

    def display(self, value):
        self.setText(str(value).rjust(self.digit_count))

# -------------------------------------------------------------------------------------
#   GraphWidget - The graph showing the audiogram
#   Coordinates: 0, 0 is upper left.

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

    def add_point( self, x, y, accept ):
        self.points.append((x, y, accept ))
        self.update()

    def remove_point( self, xr, yr ):
        self.points = [ (x, y, z ) for x, y, z in self.points if x != xr or y != yr ]
        self.update()

    def get_accepted_points( self ):
        return [ (x, y) for x, y, z in self.points if z ]

    def clear_points( self ):
        self.points = []
        self.update()

    def set_marker( self, x, y, color ):
        self.marker = (x, y, color )
        self.update()

    def clear_marker( self ):
        self.marker = None
        self.update()

    def octave_grid_lines( self, start=125, stop=16000, divisions_per_octave=5 ):
        n_start = np.log2(start)
        n_stop = np.log2(stop)
        steps = np.arange(n_start, n_stop + 1e-6, 1 / divisions_per_octave)
        return 2 ** steps

    def loss_grid_lines( self, start=0, stop=80, divisions_per_10dB = 1):
        steps = np.arange(start, stop + 1e-6, 10 /  divisions_per_10dB )
        return steps.astype( int )

    def paintEvent(self, event):
        s = Store()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()

        self.graph_width = width - 2 * self.margin_x
        graph_height = height - 2 * self.margin_y

        # --------------------------------------------------
        # Draw background

        painter.fillRect(self.rect(), QColor(s.Const.graphBG))

        # --------------------------------------------------
        # Set pen for grid lines

        sub_grid_pen = QPen(QColor( '#909090' ), 1, Qt.DotLine)
        grid_pen = QPen(QColor( '#707070' ), 1, Qt.DashLine)

        # --------------------------------------------------
        # Horizontal grid lines and labels for Y axis

        self.major_losses = self.loss_grid_lines( s.Const.loss_db_min, s.Const.loss_db_max, 1 )
        self.minor_losses = self.loss_grid_lines( s.Const.loss_db_min, s.Const.loss_db_max, 5 )
        self.minor_losses = np.setdiff1d( self.minor_losses, self.major_losses) # Remove major from minor

        for loss in self.major_losses:
            y_px = self.margin_y + ( loss - s.Const.loss_db_min) / (s.Const.loss_db_max - s.Const.loss_db_min) * graph_height
            painter.setPen(grid_pen)
            painter.drawLine(self.margin_x, y_px, width - self.margin_x, y_px)

            painter.setPen(Qt.black)
            painter.drawText( 15, y_px +2 , f"{loss:.0f}")      # +2 to center text relative to line

        # ---------------------------------------------------------------
        #   WRW 24-June-2025 - Add lighter intermediate grid lines

        painter.setPen(sub_grid_pen)

        for loss in self.minor_losses:
            y_px = self.margin_y + ( loss - s.Const.loss_db_min) / (s.Const.loss_db_max - s.Const.loss_db_min) * graph_height
            painter.drawLine(self.margin_x, y_px, width - self.margin_x, y_px)

        # ---------------------------------------------------------------
        #   Generate the frequencies for the graph, not the test frequencies.

        self.major_freqs = self.octave_grid_lines( self.start_freq, self.end_freq, 1 )
        self.minor_freqs = self.octave_grid_lines( self.start_freq, self.end_freq, s.Const.graphPointsPerOctave )
        self.minor_freqs = np.setdiff1d( self.minor_freqs, self.major_freqs)    # Remove major from minor

        # ---------------------------------------------------------------
        #   WRW 24-June-2025 - Draw lighter intermediate grid lines first
        #       Major lines will overlay.

        painter.setPen(sub_grid_pen)

        for freq in self.minor_freqs:
            x_pixel = self.map_freq(freq, self.graph_width)
            painter.drawLine(x_pixel, self.margin_y, x_pixel, height - self.margin_y)

        # --------------------------------------------------
        #   Draw vertical grid lines and label the X axis

        for freq in self.major_freqs:
            painter.setPen(grid_pen)

            x_pixel = self.map_freq(freq, self.graph_width)
            painter.drawLine(x_pixel, self.margin_y, x_pixel, height - self.margin_y)

            painter.setPen(Qt.black)

            txt = f"{int(freq):,}"
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(txt)

            painter.drawText( x_pixel - text_width//2, height-self.margin_y+20, txt )   # // integer div to avoid blurry text on some platforms

        # --------------------------------------------------
        # Draw axes - The solid boundary lines on X and Y axex.

        axis_pen = QPen(Qt.black, 2)
        painter.setPen(axis_pen)
        painter.drawLine(self.margin_x, self.margin_y, self.margin_x, height - self.margin_y)  # Y axis
        painter.drawLine(self.margin_x, height - self.margin_y, width - self.margin_x, height - self.margin_y)  # X axis

        # --------------------------------------------------
        # Draw points

        for x_val, y_val, accept in self.points:
            dia = s.Const.pointDiameter
            if accept:
                color = '#0000ff'
            else:
                color = '#ff0000'

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
            dia = s.Const.markerDiameter
            pen = QPen( QColor(color), s.Const.markerPen )
            painter.setPen( pen )
            painter.setBrush(Qt.transparent )
            x_px = self.map_freq(x_val, self.graph_width)
            y_px = self.margin_y + (y_val - self.loss_db_min) / (self.loss_db_max - self.loss_db_min) * graph_height
            rect = QRect( x_px-dia/2, y_px-dia/2, dia, dia)
            painter.drawEllipse(rect)

        # if hasattr(self, "last_click"):             # Keep for debugging int() roundoff problems
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
        s = Store()
        # self.last_click = (x_px, y_px)        # Keep for debugging int() roundoff problems
        # self.update()

        width = self.width() - 2 * self.margin_x
        height = self.height() - 2 * self.margin_y
    
        # Ensure click is inside plot area
        if not (self.margin_x <= x_px <= self.width() - self.margin_x and
                self.margin_y <= y_px <= self.height() - self.margin_y):
            return
    
        # Convert X (log scale)
        x_ratio = (x_px - self.margin_x) / width    # Per-unit position of click in graph, 0 -> 1
        freq = self.start_freq * (self.end_freq / self.start_freq) ** x_ratio

        # ---------------------------------------------------------------------
        #   WRW 24-June-2025 - Quantize clicks for reproducibility
        #   Quantizing points not related to generated points or genrated points options.
        #   Quantize to graph grid

        f0 = self.start_freq
        n = round( np.log2( freq / f0 ) * s.Const.graphPointsPerOctave )
        freq = f0 * 2 ** ( n/s.Const.graphPointsPerOctave )

        # Convert Y (audiogram: 0 dB at top)
        y_ratio = (y_px - self.margin_y) / height
        hearing_loss = self.loss_db_min + (self.loss_db_max - self.loss_db_min) * y_ratio
        loss_db = -hearing_loss
    
        qpp10db = s.Const.graphPointsPer10dB  # Quantize to qpp10db points per 10 dB
        loss_db = round( loss_db * (qpp10db/10) ) / ( qpp10db/10 )

        self.pointClicked.emit( freq, loss_db )

# -------------------------------------------------------------------------------------

class MainWindow( QMainWindow ):
    def __init__(self ):
        super().__init__()
        s = Store()

        self.exitPrepFlag = False       # set by do_exit()
        self.state_saved = False         # to prevent multiple calls, extra from closeEvent.

        # ------------------------------------------------------------------

        self.windowTitle = s.Const.What_Full_Title
        self.setup_menus( )

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
        #   Setup eye candy.
        #   Race condition between closeEvent() and scope_closed()
        #       that was previously caused by s.scope_dialog.rejected.connect( self.scope_closed )

        s.scope_dialog = ScopeDialog( on_closed=self.scopeClosedCallback )
        s.scope_dialog_showing = False

        # ------------------------------------------------------------------

        #  self.loss_db_min, ... too embedded already to replace with s.Const.loss_db_min ...

        self.loss_db_min = s.Const.loss_db_min
        self.loss_db_max = s.Const.loss_db_max
        self.gain_db_min = s.Const.gain_db_min
        self.gain_db_max = s.Const.gain_db_max
        self.reference_level = s.Const.reference_level

        # ------------------------------------------------------------------
        #   Set up the UI

        self.status = self.statusBar()
        self.stateLabel = QLabel( )

        self.status.addPermanentWidget(self.stateLabel)

        self.setWindowTitle( self.windowTitle )

        self.graph = GraphWidget( self.loss_db_min, self.loss_db_max, self )
        self.graph.pointClicked.connect( self.pointClick )

        self.playing = ColorIndicator( )

        self.gain_lcd = LCDLabel()
        self.gain_lcd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gain_lcd.setDigitCount(8)
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
        exit_button.clicked.connect( self.do_exit )
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
        txt = """<b>Next tone:</b> Space / Down-Arrow. <b>Specific tone:</b> Click in graph.
                 <b>Accept:</b> Right-Arrow. <b>Reject:</b> Left-Arrow. <b>Repeat:</b> Up-Arrow.
                 <b>Go back:</b> Backspace. """
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
        #   Restore saved parameters         

        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        gain_points_per_10dB = settings.value("gain_points_per_10dB" )
        points_per_octave = settings.value("points_per_octave" )
        start_freq = settings.value("start_freq" )
        end_freq = settings.value("end_freq" )

        if ((gain_points_per_10dB is not None) and 
            (points_per_octave is not None) and
            (start_freq is not None) and
            (end_freq is not None)):
            self.set_parameters( int(gain_points_per_10dB), int(points_per_octave), int(start_freq), int(end_freq) )

        else:
            self.set_default_parameters()

    # -------------------------------------------------------------------------------------

    def set_default_parameters( self ):
        s = Store()
        self.set_parameters( s.Const.test_gain_points_per_db, s.Const.test_points_per_octave, s.Const.start_freq, s.Const.end_freq )

    # -------------------------------------------------------------------------------------
    #   Count and range parameters for test tones and graph.
    #   Started with octaves but switched to decades.

    def set_parameters( self, gain_points_per_10dB, points_per_octave, start_freq, end_freq ):

        self.graph.set_parameters( start_freq, end_freq )                                                 

        #   Primary parameters

        self.gain_points_per_10dB = gain_points_per_10dB
        self.points_per_octave = points_per_octave
        self.start_freq = start_freq
        self.end_freq = end_freq

        #   Derived parameters

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
        #   WRW 23-June-2025 - add sub-10-dB gains_db. Compute for one 10-dB interval first.

        interval = 10/self.gain_points_per_10dB
        base_gains_db = [ i * interval for i in range( self.gain_points_per_10dB ) ]

        self.test_gains_db = []

        for gain_db in range( self.gain_db_min, self.gain_db_max + 10, 10 ):            # -80 to 0
            for i in base_gains_db:
                t = round( gain_db + i, 2 )
                if t > 0:
                    break
                self.test_gains_db.append( t )

        self.gain_points_total = len( self.test_gains_db )

        # -----------------------------------------
        #   WRW 24-June-2025 - Make a reverse map to go from freq/gain_db to gindex and findex
        #       for going back in tone sequence.

        self.reverse_map = {}

        for findex, freq in enumerate( self.test_freqs ):
            for gindex, gain_db in enumerate( self.test_gains_db ):
                if (freq, gain_db) in self.reverse_map:
                    print( f"ERROR-DEV: {freq} {gain_db} already present in map" )
                else:
                    self.reverse_map[ (freq, gain_db) ] = ( findex, gindex )

        self.reset()

    # -------------------------------------------------------------------------------------
    #   Initialize many parameters on first run or subsequent after 'Reset'

    @Slot()
    def reset( self ):
        self.saved_flag = False
        self.sm_state = SM.S_Start
        self.sm_state = SM.S_Wait       # /// TESTING
        self.findex = 0
        self.gindex = 0
        self.current_freq = self.test_freqs[ self.findex ]
        self.current_gain_db = self.test_gains_db[ self.gindex ]

        self.current_ck_freq = None                 # Bug catcher
        self.current_ck_gain_db = None              # Bug catcher

        self.graph.clear_points()
        self.graph.clear_marker()
        self.done_label.hide()
        self.freq_lcd.display( 'Pitch' )
        self.gain_lcd.display( 'Gain' )
        self.completed_lcd.display( 'Step' )
        self.status.showMessage( "Play next tone or click in graph.")
        self.stateStack = None
        self.processed = OrderedDict()
        self.processed_ck = OrderedDict()

        initialStatus = "Current-State, Input --> fsm-function() --> Next-State" 
        self.stateLabel.setText( initialStatus )

    # ==============================================================================
    #   WRW 16-June-2025 - The user interactions were getting a bit awkward and the
    #       code a bit messy. Try a FSM approach. Looks great. Haven't used this   
    #       structure since probably 1984 or 1985. 40 years ago, ouch!
    #       The matrix contains the function that is executed for a given state / input pair.
    #       The function returns the next state or None to remain in current state.

    #       Got complicated when mixing clicks and tone sequence.

    #   WRW 18-June-2025 - Add S_Click* states for explicit control.
    #       Enter S_Click* states with mouse click. Exit with Space/Down to play next tone in sequence.
    #       I sure hope the ability to interrupt the current tone sequence with a click is useful, it
    #       took a lot to do it right: additional states and a stack to save the non-click state when
    #       enter the click state. Not really a stack but like one with a depth of one.
    #       The state machine made this relatively easy to do.

    # ------------------------------------------------------------------------------
    #   State definitions

    #   S_Start     -       At beinning of test, only action is play tone or click play..
    #   S_Wait      -       After tone played, waiting for accept or reject
    #   S_ClickWait      -  After tone played, waiting for accept or reject
    #   S_Accepted  -       After accept, user may change mind and reject, repeat, play next
    #   S_ClickAccepted  -  After accept, user may change mind and reject, repeat, play next
    #   S_Rejected  -       After reject, user may change mind and accept, repeat, play next
    #   S_ClickRejected  -  After reject, user may change mind and accept, repeat, play next
    #   S_Complete  -       At end of test, all tones played, no further action
    #
    # ------------------------------------------------------------------------------
    #   State Machine for user interactions with graph.

    def init_state_machine( self ):
        # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # State: S_Start         S_Wait           S_ClickWait        S_Accepted               S_ClickAccepted     S_Rejected               S_ClickRejected    S_Complete
                                                                                                                                                                         #   Input:
        self.state_matrix= [                                                                                                                                             #   --------
            [   self.sm_play,    self.sm_play,    self.sm_play,      self.sm_play_next_freq,  self.sm_play,       self.sm_play_next_gain,  self.sm_play,      None,  ],  #   I_Play
            [   None,            self.sm_accept,  self.sm_ckaccept,  self.sm_accept,          self.sm_ckaccept,   self.sm_accept,          self.sm_ckaccept,  None,  ],  #   I_Accept
            [   None,            self.sm_reject,  self.sm_ckreject,  self.sm_reject,          self.sm_ckreject,   self.sm_reject,          self.sm_ckreject,  None,  ],  #   I_Reject
            [   None,            self.sm_repeat,  self.sm_ckrepeat,  self.sm_repeat,          self.sm_ckrepeat,   self.sm_repeat,          self.sm_ckrepeat,  None,  ],  #   I_Repeat
            [   self.sm_ckplay,  self.sm_ckplay,  self.sm_ckplay,    self.sm_ckplay,          self.sm_ckplay,     self.sm_ckplay,          self.sm_ckplay,    None,  ],  #   I_Click
            [   None,            self.sm_back,    self.sm_ckback,    self.sm_back,            self.sm_ckback,     self.sm_back,            self.sm_ckback,    None,  ],  #   I_Back
        ]

    # --------------------------------------------------------
    #   User clicked a point on the graph. Y-axis on graph
    #   is hearing loss. Convert to gain_db for tone
    #   to be heard at that loss.
    #   22-June-2025 - Add int() to hearing_loss and freq

    @Slot( float, float )
    def pointClick( self, freq, hearing_loss ):
        gain_db = self.reference_level - round(hearing_loss, 1)
        self.sm_proc_input( IM.I_Click, freq=int(freq), gain_db=gain_db )

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

        elif event.key() == Qt.Key_Backspace:
            self.sm_proc_input( IM.I_Back )

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
            if nextState is not None:
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
        self.play_test_tones( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")

        if self.stateStack is not None:             # Returning from one of the SM_Click* states.
            t = self.stateStack
            self.stateStack = None
            return t
        return SM.S_Wait

    # ------------------------------------------------
    #   Play tone at frequency / gain selected by mouse click or current ck frequency / gain.

    def sm_ckplay( self, kwargs ):
        if self.stateStack is None:         # Entering the SM_ClickWait state, save non-click state.
            self.stateStack = kwargs[ 'currentState' ]      # kwargs[ 'currentState' ] always set by sm_proc_input()

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
        self.play_test_tones( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")
        return SM.S_ClickWait

    # ---------------------------------------------------------------------
    #   Play tone at current frequency / gain, don't change state.

    def sm_repeat( self, kwargs ):
        freq = self.current_freq
        gain_db = self.current_gain_db
        self.status.showMessage("Playing tone.")
        self.play_test_tones( freq, gain_db )
        self.status.showMessage("Waiting for Accept / Reject.")
        return None

    # ------------------------------------------------
    #   Play tone at current ck frequency / gain, don't change state.

    def sm_ckrepeat( self, kwargs ):
        freq = self.current_ck_freq
        gain_db = self.current_ck_gain_db
        self.status.showMessage("Playing tone.")
        self.play_test_tones( freq, gain_db )
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
        self.play_test_tones( freq, gain_db )
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
        self.play_test_tones( freq, gain_db )
        self.status.showMessage( "Waiting for Accept / Reject.")
        return SM.S_Wait

    # ---------------------------------------------------------------------
    #   User accepted tone

    def sm_accept( self, kwargs ):
        hearing_loss = self.current_gain_db - self.reference_level
        self.graph.add_point( self.current_freq, hearing_loss, True )
        self.status.showMessage("Accepted. Play next tone or click in graph.")
        self.processed[ (self.current_freq, hearing_loss )] = True
        return SM.S_Accepted

    # ------------------------------------------------
    #   User accepted tone from mouse click

    def sm_ckaccept( self, kwargs ):
        hearing_loss = self.current_ck_gain_db - self.reference_level
        self.graph.add_point( self.current_ck_freq, hearing_loss, True )
        self.status.showMessage("Accepted. Play next tone or click in graph.")
        self.processed_ck[ (self.current_ck_freq, hearing_loss )] = True
        return SM.S_ClickAccepted

    # ---------------------------------------------------------------------
    #   User rejected tone

    def sm_reject( self, kwargs  ):
        hearing_loss = self.current_gain_db - self.reference_level
        self.graph.add_point( self.current_freq, hearing_loss, False )
        self.status.showMessage("Rejected. Play next tone or click in graph.")
        self.processed[ (self.current_freq, hearing_loss )] = False
        return SM.S_Rejected

    # ------------------------------------------------
    #   User rejected tone from mouse click

    def sm_ckreject( self, kwargs  ):
        hearing_loss = self.current_ck_gain_db - self.reference_level
        self.graph.add_point( self.current_ck_freq, hearing_loss, False )
        self.status.showMessage("Rejected. Play next tone or click in graph.")
        self.processed_ck[ (self.current_ck_freq, hearing_loss )] = False
        return SM.S_ClickRejected

    # ------------------------------------------------
    #   User wants to back up in test sequence
    #       self.current_freq = self.test_freqs[ self.findex ]
    #       self.current_gain_db = self.test_gains_db[ self.gindex ]

    def sm_back( self, kwargs ):

        if self.processed:
            (freq, loss), t = self.processed.popitem()                  # Fetch last added point
            gain_db = loss + self.reference_level

            self.graph.remove_point( freq, loss )                       # Remove it from graph
            self.graph.set_marker( freq, loss, '#00c000' )              # Mark where removed from

            point = (freq, gain_db) 
            if point in self.reverse_map:
                findex, gindex = self.reverse_map[ (freq, gain_db) ]    # get findex/gindex of point in test points
            else:
                print( f"ERROR: {point} not found in reverse_map" )
                return None

            self.findex = findex                                        # Restore self.findex/self.gindex to removed point
            self.gindex = gindex
            self.completed_lcd.display( f"{self.findex+1}/{len(self.test_freqs)}" )

            self.current_freq = self.test_freqs[ self.findex ]
            self.current_gain_db = self.test_gains_db[ self.gindex ]

            self.freq_lcd.display( f"{int(freq )} Hz")
            self.gain_lcd.display( f"{int(gain_db )} dB")

            return SM.S_Wait

        else:
            self.status.showMessage( "No more test points.")
            return SM.S_Start

    # ------------------------------------------------
    #   User wants to back up in click points. Just remove from graph

    def sm_ckback( self, kwargs  ):
        if self.processed_ck:
            (freq, loss), t = self.processed_ck.popitem()               # Fetch last added point    
            gain_db = loss + self.reference_level

            self.graph.remove_point( freq, loss )                       # Remove it from graph      
            self.graph.set_marker( freq, loss, '#00c000' )              # Mark where removed from

            self.completed_lcd.display( f"User" )

            self.current_ck_freq = freq
            self.current_ck_gain_db = gain_db

            self.freq_lcd.display( f"{int(freq )} Hz")
            self.gain_lcd.display( f"{int(gain_db )} dB")

        else:
            self.status.showMessage( "No more click points.")

        return SM.S_ClickWait

    # =========================================================================

    def play_test_tone( self ):
        test_freq = 1000
        test_gain_db = 0
        test_gain = 10 ** (test_gain_db/20)

        self.playing.setColor( '#00ff00' )
        self.freq_lcd.display( f"{int(test_freq )} Hz")
        self.gain_lcd.display( f"{int(test_gain_db )} dB")
        QApplication.processEvents()
        tone = self.gen_tone( test_freq, .75, test_gain )     # play tone for .75 seconds
        self.play_tone( tone )
        self.playing.setColor( '#c0c0c0' )

    # ------------------------------------------------------------------------------
    #   Alt functions generate the entire three tone/silence sequence before starting
    #   playback. When switched to sounddevice got buffer underruns when doing each separately.

    def play_test_tones( self, freq, gain_db ):
        self.freq_lcd.display( f"{int(freq)} Hz")
        # self.gain_lcd.display( f"{int(gain_db )} dB")
        self.gain_lcd.display( f"{round(gain_db,1)} dB")

        self.playing.setColor( '#00ff00' )
        loss = gain_db - self.reference_level
        self.graph.set_marker( freq, loss, '#00c000' )
        self.playing.repaint()              # 23-June-2025, problem on macOS - color not showing, this resolved
        QApplication.processEvents()        # To give lcd and label a chance to change.

        gain = 10 ** (gain_db/20)

        tones = []
        for j in range( 3 ):                                    # repeat tone three times
            tone = self.gen_tone( freq, self.dur, gain )        # make tone

            if True:  # Windows is clipping the end, add silence
                silence = self.gen_tone( freq, self.dur, 0 )    # make silence
                tones = np.concatenate( [tones, tone, silence] )    # combine in one buffer

            if False:
                if j < 2:                                           # Don't need trailing silence
                    silence = self.gen_tone( freq, self.dur, 0 )    # make silence
                    tones = np.concatenate( [tones, tone, silence] )    # combine in one buffer
                else:
                    tones = np.concatenate( [tones, tone] )    # combine in one buffer

        self.play_tone( tones )

        self.playing.setColor( '#808080' )

    # --------------------------------------------------------
    #   simpleaudio.play_buffer(audio_data, num_channels, bytes_per_sample, sample_rate)
    #   Works fine without tobytes() but chat says better to include it.

    def gen_tone( self, freq, dur, gain, show=False ):
        audio = self.p.make_wave_from_freq_dur( freq, dur, show ) * gain  # freq in hz, dur in seconds.
        return audio

    # --------------------------------------------------------
    def play_tone( self, audio ):
        s = Store()
        self.fs = 44100

        if s.scope_dialog_showing:
            s.scope_dialog.update_signal( audio )
            QApplication.processEvents()        # To give scope a chance to show graph.

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

    # -----------------------------------------------------------------
    #   WRW 28-June-2025 - User clicked Exit button or Quit from menu. 
    #   Shutdown in orderly manner.
    #   This will trigger overridden closeEvent().

    def do_exit( self ):
        s = Store()
        s.Verbose and print( "/// do_quit()", s.scope_dialog_showing )

        if not self.do_exit_test():
            return                  #   User doesn't really want to exit.

        self.do_save_state()        #   Otherwise save state and quit. Do before scope_dialog.close() as that changes state.
        s.scope_dialog.close()      #   Close the dialog window whether it is open or not, no issue if not.
        self.exitPrepFlag = True
        QApplication.quit()         #   End things gracefully. Will trigger closeEvent()

    # ------------------------------------------------------------------------------
    #   WRW 29-June-2025 - Separated from closeEvent() to share with other code
    #   Trying to get away from doing all on closeEvent(). 
    #   Return True to exit, False to suppress exit.

    def do_exit_test( self ):
        s = Store()
        s.Verbose and print( "/// do_exit_test()" )
        count = len( self.graph.get_accepted_points( ) )
        if count and not self.saved_flag:
            reply = QMessageBox.question(
                self,
                self.windowTitle,
                "You have test results that have not been saved.\nAre you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # default
            )

            if reply == QMessageBox.Yes:
                return True
            else:
                return False

        return True         # Ok to exit without asking if nothing in graph or already savd.

    # ------------------------------------------------------------------------------
    #   Save the state of the application for restoratin on next launch.

    def do_save_state( self ):
        s = Store()
        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        settings.setValue( "gain_points_per_10dB", self.gain_points_per_10dB )
        settings.setValue( "points_per_octave", self.points_per_octave )
        settings.setValue( "start_freq", self.start_freq )
        settings.setValue( "end_freq", self.end_freq )
        settings.setValue( "geometry", self.saveGeometry())
        settings.setValue( "scope_geometry", s.scope_dialog.saveGeometry())
        settings.setValue( "scope_showing", s.scope_dialog_showing )
        self.state_saved = True
        s.Verbose and print( "/// do_save_state()", s.scope_dialog_showing )

    # --------------------------------------------------------
    #   Override closeEvent() to prompt user to save results, if any, and save state.
    #   WRW 28-June-2025 - closeEvent() and scopeClosedCallback() can be called in any order.
    #       Issue saving s.scope_dialog_showing. Pickup 'Quit' button and save there.
    #       Resolved by overriding closeEvent in Scope() and calling scopeClosedCallback() here.
    #   WRW 29-June-2025 - Lots of thrashing about and race conditions with Scope regaring exit.
    #       New approach now puts most logic in do_exit() but duplicates here for the
    #       case where the user closes the app with the 'X' in the border, less orderly but try.
    #       This is called an any exit, controlled from do_exit() and uncontrolled from 'X'.d
    #       Previously trying to do all here.

    def closeEvent(self, event):
        s = Store()
        s.Verbose and print( "/// What? closeEvent" )

        if not self.exitPrepFlag:           # May have already asked user in do_exit()
            if not self.do_exit_test():     # Give user a second chance on 'X', too.
                event.ignore()
                return

        if not self.state_saved:
            self.do_save_state()        #   Do before close dialog.

        s.scope_dialog.close()          #   Close the dialog window whether it is open or not, no issue if not.
        event.accept()
        super().closeEvent(event)       #   And finally get out of her.

    # ------------------------------------------------------------------------------
    #   Give graph focus after user hit return

    Slot()
    def return_pressed(self):
        self.graph.setFocus()

    # ------------------------------------------------------------------------------
    #   Sort by ascending frequency, user may test frequencies out of order, test frequencies certainly are.
    #   WRW 16-June-2025 - select the least loss that has been accepted, i.e. value of True.
    #   audiogram: [ (freq, gain_db), (freq, gain_db) ]
    #   WRW 24-June-2025 - Migrate to using points saved in graph instead of separate results array.

    @Slot()
    def do_save( self ):
        s = Store()
        audiogram = self.graph.get_accepted_points()
        if not audiogram:
            QMessageBox.information( self, self.windowTitle, "No accepted results to save" )
            return

        audiogram = sorted( audiogram, key=lambda x: x[0] ) # Sort by frequency

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
        title = f"Audiogram for: {user}, {mode}, {title_timestamp}"

        file_timestamp = now.strftime('%d-%b-%Y_%H-%M-%S')
        ofile = f"Audiogram-{user}-{smode}-{file_timestamp}.png"

        # Show folder picker dialog
        path = QFileDialog.getExistingDirectory( self,
                    "Select Output Folder",
                    options=QFileDialog.Options() | QFileDialog.DontUseNativeDialog )

        if path:
            fpath = os.path.join( path, ofile)
        else:
            QMessageBox.information( self, "Cancelled", "No folder selected.")
            return

        #   WRW 23-June-2025 - do_plot() now with 'import matplotlib' takes enough time
        #       that we need a busy cursor.

        s.app.setOverrideCursor( QCursor(Qt.WaitCursor) )
        self.do_plot( audiogram, title, fpath, smode )
        s.app.restoreOverrideCursor()

        msg = f"Test results saved in:\n{fpath}"
        QMessageBox.information( self, self.windowTitle, msg )
        self.saved_flag = True

    # --------------------------------------------------------
    #   WRW 23-June-2025 - Defer import of matplotlib until needed
    #   lock in 'Agg' backend so matplotlib doesn't look further. Did not resolve long import
    #   time but chat recommends keeping it. Add WaitCursor around this above.
    #   Standard audiogram:
    #       Frequencies tested: 125 Hz, 250 Hz, 500 Hz, 1000 Hz, 2000 Hz, 3000Hz, 4000 Hz, and 8000 Hz.
    #       Loss -10 to 120
    #       Right ear - Red 'o'
    #       Left ear - Blue 'x'
    #   This uses the symbols but not the loss range nor frequencies.

    # -------------------------------------------------------------------------------------

    def do_plot( self, data: list[tuple[int, int]], title, ofile, smode ):

        s = Store()
        import matplotlib
        matplotlib.use('Agg')           
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FixedLocator, FuncFormatter       # WRW 25-June-2025
        from matplotlib.offsetbox import AnchoredText

        # -----------------------------
        #   Unzip data into two arrays.
        freqs, gains = zip(*data)   # with '*' unzips (( f1, g1 ), ( f2, g2 ), ... ) into (f1, f2, ...), (g1, g2, ...)
    
        # -----------------------------
        #   Create figure and set title

        dpi = 100
        fig = plt.figure(figsize=( s.Const.plot_width_in, s.Const.plot_height_in ), dpi=dpi)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title( title )

        # -----------------------------
        #   Plot - Define marker characteristics

        if smode == 'B':
            marker = 'o'
            # color = '#000000'
            facecolor = '#000000'
            edgecolor='#000000'

        elif smode == 'L':
            marker = 'x'
            # color = '#0000ff'
            facecolor = 'none'
            edgecolor='#0000ff'

        elif smode == 'R':
            marker = 'o'
            # color = '#ff0000'
            facecolor = 'none'
            edgecolor='#ff0000'

        ax.plot(freqs, gains, 
            marker=marker,
            markersize=7,
            markeredgewidth=1.4,
            linestyle='-',
            color='#000000',
            linewidth=.75,
            markerfacecolor=facecolor,
            markeredgecolor=edgecolor 
        )
    
        # -----------------------------
        #   Axes labels and tick params

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Hearing Loss (dB) (Required gain for normal hearing)")
        ax.tick_params(axis='both', which='major', length=4, width=1, labelsize=8)

        # -----------------------------
        #   Y-axis: 0 at top

        ax.set_ylim(self.loss_db_max, self.loss_db_min )
        ax.set_yticks( self.graph.major_losses )
        ax.set_yticks( self.graph.minor_losses, minor=True )

        ax.yaxis.set_major_formatter( FuncFormatter(lambda x, _: f"{int(x)}"))
    
        # -----------------------------
        #   X-axis:

        #   Set tick positions (major & minor)
        ax.set_xlim(self.start_freq, self.end_freq)
        ax.set_xscale("log")

        ax.xaxis.set_major_locator( FixedLocator( self.graph.major_freqs ))
        ax.xaxis.set_minor_locator( FixedLocator( self.graph.minor_freqs ))

        #   Set tick labels (major only)
        def format_tick(x, _):
            return f"{int(x):,}" if x in self.graph.major_freqs else ""

        ax.xaxis.set_major_formatter(FuncFormatter(format_tick))
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda x, _: ""))  # Hide minor labels

        # -----------------------------
        #   Grid
        #   ax.grid(True, which='both', linestyle='--', alpha=0.4)

        #   linestyle: '-', '--', '-.', ':', 'None', ' ', '', 'solid', 'dashed', 'dashdot', 'dotted''

        ax.grid(True, which='major', linewidth=1, color='#808080', linestyle='dashed')
        ax.grid(True, which='minor', linewidth=1, color='#a0a0a0', linestyle='dotted')
    
        # -----------------------------
        #   Add a little advertisement

        txt = f"""{s.Const.What_Full_Title}\nhttps://what.wrwetzel.com"""
        info_box = AnchoredText( txt, loc='lower center')
        ax.add_artist(info_box)

        # -----------------------------
        #   Write graph to file

        fig.tight_layout()
        fig.savefig(ofile)
        plt.close(fig)

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
        quit_action.triggered.connect( self.do_exit )
        file_menu.addAction(quit_action)

        # View menu
        view_menu = menu_bar.addMenu("View")
        scope_action = QAction("Show Waveform", self)
        scope_action.triggered.connect( self.show_scope )
        view_menu.addAction(scope_action)
    
        # Parameters menu
        param_menu = menu_bar.addMenu("Parameters")

        self.show_points_action = QAction("View", self)
        self.show_points_action.triggered.connect(self.show_parameters)
        param_menu.addAction(self.show_points_action)

        param_action = QAction("Edit", self)
        param_action.triggered.connect(self.edit_parameters)
        param_menu.addAction(param_action)

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
        dialog = ParameterDialog( self.gain_points_per_10dB, self.points_per_octave, self.start_freq, self.end_freq, self )
        if dialog.exec():
            gain_points_per_10dB, points_per_octave, start_freq, end_freq = dialog.values()
            self.set_parameters( gain_points_per_10dB, points_per_octave, start_freq, end_freq )

    # -----------------------------------------------------------------

    def show_scope( self ):
        s = Store()
        s.scope_dialog_showing = True        # Tell play_tone to send data to scope.
        s.scope_dialog.show()

    def scopeClosedCallback( self ):
        s = Store()
        s = Store()
        s.Verbose and print( "/// scopeClosedCallback()" )
        s.scope_dialog_showing = False       # Only to save a few cycles rendering the scope on each tone.

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
            <li><b>Gain points / 10 dB:</b> {self.gain_points_per_10dB}</li>
            <li><b>Frequency Range:</b> {self.start_freq} Hz to {self.end_freq} Hz</li>
            <li><b>Frequency Points / octave:</b> {self.points_per_octave}</li>
        </ul>

        <h5>Derived</h5>
        <ul>
            <li><b>Gain points</b> {self.gain_points_total}</li>
            <li><b>Frequency Points</b> {self.points_total+1}</li>
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
        s = Store()
    
        file = QFile( s.Const.License )
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            txt = stream.readAll()
            file.close()
        else:
            txt = f"ERROR-DEV: Can't find license file: '{s.Const.License}'"
    
        self.show_dialog( "License", txt )

        if False:                               # This was NG on macOS, included html tags.
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("License")
            msg.setTextFormat(Qt.RichText)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowFlags(Qt.Dialog)       # /// 30-June-2025 - Testing to avoid showing html tags on macOS
            msg.setText( txt )
            msg.exec()

    # ---------------------------------------------------------------------------------

    def show_dialog( self, title, html_text):
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

    def get_glibc_version( self ):
        try:
            # Load the C standard library
            libc = ctypes.CDLL("libc.so.6")
            # Get the gnu_get_libc_version function
            gnu_get_libc_version = libc.gnu_get_libc_version
            gnu_get_libc_version.restype = ctypes.c_char_p
            # Call the function and decode the result
            version = gnu_get_libc_version().decode("utf-8")
            return version
        except Exception as e:
            return f"Error retrieving glibc version: {e}"

    # ---------------------------------------------------------------------------------

    def show_about(self):
        txt = self.get_about()
        self.show_dialog( "About What?", txt )

    # ---------------------------------------------------

    def get_about(self):

        s = Store()

        # ----------------------------------

        screen = QGuiApplication.primaryScreen()
        logical_dpi = screen.logicalDotsPerInch()  # You can also use physicalDotsPerInch()
        physical_dpi = screen.physicalDotsPerInch()  # You can also use physicalDotsPerInch()
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            run_environment = "PyInstaller bundle"

        else:
            run_environment = "Python process"

        # ----------------------------------
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = os.path.realpath( s.Const.Me )

        try:
            # mtime = os.path.getmtime(app_path)
            # timestamp = time.strftime('%a, %d-%b-%Y, %H:%M:%S', time.localtime(mtime))
            timestamp = datetime.datetime.fromtimestamp( Path( app_path ).stat().st_mtime ).strftime( '%a, %d-%b-%Y, %H:%M:%S')

        except Exception:
            timestamp = f"Not available for {app_path}"

        # ----------------------------------
    
        txt = f"""                                                                                 
            <h3>About What?</h3>
            <p>
            <i>What?</i> is a multi-platform, interactive, tone-based hearing test that
            measures hearing thresholds across a range of frequencies.  Users respond to
            tones using keyboard interaction and results are visualized on a graph and
            saved as an audiogram.
            </p>

            <p>
            What? is written in Python using the PySide6 GUI library.
            </p>
<div style="white-space: pre-wrap;">
<p>
<b>System:</b>
    Architecture: {platform.architecture()}
    Machine: {platform.machine()}
    Node: {platform.node()}
    sys.platform: {sys.platform}
    Platform: {platform.platform()}
    Processor: {platform.processor()}
    Sysname: {platform.system()}
    Release: {platform.release()}
    Version: {platform.version()}
    Original GUI Style: {s.originalStyle}
    glibc version: {self.get_glibc_version()}
</p>
<p>
<b>Display:</b>
    Logical: {logical_dpi:.2f} DPI
    Physical: {physical_dpi:.2f} DPI
    P/L Ratio: {100*physical_dpi/logical_dpi:.2f}%
</p>
<p>
<b>Python:</b>
    Python Version:  {platform.python_version()}
    Pyside6 Version: {QtCore.__version__}
    Runtime Qt Version: {QtCore.qVersion()}
</p>
<p>
<b>What:</b>
    Version: {s.Const.Version}
    Run Environment: {run_environment}
    Package Type: {s.Const.Package_Type}
    Settings Directory: {s.conf.confdir}
    Executable: {s.Const.Me}
    Executable Timestamp: {timestamp}
</p>
</div>
            <p>
            {s.Const.Copyright}
            </p>

        """
        return txt

    # --------------------------------------------------------------------------

    def show_quickstart(self):
        s = Store()

        file = QFile( s.Const.Quick_Start )
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            txt = stream.readAll()
            file.close()
        else:
            txt = f"ERROR-DEV: Can't find quick-start file: '{s.Const.Quick_Start}'"

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

def exception_hook(extype, value, tb):
    trace = '<br>'.join(traceback.format_exception(extype, value, tb))
    txt = f"ERROR: unhandled exception in event loop:<br>type: '{extype}'<br>value: '{value}'<br>{trace}"
    txt = txt.replace( '\n', '<br>' )

    QMessageBox.critical( None, "Critical error", txt )

    QApplication.quit()

# ------------------------------------------------------------------------------------
#   The approach of do_main(), do_main_continue_a(), and do_main_continue_b() plus
#       the singleShots were developed for Birdland-Qt with chat's help. Work well,
#       use here. The one-shot gives Qt the opportunity to run.

def do_main( ):
    s = Store()                                 # Global store, short var name since used a lot.
    QTimer.singleShot(100, lambda: do_main_continue_a())

    sys.excepthook = exception_hook         # WRW 16-May-2025 - catch exceptions in event loop.
    sys.exit( s.app.exec() )

# ----------------------------------------------------------
#   This picks up exceptions that occur while the splash screen
#   is still up and cause a hang.

def do_main_continue_a( ):
    s = Store()                                 # Global store, short var name since used a lot.

    try:
        do_main_continue_b()

    except Exception:
        (extype, value, xtraceback) = sys.exc_info()

        # -------------------------------------------
        #   WRW 16-May-2025 - Show a popup on this failure, otherwise stdout/stderr going
        #   down the tubes in bundled packaging.

        trace = '<br>'.join(traceback.format_exception(extype, value, xtraceback ))
        txt = f"ERROR unhandled exception during startup:<br>type: '{extype}'<br>value: '{value}'<br>{trace}"
        txt = txt.replace( '\n', '<br>' )

        # QMessageBox.critical(parent, "Title", "Message text")
        QMessageBox.critical( None, "Critical error", txt )

        # -------------------------------------------

        s.splash.close()                # Out of an abundance of OCD caution. quit() below should do it.
        QApplication.quit()

# ----------------------------------------------------------
#   WRW 17-Apr-2025 - Continue with original content of do_main() after a short oneshot 
#       enclosure in a try/except.

def do_main_continue_b():
    s = Store()                     # Global store, short var name since used a lot.
    s.Verbose = False               # Only for debugging, no need for option.
    s.conf = Config()

    s.splash_pix.progress( "Startup" )

    # ------------------------------------------------------------------
    #   Do this every time to be sure it gets done once and again after
    #   updates.

    if s.Const.Platform == 'Linux':
        make_desktop()

    # ------------------------------------------------------------------
    #   Do this only on first launch.

    if not s.conf.check_config_directory():
        s.conf.initialize_config_directory()

    # ------------------------------------------------------------------
    #   Set the icon in the window decoration

    s.app.setWindowIcon( QIcon( s.Const.What_Icon_PNG ))

    # ------------------------------------------------------------------

    s.Const.set( 'Me', __file__ )

    # ------------------------------------------------------------------
    #   Build the user interface.

    s.splash_pix.progress( "Build User Interface" )

    window = MainWindow( )
    window.setStyleSheet( StyleSheet )

    # ------------------------------------------------------------------------------------------
    #   Restore geometry settings if saved

    settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
    geometry = settings.value( "geometry")
    scope_geometry = settings.value( "scope_geometry" )
    scope_showing = settings.value( "scope_showing" )

    if geometry is not None:
        window.restoreGeometry(geometry)
    else:
        size = QApplication.primaryScreen().size()
        width = size.width()
        height = size.height()
        width = min( 1000, width )              # /// Don't want it too big on my desktop
        height = width/1.61                     # Golden rectangle ratio
        window.resize( width*.8, height*.8 )

    if scope_geometry is not None:
        s.scope_dialog.restoreGeometry(scope_geometry)
    else:
        s.scope_dialog.resize(1000, 300)

    if scope_showing is not None:
        if scope_showing == 'true':
            s.scope_dialog_showing = True
            s.scope_dialog.show()
        else:
            s.scope_dialog_showing = False
    else:
        s.scope_dialog_showing = False

    # ------------------------------------------------------------------------------------------

    window.show()

    # ------------------------------------------------------------------------------------------
    #   Finally close the splash screen. Application already exec()'ed

    def finish_splash():
        if s.splash:
            if True:
                s.splash.close()
            else:
                s.splash.finish( s.window )

            s.splash = None  # only after it's safely closed

        # -----------------------------------------------------------

    QTimer.singleShot(50, finish_splash )

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    do_main()

# ------------------------------------------------------------------------------
