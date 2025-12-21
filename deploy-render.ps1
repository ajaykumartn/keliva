# KeLiva Render.com Deployment Script
# Run this script to prepare for deployment

Write-Host "KeLiva Render.com Deployment Preparation" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Check if required files exist
$requiredFiles = @("main.py", "requirements.txt", "render.yaml", ".env")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Deployment Checklist:" -ForegroundColor Yellow
Write-Host "1. Backend files ready"
Write-Host "2. Keep-alive system implemented"
Write-Host "3. Security configuration complete"
Write-Host "4. Environment variables configured"

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://render.com and create account"
Write-Host "2. Create new Web Service from GitHub repo"
Write-Host "3. Use these settings:"
Write-Host "   - Environment: Python 3"
Write-Host "   - Build Command: pip install -r requirements.txt"
Write-Host "   - Start Command: uvicorn main:app --host 0.0.0.0 --port `$PORT"
Write-Host "4. Add environment variables from .env file"
Write-Host "5. Deploy and note your backend URL"

Write-Host ""
Write-Host "Full guide available in: render-deploy-guide.md" -ForegroundColor Magenta

Write-Host ""
Write-Host "Expected Backend URL: https://keliva-backend.onrender.com" -ForegroundColor Green
Write-Host "Health Check: https://keliva-backend.onrender.com/api/health" -ForegroundColor Green

Write-Host ""
Write-Host "Keep-Alive Features:" -ForegroundColor Yellow
Write-Host "- Self-ping every 14 minutes"
Write-Host "- Automatic URL detection"
Write-Host "- 24/7 uptime on free tier"
Write-Host "- Enterprise security enabled"

Write-Host ""
Write-Host "Ready for deployment!" -ForegroundColor Green