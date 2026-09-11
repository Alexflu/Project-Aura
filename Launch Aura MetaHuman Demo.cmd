@echo off
python "%~dp0tools\unreal_body.py" demo --metahuman
if errorlevel 1 pause
