# How to build (command line)

## WINDOWS
$ pyinstaller --onefile --windowed .\Source\main.py

### Cleaning up
$ move /Y .\dist\main.exe .\Builds\main.exe && rmdir /S /Q .\build && rmdir .\dist && del .\main.spec

## LINUX

No idea

## MAC

Who knows