@echo off
chcp 65001 >nul
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"

if not exist "%OLLAMA_EXE%" (
  echo Ollama n'est pas installe sur ce PC.
  echo Installez-le avant de relancer ce fichier.
  pause
  exit /b 1
)

echo Demarrage du moteur IA local...
"%OLLAMA_EXE%" list >nul 2>nul
if errorlevel 1 (
  start "" /b "%OLLAMA_EXE%" serve >nul 2>nul
  timeout /t 3 /nobreak >nul
)

echo Telechargement du modele Qwen 3 4B, environ 2,5 Go.
echo Cette operation doit etre effectuee sur un reseau qui autorise le registre Ollama.
"%OLLAMA_EXE%" pull qwen3:4b
if errorlevel 1 (
  echo.
  echo Le telechargement a ete bloque ou interrompu. Reessayez sur un reseau autorise.
  pause
  exit /b 1
)

echo.
echo L'IA locale est prete. Vous pouvez maintenant lancer Signal avec Lancer.cmd.
pause
