@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.11 ou plus recent est necessaire pour lancer Signal.
  echo Telechargement : https://www.python.org/downloads/
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3, n) for n in range(11, 100)] else 1)"
if errorlevel 1 (
  echo Votre version de Python est trop ancienne. Installez Python 3.11 ou plus recent.
  pause
  exit /b 1
)

echo Demarrage de Signal en local...
echo L'application sera disponible sur http://127.0.0.1:8765
where foundry >nul 2>nul
if not errorlevel 1 (
  start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "foundry server start | Out-Null; $loaded=foundry model list --loaded --output json | ConvertFrom-Json; if (-not ($loaded.models.alias -contains 'phi-4-mini')) { foundry model load phi-4-mini | Out-Null }"
)
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Milliseconds 1200; Start-Process 'http://127.0.0.1:8765'"
python server.py
echo.
echo Signal est arrete. Relancez ce fichier pour rouvrir l'application.
pause
