# Railway Deployment Script for KeLiva Python Backend
# This will deploy your sophisticated Python backend in minutes

Write-Host "🚀 KeLiva Railway Deployment" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Yellow

# Check if Railway CLI is installed
try {
    railway --version | Out-Null
    Write-Host "✅ Railway CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Railway CLI not found. Installing..." -ForegroundColor Red
    npm install -g @railway/cli
    Write-Host "✅ Railway CLI installed" -ForegroundColor Green
}

# Create railway.json configuration
$railwayConfig = @{
    "build" = @{
        "builder" = "NIXPACKS"
    }
    "deploy" = @{
        "startCommand" = "cd functions && python -m uvicorn main:app --host 0.0.0.0 --port `$PORT"
        "healthcheckPath" = "/api/health"
    }
} | ConvertTo-Json -Depth 3

$railwayConfig | Out-File -FilePath "railway.json" -Encoding UTF8
Write-Host "✅ Created railway.json" -ForegroundColor Green

# Create Procfile for Railway
"web: cd functions && python -m uvicorn main:app --host 0.0.0.0 --port `$PORT" | Out-File -FilePath "Procfile" -Encoding UTF8
Write-Host "✅ Created Procfile" -ForegroundColor Green

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Run: railway login" -ForegroundColor Yellow
Write-Host "2. Run: railway up" -ForegroundColor Yellow
Write-Host "3. Set environment variables:" -ForegroundColor Yellow
Write-Host "   railway variables set GROQ_API_KEY=your_key" -ForegroundColor White
Write-Host "   railway variables set TELEGRAM_BOT_TOKEN=your_token" -ForegroundColor White
Write-Host "   railway variables set ELEVENLABS_API_KEY=your_key" -ForegroundColor White

Write-Host "`n⚡ Your app will be live in 2-3 minutes!" -ForegroundColor Green
Write-Host "🌐 Railway will give you a URL like: https://keliva-production.up.railway.app" -ForegroundColor Cyan