# Install Birdland on Windows

Please read
the *Quick-Start Guide*, the *Documentation Guide*, and *Documentation* as they contains much not covered here.

## System Requirements

Birdland was tested and packaged on Windows 10. It is expected to work on Windows 11 but has not yet been tested.

## Install Birdland
Open on the downloaded .exe file to launch an installation wizard.

See *Helper Applications* in the *Quick-Start Guide* for additional applications you
may wish to install for audio and MIDI playback, viewing ChordPro files, and engraving MIDI files.
Note the requirement to install VLC in *C:\Program Files*.

## Run Birdland
Launch Birdland as you would any other application.

On first launch *Birdland* creates configuration and data directories,
copies a prototype configuration file and several other to the
configuration directory, copies raw-index files and several others to the
data directory, processes the raw-index files, and build a database from
the processed files.  A series of pop-up windows guides you through this.

## Next Steps

See the *Quick-Start Guide* and *Configuration Guide*, which are linked from here and also in the
Birdland *Help* menu.                                                                       

#### Briefly

Go to *File->Settings* to configure the location of your music, audio, midi, ChordPro,
and JJazzLab libraries as applicable and your preferred external viewers and players.

Be sure to also configure the *Canonical->File map file(s)* and
Editable *Canonical->File map file* settings.

Birdland needs to know the mapping between canonical music file names and *your* music files.
Use the tool in the *Edit Canonical->File* tab or
edit Canonical2File.txt in your configuration directory possibly using Example-Canonical2File.txt
as a starting point.

With the settings configured, optionally scan your audio library and then rebuild the database.
Large audio libraries take a long time to scan so you may want to defer that if you are anxious
to get started.

```
Database -> Scan Audio Library
Database -> Rebuild All Tables
```

## Upgrade Birdland
Repeat the steps above in *Install Birdland*. 
The configuration and data directories are preserved on subsequent installations.

## Remove Birdland
Remove Birdland as you would any other application:

```
/// Check
Control Panel -> Programs -> Add / Remove Programs
Select Birdland, click *Remove*
```

The configuration and data directories are not removed. Do it manually if you
really no longer want them. The directory locations are in the *Quick-Start Guide*.
