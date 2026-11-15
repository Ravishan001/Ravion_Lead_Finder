@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo.
echo   Ravion Lead Finder app eka start wenawa...
echo   Browser eka auto open wenawa. Me black window eka close karanna epa.
echo   App eka nawaththanna: me window eka close karanna.
echo.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 5; Start-Process http://localhost:8501"
python -m streamlit run app.py --server.port 8501
pause
