#include "src\what_version.iss"

[Setup]
AppName=What
AppVersion={#AppVersionFull}
DefaultDirName={commonpf}\What
DefaultGroupName=what
UninstallDisplayIcon={app}\what.exe
OutputDir=C:\Users\wrw\Desktop\What\onedir
OutputBaseFilename="what_win_installer_{#AppVersionFull}"
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
CreateUninstallRegKey=yes
SetupIconFile=Documentation\Images\ear-128.ico
WizardImageFile=Documentation\Images\ear-128.bmp

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; Install everything from the one-dir bundle located on the user's Desktop
Source: "C:\Users\wrw\Desktop\What\onedir\what\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

; These files will be tracked and removed by the uninstaller

[Icons]
Name: "{group}\What"; Filename: "{app}\what.exe"
Name: "{userdesktop}\What"; Filename: "{app}\what.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\what.exe"; Description: "Launch What? now"; Flags: nowait postinstall skipifsilent

