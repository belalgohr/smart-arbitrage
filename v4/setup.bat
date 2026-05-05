@echo off
echo ============================================
echo    Smart Arbitrage Finder - Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! Install from python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Node
node --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found! Install from nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo --- Setting up Backend ---
cd backend
pip install -r requirements.txt
IF NOT EXIST .env (
    copy .env.example .env
    echo [OK] Created .env file - Edit it to add your API keys!
)
cd ..

echo.
echo --- Setting up Frontend ---
cd frontend
call npm install
cd ..

echo.
echo ============================================
echo    Setup Complete!
echo.
echo    To start the app, run: start.bat
echo    Then open: http://localhost:3000
echo.
echo    IMPORTANT: Edit backend\.env to add:
echo    - GROQ_API_KEY (free from console.groq.com)
echo    - EBAY API keys (when ready)
echo ============================================
pause
