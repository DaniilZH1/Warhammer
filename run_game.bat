@echo off
set "PYTHON_EXE=C:\Users\Bomj_\AppData\Local\Programs\Python\Python313\python.exe"

cd /d "%~dp0"

if not exist "%PYTHON_EXE%" (
    echo Python was not found:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%~dp0main.py"

if errorlevel 1 (
    echo.
    echo Game exited with an error.
    pause
)
