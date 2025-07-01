:: # --------------------------------------------------------------------------------------------------
:: #   WRW 3-Apr-2025 - too much to remember, encpsulte in shell script

set start=%time%
pushd src
pyside6-rcc bl_resources.qrc -o bl_resources_rc.py
popd

pyinstaller pyi.win.onedir.spec ^
        --clean ^
        --noconfirm ^
        --distpath %USERPROFILE%\Desktop\onedir ^
        --workpath %USERPROFILE%\Desktop\onedir\Build

set end=%time%
echo Start: %start%
echo End: %end%

:: # --------------------------------------------------------------------------------------------------
