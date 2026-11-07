@echo off
cd /d "%~dp0"
python -m kicad_ai.automation.desktop
if errorlevel 1 pause
