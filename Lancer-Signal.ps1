$ErrorActionPreference = 'Stop'

$appUrl = 'http://127.0.0.1:8765/'
$logOut = Join-Path $env:TEMP 'signal-veille-ia.log'
$logErr = Join-Path $env:TEMP 'signal-veille-ia-erreurs.log'
$edgeProfile = Join-Path $env:LOCALAPPDATA 'Signal Veille IA\Profil Edge'
$serverProcess = $null
$foundryLoaderProcess = $null
$foundryCommand = Get-Command foundry.exe -ErrorAction SilentlyContinue
$foundryAvailable = $null -ne $foundryCommand
$createdNew = $false
$singleInstance = New-Object System.Threading.Mutex($true, 'Local\SignalVeilleIA.Launcher', [ref]$createdNew)

function Test-SignalReady {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri ($appUrl + 'api/state') -TimeoutSec 2
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

function Test-SessionLifecycle {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri ($appUrl + 'api/session/heartbeat') `
      -Method Post -ContentType 'application/json' -Body '{}' -TimeoutSec 2
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

function Stop-OldSignalServer {
  foreach ($line in (netstat -ano -p tcp)) {
    if ($line -match '^\s*TCP\s+127\.0\.0\.1:8765\s+\S+\s+LISTENING\s+(\d+)\s*$') {
      $process = Get-Process -Id ([int]$Matches[1]) -ErrorAction SilentlyContinue
      if ($process -and $process.ProcessName -like 'python*') {
        Stop-Process -Id $process.Id -Force
        Start-Sleep -Milliseconds 500
        return
      }
      throw 'Le port 8765 est déjà utilisé par un autre programme.'
    }
  }
}

function Find-Edge {
  $candidates = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
  )
  return $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

function Invoke-FoundryCommand {
  param(
    [string[]]$Arguments,
    [int]$TimeoutMilliseconds = 8000
  )

  try {
    $process = Start-Process -FilePath $foundryCommand.Source -ArgumentList $Arguments `
      -WorkingDirectory $env:TEMP -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit($TimeoutMilliseconds)) {
      Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
  } catch {
    # Le processus Foundry peut déjà être arrêté : le nettoyage peut continuer.
  }
}

try {
  if (-not $createdNew) { throw 'Signal est déjà ouvert.' }
  $python = (Get-Command python.exe -ErrorAction Stop).Source
  $edge = Find-Edge
  if (-not $edge) { throw 'Microsoft Edge est introuvable sur ce PC.' }

  # Une ancienne version pouvait rester ouverte après la fermeture du
  # navigateur. On ne l'arrête que si le port appartient bien à Python.
  if ((Test-SignalReady) -and -not (Test-SessionLifecycle)) {
    Stop-OldSignalServer
  }

  if (-not (Test-SignalReady)) {
    $serverProcess = Start-Process -FilePath $python -ArgumentList 'server.py' `
      -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru `
      -RedirectStandardOutput $logOut -RedirectStandardError $logErr

    $ready = $false
    foreach ($attempt in 1..40) {
      Start-Sleep -Milliseconds 250
      if ($serverProcess.HasExited) {
        $details = if (Test-Path $logErr) { Get-Content -LiteralPath $logErr -Raw } else { '' }
        throw ('Signal ne peut pas démarrer. ' + $details)
      }
      if (Test-SignalReady) { $ready = $true; break }
    }
    if (-not $ready) { throw 'Le serveur Signal ne répond pas sur le port 8765.' }
  }

  if ($foundryAvailable) {
    $foundryLoaderProcess = Start-Process -FilePath 'powershell.exe' -WorkingDirectory $env:TEMP `
      -WindowStyle Hidden -PassThru -ArgumentList @(
      '-NoProfile', '-Command',
      "foundry server start | Out-Null; foundry model load phi-4-mini | Out-Null"
    )
  }

  New-Item -ItemType Directory -Force -Path $edgeProfile | Out-Null
  $edgeProcess = Start-Process -FilePath $edge -PassThru -ArgumentList @(
    "--app=$appUrl",
    "--user-data-dir=$edgeProfile",
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-mode'
  )

  # Le profil Edge dédié garantit que ce processus correspond à la fenêtre
  # Signal. Fermer cette fenêtre rend donc la main immédiatement.
  Wait-Process -Id $edgeProcess.Id
} catch {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show($_.Exception.Message, 'Signal — démarrage impossible', 'OK', 'Error') | Out-Null
} finally {
  # Le chargement est asynchrone. On l'interrompt avant d'arrêter Foundry pour
  # éviter qu'il ne redémarre le moteur après la fermeture de la fenêtre.
  if ($foundryLoaderProcess -and -not $foundryLoaderProcess.HasExited) {
    Stop-Process -Id $foundryLoaderProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($serverProcess -and -not $serverProcess.HasExited) {
    Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($foundryAvailable) {
    Invoke-FoundryCommand -Arguments @('model', 'unload', 'phi-4-mini')
    Invoke-FoundryCommand -Arguments @('server', 'stop')

    # Dernier recours si la commande d'arrêt de Foundry est bloquée.
    Get-Process -Name 'foundrylocald' -ErrorAction SilentlyContinue |
      Stop-Process -Force -ErrorAction SilentlyContinue
  }
  if ($createdNew) { $singleInstance.ReleaseMutex() }
  $singleInstance.Dispose()
}
