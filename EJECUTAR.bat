@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Software FJ
if not exist software_fj.py (
  echo [PROBLEMA] No encuentro software_fj.py junto a este archivo.
  echo Si abriste el .zip, primero haz clic derecho - Extraer todo.
  goto fin
)
where py >nul 2>nul
if %errorlevel%==0 (
  py software_fj.py
  goto fin
)
where python >nul 2>nul
if %errorlevel%==0 (
  python software_fj.py
  goto fin
)
echo [PROBLEMA] Python no esta instalado en este computador.
echo Instalelo desde https://www.python.org/downloads/ marcando "Add Python to PATH".
:fin
echo.
echo ---- Programa finalizado. Puede cerrar esta ventana ----
pause
