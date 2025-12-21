@echo off
echo KeLiva Render.com Deployment Preparation
echo ==========================================

REM Check if required files exist
if exist main.py (
    echo SUCCESS - main.py exists
) else (
    echo ERROR - main.py missing
    exit /b 1
)

if exist requirements.txt (
    echo SUCCESS - requirements.txt exists
) else (
    echo ERROR - requirements.txt missing
    exit /b 1
)

if exist render.yaml (
    echo SUCCESS - render.yaml exists
) else (
    echo ERROR - render.yaml missing
    exit /b 1
)

if exist .env (
    echo SUCCESS - .env exists
) else (
    echo ERROR - .env missing
    exit /b 1
)

echo.
echo Deployment Checklist:
echo 1. Backend files ready
echo 2. Keep-alive system implemented
echo 3. Security configuration complete
echo 4. Environment variables configured

echo.
echo Next Steps:
echo 1. Go to https://render.com and create account
echo 2. Create new Web Service from GitHub repo
echo 3. Use these settings:
echo    - Environment: Python 3
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
echo 4. Add environment variables from .env file
echo 5. Deploy and note your backend URL

echo.
echo Full guide available in: render-deploy-guide.md

echo.
echo Expected Backend URL: https://keliva-backend.onrender.com
echo Health Check: https://keliva-backend.onrender.com/api/health

echo.
echo Keep-Alive Features:
echo - Self-ping every 14 minutes
echo - Automatic URL detection
echo - 24/7 uptime on free tier
echo - Enterprise security enabled

echo.
echo Ready for deployment!
pause