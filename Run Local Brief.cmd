@echo off
setlocal
set "BRIEF_EXIT=0"
cd /d "%~dp0"
title RetailPulse - Local Sales Brief

echo RetailPulse - Local Sales Brief
echo.
echo This uses Qwen2.5 through Ollama on this computer.
echo No API key or paid service is required.
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python and try again.
    goto :failed
)

ollama --version >nul 2>&1
if errorlevel 1 (
    echo Ollama was not found. Install Ollama from https://ollama.com/download
    goto :failed
)

ollama list 2>nul | findstr /I /C:"qwen2.5:1.5b" >nul
if errorlevel 1 (
    echo The local model is missing.
    echo Run: ollama pull qwen2.5:1.5b
    goto :failed
)

python src\generate_weekly_brief.py --provider ollama --model qwen2.5:1.5b
if errorlevel 1 goto :failed

echo.
echo Brief created successfully:
echo outputs\weekly_sales_brief.md
goto :finish

:failed
echo.
echo The brief was not created.
set "BRIEF_EXIT=1"

:finish
if /I not "%~1"=="--no-pause" pause
exit /b %BRIEF_EXIT%
