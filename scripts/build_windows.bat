@echo off
setlocal

REM Builds a standalone Windows executable in dist\Musica\Musica.exe.
REM Run this file from the repository root on a Windows machine.

python -m pip install --upgrade pip
python -m pip install -e ".[build]"

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name Musica ^
  --collect-all mutagen ^
  src\musica\app.py

echo.
echo Build finished. Open dist\Musica\Musica.exe to run the app.
endlocal
