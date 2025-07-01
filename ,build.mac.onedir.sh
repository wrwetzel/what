#!/opt/local/bin/bash
# --------------------------------------------------------------------------------------------------
#   WRW 29-Mar-2025 - too much to remember, encpsulte in shell script
#   Rebuild resources as safety measure if I forget to do so before building a bundle

(
    cd src
    pyside6-rcc what_resources.qrc -o what_resources_rc.py
)

time pyinstaller pyi.mac.onedir.spec \
        --clean \
        --noconfirm \
        --distpath ~/Uploads/what/onedir \
        --workpath ~/Uploads/what/onedir/build

# --------------------------------------------------------------------------------------------------
