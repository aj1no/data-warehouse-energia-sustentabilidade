$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DepsDir = Join-Path $ProjectRoot ".deps"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

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
    throw "Nenhum Python com pip foi encontrado. Instale Python 3.10+ ou selecione um interpretador Python válido no VSCode."
}

if (-not (Test-Path $DepsDir)) {
    New-Item -ItemType Directory -Path $DepsDir | Out-Null
}

$PreviousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = $DepsDir

& $Python -c "import duckdb, pandas" *> $null
$DependenciesOk = $LASTEXITCODE -eq 0

if (-not $DependenciesOk) {
    & $Python -m pip install --upgrade --target $DepsDir -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar dependências em .deps."
    }
}

& $Python (Join-Path $ProjectRoot "run_all.py")
$env:PYTHONPATH = $PreviousPythonPath
