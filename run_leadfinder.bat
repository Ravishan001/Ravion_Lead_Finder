@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo Ravion Lead Finder
set /p CITIES=Cities (eg: Kuliyapitiya Negombo) [Enter = default]: 
set /p CATS=Categories (eg: salon beauty_salon) [Enter = default]: 
set /p TIERS=Tiers (eg: A B) [Enter = all]: 
set ARGS=
if not "%CITIES%"=="" set ARGS=%ARGS% --cities %CITIES%
if not "%CATS%"=="" set ARGS=%ARGS% --categories %CATS%
if not "%TIERS%"=="" set ARGS=%ARGS% --tiers %TIERS%
python leadfinder.py %ARGS%
start "" output
pause
