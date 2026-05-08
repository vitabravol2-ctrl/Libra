Set-Location $PSScriptRoot
if (-not (Test-Path .venv)) { py -3 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
if ($LASTEXITCODE -ne 0) { Write-Host 'Application exited with error.' -ForegroundColor Red }
Read-Host 'Press Enter to exit'
