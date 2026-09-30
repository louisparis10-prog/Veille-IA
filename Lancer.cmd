@echo off
start "Signal" /b powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0Lancer-Signal.ps1"
