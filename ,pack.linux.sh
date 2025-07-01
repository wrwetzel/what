#!/usr/bin/bash
# -------------------------------------------------------------------------------
#   pack.linux.sh - Package a Linux onedir bundle for distribution.

#   Reminder: '-C $Dir' changes directory to $Dir before building
# -------------------------------------------------------------------------------

. src/fb_version.sh

Dir=~/Uploads/What/onedir

tar -C $Dir -czvf $Dir/what-Linux-${AppVersionFull}.gz what

cd $Dir
zip -r $Dir/what-Linux-${AppVersionFull}.zip what
