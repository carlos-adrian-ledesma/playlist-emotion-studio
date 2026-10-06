@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 playlist_emotion_studio.py
) else (
  python playlist_emotion_studio.py
)
if errorlevel 1 (
  echo.
  echo No se pudo iniciar. Instala Python 3 desde python.org y activa "Add Python to PATH".
  pause
)
