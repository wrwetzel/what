-------------------------------------------------------------------------
WRW 8-May-2025

Scripts here are used to bundle and package birdland_qt in each of the
three suported platforms, Linux, MacOS, Windows, which are run on each
platform to build for that platform.

Bundling is done with pyinstaller in both onefile and onedir mode.  I
started down the path of assuming I would distribute onefile only despite
the large file size and longer startup time.  After realizing the
advantage of onedir for packaging on MacOS (at great effort in debugging
the .iss files) I decided to use that for all three environments and have
not maintained the onefile scripts.

As of 14-May-2025 I'm planning to distribute only the onedir bundles.

-------------------------------------------------------------------------
Important:

    Run update-version.sh as first step
    Run build* scripts in virtual environment
        activate-what

-------------------------------------------------------------------------

Directions for Making a Release:

    Preparatory:

        Update build number and several version-related files.  

            build-version.sh

            (This is no longer done in the build Linux script so that it
            can be run as a first step and eliminate order dependencies.)
            Generates:
                fb_version.py
                fb_version.iss
                fb_version.sh
                ../Documentation/download-inc.html


    Documentation:

        cd Documentation

        Create PDF files for birdland.md, quickstart.md configuration.md. This must be
            done before building bundles as the PDF files are included in the resource
            file in the bundles.

            Open with Typora, export as PDF.

        Build sphinx-based web page from birdland.md:

            make doc

        Upload sphinx-based web page and remainder of website:

            make site

    Packages:

        Be sure ./YouTube-Index contains current index, which is created in ~/Upload.
        Copy Birdland-Qt folder to macOS and Windows, if not already there through Dropbox.

            rsync -av Birdland-Qt parker:Work

        Build and package bundles for Linux, macOS, and Windows:
            See 'Build and Package Bundles' below:

        Copy resultant packages from each platform to ~/Uploads/Distribution.
            See 'Location of Distributables' below:

        Upload packages:

            make upload

-------------------------------------------------------------------------

Build and Package Bundles:
    Build onedir bundle:
        build.linux.onedir.sh
            pyi.linux.onedir.spec       (Linux)
    
        build.mac.onedir.sh             (Also makes birdland_qt.app, which is packaged)
            pyi.win.onedir.spec         (Windows)
    
        build.win.onedir.bat
            pyi.mac.onedir.spec         (MacOS)
    
    Package onedir bundle:
        pack.linux.sh
        pack.mac.dmg.sh
        pack.win.inno.bat
            pack.win.inno.iss

-------------------------------------------------------------------------

Location of Distributables:

    Linux:
        ~/Uploads/onedir
        ~/Uploads/onefile

    MacOS:
        ~/Uploads/onedir
        ~/Uploads/onefile

    Windows:
        C:\Users\wrw\Desktop\Uploads\onedir
        C:\Users\wrw\Desktop\Uploads\onefile

-------------------------------------------------------------------------

Python module requirements for unbundled installation:
    requirements.txt

-------------------------------------------------------------------------
One File - not presently used

Build distributable file:
    build.linux.onefile.sh
    build.mac.onefile.sh
    build.win.onefile.bat

    With pyinstaller spec file:
        pyi.linux.onefile.spec      (Linux)
        pyi.win.onefile.spec        (Windows)
        pyi.mac.onefile.spec        (MacOS)

-------------------------------------------------------------------------
