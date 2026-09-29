@echo off
chcp 65001 >nul

where foundry >nul 2>nul
if errorlevel 1 (
  echo Installation du moteur Microsoft Foundry Local...
  winget install --id Microsoft.FoundryLocal --exact --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo L'installation de Foundry Local a echoue.
    pause
    exit /b 1
  )
)

echo Telechargement de Phi-4 Mini, environ 2,2 Go...
foundry model download phi-4-mini
if errorlevel 1 (
  echo.
  echo Le telechargement a ete interrompu. Verifiez la connexion puis reessayez.
  pause
  exit /b 1
)

echo Demarrage du moteur et chargement du modele...
foundry server start
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "foundry model load phi-4-mini | Out-Null"

echo.
echo L'IA locale est installee. Le premier chargement peut prendre plusieurs minutes.
echo Vous pouvez lancer Signal avec Lancer.cmd.
pause
