#!/usr/bin/bash
# -------------------------------------------------------------------------
#   make-images.sh - convert a single image file to multiple formats and
#       sizes needed for What?.

#   The application, what.py what_resources.qrc (for pyside6-rcc) obtain
#       images from here. Packaging, documentation and site obtains images
#       from $DocDir (Documentation/Images), copied there from here.

#   Run png2icns.sh in $DocDir on macOS to make .icns file, which lives in $DocDir

# -------------------------------------------------------------------------

Source=realistic-ear-large.png
DocDir=../../Documentation/Images

magick $Source -resize 64x64 ear-64.ico
magick $Source -resize 64x64 ear-64.png
magick $Source -resize 64x64 ear-64.bmp
magick $Source -resize 128x128 ear-128.bmp
magick $Source -resize 128x128 ear-128.ico

cp ear-64.png $DocDir
cp ear-64.ico $DocDir
cp ear-128.ico $DocDir
cp ear-128.bmp $DocDir
