@echo off
cd /d "%~dp0"
REM Web UI + serial: python app.py COM3
REM Debug only (no ESP32): python app.py --no-serial
python app.py %*
