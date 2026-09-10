@echo off
python "%~dp0tools\unreal_body.py" demo
if errorlevel 1 pause
