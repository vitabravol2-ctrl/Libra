Set-Location $PSScriptRoot
if (-not (Test-Path .venv)) { py -3 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if (Test-Path requirements.txt) {
    Write-Host '[INFO] requirements.txt found' -ForegroundColor Green
    pip install -r requirements.txt
} else {
    Write-Host '[WARNING] requirements.txt not found' -ForegroundColor Yellow
}
python main.py
if ($LASTEXITCODE -ne 0) { Write-Host 'Application exited with error.' -ForegroundColor Red }
Read-Host 'Press Enter to exit'
