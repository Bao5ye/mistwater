@echo off
cd /d "%~dp0"
"G:\Blender\blender.exe" -b -P "%~dp0mistwater_hero.py"
echo.
echo DONE. Check hero_*.png and mistwater_hero.glb in this folder.
pause
