@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Preparando o ambiente do projeto pela primeira vez...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.12 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto falha
)

if not exist ".venv\instalado.ok" (
    echo Instalando as dependencias. Isto pode levar alguns minutos...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto falha
    type nul > ".venv\instalado.ok"
)

".venv\Scripts\python.exe" app_gui.py
if errorlevel 1 goto falha
exit /b 0

:falha
echo.
echo Nao foi possivel iniciar. Confira se o Python 3.12 e o pip estao instalados.
pause
exit /b 1
