@echo off
cd /d "%~dp0"
python -m PyInstaller --noconfirm --onefile --windowed --name "WhaleDesktopPet" --icon "expressions\DSniang1.png" whale_pet.py
echo.
echo 打包完成：dist\WhaleDesktopPet.exe
pause
