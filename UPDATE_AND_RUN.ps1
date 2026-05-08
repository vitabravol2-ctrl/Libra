Set-Location $PSScriptRoot
git pull
if ($LASTEXITCODE -ne 0) { Write-Host 'git pull failed' -ForegroundColor Red; Read-Host 'Press Enter to exit'; exit 1 }
if (-not (Test-Path .venv)) { py -3 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host 'Tests failed. App not started.' -ForegroundColor Red; Read-Host 'Press Enter to exit'; exit 1 }
python main.py
if ($LASTEXITCODE -ne 0) { Write-Host 'Application failed.' -ForegroundColor Red }
Read-Host 'Press Enter to exit'
