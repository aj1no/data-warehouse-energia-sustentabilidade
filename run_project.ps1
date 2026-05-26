$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONUSERBASE = Join-Path $ProjectRoot ".tmp\pyuser"

function Test-PythonWithPip {
    param([string]$PythonCommand)

    try {
        & $PythonCommand -m pip --version *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

$Python = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    if (Test-PythonWithPip "python") {
        $Python = "python"
    }
}

if (-not $Python -and (Test-Path $BundledPython)) {
    if (Test-PythonWithPip $BundledPython) {
        $Python = $BundledPython
    }
}

if (-not $Python) {
    throw "Nenhum Python com pip foi encontrado. Instale Python 3.10+."
}

Write-Host "Instalando dependencias de $Requirements..."
& $Python -m pip install -r $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar dependencias."
}

Write-Host "Executando o pipeline do DW..."
& $Python (Join-Path $ProjectRoot "run_all.py")
