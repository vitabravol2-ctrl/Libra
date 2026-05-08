@echo off
cd /d %~dp0
git pull
if errorlevel 1 goto :fail
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
if errorlevel 1 goto :fail
python main.py
if errorlevel 1 goto :fail
goto :end
:fail
echo Failed. Check errors above.
pause
:end
