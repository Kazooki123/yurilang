@echo off
:: YuriLang Windows Installer
:: "She found her way in. Now so can you. 🪟"
:: Double-click to install, or run from cmd

title YuriLang Installer

echo.
echo   ╔══════════════════════════════════════╗
echo   ║         Y U R I L A N G              ║
echo   ║   "Yuring Complete since 2026"       ║
echo   ╚══════════════════════════════════════╝
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found!
    echo   Please install Python 3.14+ from https://python.org
    pause
    exit /b 1
)

echo   Running installer...
echo.
python install.py %*

if errorlevel 1 (
    echo.
    echo   [ERROR] Installation failed.
    echo   Try running as Administrator or use:
    echo   python install.py --user
    pause
    exit /b 1
)

pause
