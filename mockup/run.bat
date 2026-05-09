@echo off
cd /d "%~dp0.."
python -m mockup.main
if errorlevel 1 pause
