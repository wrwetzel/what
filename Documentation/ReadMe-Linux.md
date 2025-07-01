# Install What? on Linux

## System Requirements

What? was developed on an up-to-date (as of spring 2025) Arch Linux system with up-to-date
applications including Python.  While Python and the required Python modules are bundled
in the distribution, system libraries are not.  The development system is running *GNU C
Library (GNU libc) stable release version 2.41.* What? is unlikely to work on Linux
distributions with an older glibc, especially LTS distributions.

You may see an error like:

```
[PYI-970357:ERROR] Failed to load Python shared library
   '/tmp/what/_internal/libpython3.13.so.1.0':
dlopen: /usr/lib/libm.so.6: version `GLIBC_2.38' not found 
  (required by /tmp/what/_internal/libpython3.13.so.1.0)
```
You can check your version of glibc:
```
ldd --version
```
Maybe it's time to bring your system up-to-date? 

## Unpack What?

Unpack the What? distribution file to a convenient location, perhaps a directory
where you install other bundled applications. I'll use the metasyntactic variable
*~/foo* here in for a directory in your home directory.
A directory named *foo* in your home directory is a really bad idea - this is just an example.
```
mkdir ~/foo
cd ~/foo
tar -xzvf what-Linux.*.gz
or
unzip what-Linux.*.zip

```
This creates a new directory, *what* containing the What? executable *what*
and another directory, *_internal*, containing the rest of the bundled files.

```
|-- ~/foo
    |-- what
        |-- what
        |-- _internal
```

Make a symbolic link to the executable from a *bin* directory in your *$PATH*, here *~/bin*.

```
cd ~/bin
ln -s ~/foo/what/what .
```

## Run What?
The name of the executable is *what*. Run it from the command line:

```
what
```
What creates a file *what.desktop* in
*~/.local/share/applications* to add itself to the system menu.
After running it once from the command line you can then run it
from the system menu. 

## Upgrade What?
Repeat the steps above in *Install What?*.

## Remove What?

```
rm ~/foo/what
```
