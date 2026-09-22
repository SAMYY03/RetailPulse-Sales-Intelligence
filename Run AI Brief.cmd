@echo off
cd /d "%~dp0"
echo RetailPulse - Free Offline Brief
echo Creates a template summary locally. No API key or payment required.
echo.
python src\generate_insights.py --preview
echo.
pause
