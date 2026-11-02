@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements.txt
if errorlevel 1 goto error
python app.py
if errorlevel 1 goto error
goto end
:error
echo.
echo Setup or startup failed. Check the error above and confirm Python 3.10-3.12 is installed.
pause
:end
endlocal
