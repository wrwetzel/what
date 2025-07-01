#!/usr/bin/env python
# ---------------------------------------------------------------------------
#   WRW 4-Apr-2025
#   build_version.py
#   Called from build for Linux routine, which should be run before Windows and MacOS

#   WRW 8-May-2025 - add support for Inno Setup build file
#   WRW 14-May-2025 - add version in shell script
#   WRW 19-june-2025 - copied for What?

#   Initial from chat.
# ---------------------------------------------------------------------------

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------

VERSION_FILE = Path("what_version.py")
INNO_FILE = Path("what_version.iss")
SHELL_FILE = Path("what_version.sh")
INCLUDE_FILE = Path("../Documentation/download-inc.html")  # WRW 7-June-2025

# -----------------------------------------------------
def bump_build( update_flag ):
    if not VERSION_FILE.exists():
        print("version.py not found.")
        return

    content = VERSION_FILE.read_text()

    # -----------------------------------------------------
    # Match something like: __build__ = 123

    pattern = r'(__build__\s*=\s*)(\d+)'
    match = re.search(pattern, content)

    if not match:
        print("No __build__ variable found.")
        return

    old_build = int(match.group(2))

    if update_flag:                     # WRW 7-June-2025 - added for testing
        new_build = old_build + 1
    else:
        new_build = old_build    

    # -----------------------------------------------------

    # Replace only the build number
    updated = (
        content[:match.start(2)] +
        str(new_build) +
        content[match.end(2):]
    )

    VERSION_FILE.write_text(updated)

    # -----------------------------------------------------
    #   WRW 8-May-2025 - Addition for inno setup
    #       Match something like: __version__ = '2.0.0-beta'

    pattern = r'(__version__\s*=\s*)(.+)'
    match = re.search(pattern, content)

    if not match:
        print("No __version__ variable found.")
        return

    version = match.group(2)

    # -----------------------------------------------------

    inno_version = f"""
#define AppVersionFull "{version}.{new_build}"\n
#define AppVersionShort "{version}"\n
"""
    inno_version = inno_version.replace( "'", "" )     # Strip the single quotes, not wanted for .iss file
    INNO_FILE.write_text( inno_version )

    # -----------------------------------------------------

    shell_version = f"""
AppVersionFull="{version}.{new_build}"  
AppVersionShort="{version}"  
"""
    shell_version = shell_version.replace( "'", "" )     # Strip the single quotes, not wanted for .iss file
    SHELL_FILE.write_text( shell_version )

    # -----------------------------------------------------
    # birdland_qt_win_installer_2.0.0-beta.1098.exe
    # birdland_qt-MacOS-2.0.0-beta.1098.dmg
    # birdland_qt-Linux-2.0.0-beta.1098.zip
    # birdland_qt-Linux-2.0.0-beta.1098.gz

    full = f"{version}.{new_build}"
    full = full.replace( "'", "" )     # Strip the single quotes, not wanted for table

    table_template ="""
    <tr>
        <td>Windows</td>
        <td><a href=/Downloads/birdland_qt_win_installer_<***>.exe download>https://birdland-qt/Downloads/birdland_qt_win_installer_<***>.exe</a><br></td>
        <td><a href="javascript:void(0);" onclick="show_md( '/ReadMe-Windows.md' )" >ReadMe-Windows</a></td>
    </tr>

    <tr>
        <td>macOS</td>
        <td><a href=/Downloads/birdland_qt-MacOS-<***>.dmg download>https://birdland-qt/Downloads/birdland_qt-MacOS-<***>.dmg</a><br></td>
        <td><a href="javascript:void(0);" onclick="show_md( '/ReadMe-macOS.md' )" >ReadMe-macOS</a></td>
    </tr>
    <tr>
        <td>Linux Zip</td>
        <td><a href=/Downloads/birdland_qt-Linux-<***>.zip download>https://birdland-qt/Downloads/birdland_qt-Linux-<***>.zip</a><br></td>
        <td><a href="javascript:void(0);" onclick="show_md( '/ReadMe-Linux.md' )" >ReadMe-Linux</a></td>
    </tr>
    <tr>
        <td>Linux Gzip</td>
        <td><a href=/Downloads/birdland_qt-Linux-<***>.gz download>https://birdland-qt/Downloads/birdland_qt-Linux-<***>.gz</a><br></td>
        <td><a href="javascript:void(0);" onclick="show_md( '/ReadMe-Linux.md' )" >ReadMe-Linux</a></td>
    </tr>
    """
    table_template = table_template.replace( "<***>", full )
    INCLUDE_FILE.write_text( table_template )

    # -----------------------------------------------------
    print(f"Updated __build__ from {old_build} to {new_build}")

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    update_flag = True

    if len( sys.argv ) > 1:
        if sys.argv[1] == '-n':
            update_flag = False

    bump_build( update_flag )

# ---------------------------------------------------------------------------
