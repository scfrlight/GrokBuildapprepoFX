@echo off
setlocal EnableExtensions
REM BotModuleProject1 platform kernel — Windows launcher.
REM Does not send orders. Live trading is disabled.
cd /d "%~dp0\..\.."

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

if "%LOG_DIR%"=="" set "LOG_DIR=logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

python -m botmoduleproject1 %* 1>>"%LOG_DIR%\platform.out.log" 2>>"%LOG_DIR%\platform.err.log"
exit /b %ERRORLEVEL%
