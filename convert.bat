@echo off
if "%~1"=="" (
    node "%~dp0tui.js"
    exit /b
)
python "%~dp0generate.py" %*