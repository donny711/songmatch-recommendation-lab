@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import streamlit" >nul 2>nul
  if not errorlevel 1 (
    ".venv\Scripts\python.exe" -m streamlit run app.py --global.developmentMode false
    exit /b
  )
)
if exist ".packages\streamlit" set "PYTHONPATH=%CD%\.packages"
python -m streamlit run app.py --global.developmentMode false
