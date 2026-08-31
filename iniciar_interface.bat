@echo off
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto usar_python

py -3 app_gui.py
goto verificar

:usar_python
python app_gui.py

:verificar
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar. Verifique se o Python 3 esta instalado.
    pause
)
