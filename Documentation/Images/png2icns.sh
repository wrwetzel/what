#!/bin/bash

# Set input PNG file and output names
INPUT="$1"
BASENAME=$(basename "$INPUT" .png)
ICONSET="$BASENAME.iconset"
ICNS="$BASENAME.icns"

# Check if input file exists
if [ ! -f "$INPUT" ]; then
  echo "Error: File '$INPUT' not found."
  echo "Usage: ./png2icns.sh your_icon.png"
  exit 1
fi

# Create iconset folder
mkdir -p "$ICONSET"

# Generate all required icon sizes using sips (built-in on macOS)
sips -z 16 16     "$INPUT" --out "$ICONSET/icon_16x16.png"
sips -z 32 32     "$INPUT" --out "$ICONSET/icon_16x16@2x.png"
sips -z 32 32     "$INPUT" --out "$ICONSET/icon_32x32.png"
sips -z 64 64     "$INPUT" --out "$ICONSET/icon_32x32@2x.png"
sips -z 128 128   "$INPUT" --out "$ICONSET/icon_128x128.png"
sips -z 256 256   "$INPUT" --out "$ICONSET/icon_128x128@2x.png"
sips -z 256 256   "$INPUT" --out "$ICONSET/icon_256x256.png"
sips -z 512 512   "$INPUT" --out "$ICONSET/icon_256x256@2x.png"
sips -z 512 512   "$INPUT" --out "$ICONSET/icon_512x512.png"
sips -z 1024 1024 "$INPUT" --out "$ICONSET/icon_512x512@2x.png"

# Convert iconset to .icns
iconutil -c icns "$ICONSET" -o "$ICNS"

# Optional: clean up
rm -r "$ICONSET"

echo "✅ Created $ICNS"

