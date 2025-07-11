.RECIPEPREFIX = +
# ---------------------------------------------------------------------------
#   Makefile for building documentation with sphinx and uploading
#   documentation and packaged software to site.

#   WRW 5-June-2025 - Revised from 2022 version.
#   Sphinx configuration in conf.py

#   WRW 20-June-2025 - Taken for What?

# ---------------------------------------------------------------------------
#   Minimal makefile for Sphinx documentation
#
#   markdown-pdf is an npm file:
#       npm install -g markdown-pdf --ignore-scripts
#       Failed.

#   Use pandoc instead:
#       paru -S python-weasyprint

# ---------------------------------------------------------------------------
#   You can set these variables from the command line, and also
#   from the environment for the first two.

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

DEST      = wrwetzel.com:www/What
LOCALDEST = /home/wrw/Uploads/documentation/

# ---------------------------------------------------------------------------

PHPMailer = \
PHPMailer-master/src/PHPMailer.php \
PHPMailer-master/src/OAuth.php \
PHPMailer-master/src/POP3.php \
PHPMailer-master/src/SMTP.php \
PHPMailer-master/src/Exception.php  

SITE_FILES = what.shtml content.shtml download-inc.html quick-start.html what.css contact.php contact.html \
            ReadMe-Linux.md ReadMe-Windows.md ReadMe-macOS.md $(PHPMailer) Images/ear-64.png Images/favicon.ico \
            Images/screenshot.png Images/Audiogram.png

READMES =
PACKAGES =

MDFILES=

QuickStart=

# ---------------------------------------------------------------------------
# Put it first so that "make" without argument is like "make help".

help:
+ @$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).

# ---------------------------------------------------------------------------
#   Run sphinx on the sources in this directory, copy result to $(LOCALDEST)
#   TARGET is env var

local:
+ TARGET=local sphinx-build -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
+ rsync -avR --exclude ',*' --exclude={'.es1','.ek1','.ec1'} _build/* $(LOCALDEST)
# + rsync -avR --exclude ',*' --exclude={'.es1','.ek1','.ec1'} _build/* _static/* $(LOCALDEST)

# ---------------------------------------------------------------------------
#   WRW 9-June-2025 - Restructured a bit into smaller units.

all: doc site         

# ---------------------------------------------------------------------------
#   Run sphinx on the sources in this directory, copy result to $(DEST)
#   TARGET is env var

# remote:
# + TARGET=production sphinx-build -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
# + rsync -avR --exclude ',*' --exclude={'.es1','.ek1','.ec1'} _build/* _static/* $(DEST)

# ---------------------------------------------------------------------------
#   TARGET is env var

doc:
+ TARGET=production sphinx-build -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

#   -L to copy file pointed to by a symlink, not the symlink

site:
+ rsync -avRL $(SITE_FILES) $(DEST)
# + rsync -avR --exclude ',*' --exclude={'.es1','.ek1','.ec1'} _build/* _static/* $(DEST)

# packages:
# + rsync -av $(PACKAGES) $(READMES) $(DEST)/Downloads

# ---------------------------------------------------------------------------
#   Output was awful
#       pdf:
#       + TARGET=production sphinx-build -b pdf "$(SOURCEDIR)" "$(BUILDDIR)"

#   Never saw output
# pdf:
# + TARGET=production sphinx-build -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)"


# pdf:
# + markdown-pdf \
#     -o Test-Tutorial.pdf \
#     -s /home/wrw/.config/Typora/themes/newsprint.css \
#     -f Letter \
#     $(MDFILES)

# ---------------------------------------------------------------------------
#   Initial conversion, edited by hand.

Xreadme:
+ pandoc \
    --css=/home/wrw/.config/Typora/themes/newsprint.css \
    --standalone \
    -o ../README-NO.md \
    content.shtml quick-start.html

# ---------------------------------------------------------------------------
#   Exploratory.
#       birdland.pdf and quickstart.pdf are exported from Typora, not generated here

birdland:
+ pandoc \
    --css=/home/wrw/.config/Typora/themes/newsprint.css \
    --pdf-engine=weasyprint \
    -o birdland_exp.pdf \
    $(MDFILES)

#    --metadata title="Birdland-Qt Quick-Start Guide" \

quickstart:
+ pandoc \
    --css=/home/wrw/.config/Typora/themes/newsprint.css \
    --pdf-engine=weasyprint \
    -o quickstart_exp.pdf \
    $(QuickStart)

# ---------------------------------------------------------------------------
