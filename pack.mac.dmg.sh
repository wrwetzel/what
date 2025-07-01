#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#   build.mac.dmg.sh - build Birdland dmg image using create-dmg

#   Run in Birdland-Qt directory

#   Installed create-dmg from source from GitHub. May have been
#       OK from homebrew install before. npm install did not work well.
# ------------------------------------------------------------------------------

. src/what_version.sh

DMGDIR=~/Uploads/What/onedir/build_dmg
BUNDLEDIR=~/Uploads/What/onedir
APP=what.app
DMG=what-MacOS-${AppVersionFull}.dmg
NAME="What? Installer"

# ------------------------------------------

# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p $DMGDIR

# Empty the dmg folder.
rm -r $DMGDIR/*

# Copy the app bundle to the dmg folder.

cp -R $BUNDLEDIR/$APP $DMGDIR

# If the DMG already exists delete it.
test -f $BUNDLEDIR/$DMG && rm $BUNDLEDIR/$DMG 

#   create-dmg [options...] output_name.dmg source_folder

#   Maybe later, License is in html, need plain text.
#       --background "src/Images/splash-piano-hori-640-background.png" \
#       --eula Documentation/License.txt \
#       --hdiutil-quiet - WRW 30-June-2025 - Testing using it to prevent popup on console. NG.

create-dmg \
  --icon-size 80 \
  --icon "$APP" 80 80 \
  --app-drop-link 240 80 \
  --volname "$NAME" \
  --window-size 400 240 \
  --window-pos 200 120 \
  --hide-extension "$APP" \
  "$BUNDLEDIR/$DMG" \
  "$DMGDIR"
