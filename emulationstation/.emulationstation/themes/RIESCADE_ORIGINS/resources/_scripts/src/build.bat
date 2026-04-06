@echo off
REM Script para compilar Launch_Squash.py em um EXE com PyInstaller
REM Saída: arcadeDumpLauncher.exe

echo Compilando arcadeDumpLauncher.exe...
pyinstaller --onefile --noconsole --icon=window_icon_256.ico --name arcadeDumpLauncher .\arcadeDumpLauncher.py

echo.
echo Compilacao concluida!
echo Arquivo de saida: dist\arcadeDumpLauncher.exe
pause
