#   pyi.linux.onedir.spec
# ----------------------------------------------------------------------------------------
#   WRW 21-June-2025 - Taken from birdland for what?

# ----------------------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os
import sys
from pathlib import Path

# ----------------------------------------------------------------------------------------

sys.setrecursionlimit(3000)
block_cipher = None

# ----------------------------------------------------------------------------------------

# Paths

project_root = os.path.abspath(os.getcwd())
src_dir = os.path.join(project_root, "src")

# Collect all .py files manually if needed
# e.g. src/, src/utils/, src/models/, etc.

source_files = [
    os.path.join( src_dir, "what.py"),             # Main entry point, dispatches to many files
    os.path.join( src_dir, "what_resources_rc.py" ),
    os.path.join( src_dir, "make_desktop.py" ),
    os.path.join( src_dir, "what_version.py" ),
    os.path.join( src_dir, "Player.py" ),
    os.path.join( src_dir, "Store.py" )
]
    
    
# ----------------------------------------------------------------------------------------
#   Add data files (relative path inside bundle, source path)
#       Format: (source_file_path, target_directory_in_bundle)

data_files = [
]
data_files += collect_data_files("numpy")

# ----------------------------------------------------------------------------------------
# Collect hidden modules (useful for PySide6 sometimes)
#   hiddenimports = collect_submodules('PySide6')
#   Tested below on python and it looks OK.

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

hiddenimports += collect_submodules("numpy")


a = Analysis(
    source_files,                                          
    pathex=[ src_dir ],
    binaries=[],
    datas=data_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', "pkg_resources", "setuptools", "jaraco", "jaraco.text",
              "pandas", "tkinter", "django", "scipy", 'babel', 'wx', 'sphinx' ],
    cipher=block_cipher,
)

#   a.binaries[] format:
#       (target_filename, source_path, type)
#   [('dest_path', 'source_path', 'BINARY')]

a.binaries += [
]

# ----------------------------------------------------------------------------------------
#   WRW 6-May-2025 - Finally solved a problem causing the executable for a onedir build
#       to fail. The exclude_binaries parameter was False. Wasted almost two days on it.

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,                  # Smoking gun! exclude_binaries=False caused a big, big headache on onedir
    name='what',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                          # True if you want to see a console for output.

    disable_windowed_traceback=False,       # These five copied from .spec file built automatically for simple test
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Documentation/Images/ear-64.ico',       # WRW 27-Mar-2025 - Added, must be .ico
)

#   Include Collect() for onedir

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='what'
)
