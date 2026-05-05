@echo off
echo ============================================
echo    Smart Arbitrage Finder - Starting...
echo ============================================
echo.
echo Starting Backend (FastAPI) on port 8000...
start "Backend - Smart Arbitrage" cmd /k "cd backend && python -m uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend (React) on port 3000...
start "Frontend - Smart Arbitrage" cmd /k "cd frontend && npm start"

echo.
echo ============================================
echo    Both services starting...
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API Docs: http://localhost:8000/docs
echo ============================================
timeout /t 5 /nobreak >nul
start http://localhost:3000
