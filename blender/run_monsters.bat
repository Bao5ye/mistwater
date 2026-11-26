@echo off
cd /d "%~dp0"
"G:\Blender\blender.exe" -b -P "%~dp0mistwater_monsters.py"
echo.
echo DONE. Check bag_*.png nurse_*.png boss_*.png
pause
