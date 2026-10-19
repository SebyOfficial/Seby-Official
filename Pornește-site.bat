@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
) else (
  where python >nul 2>nul
  if %errorlevel% neq 0 (
    echo Python nu este instalat. Instaleaza Python 3, apoi porneste din nou acest fisier.
    pause
    exit /b 1
  )
  python server.py
)
pause
