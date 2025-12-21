# Simple KeLiva Deployment Script
Write-Host "🚀 KeLiva Deployment Starting..." -ForegroundColor Cyan

# Check wrangler
try {
    wrangler whoami
    Write-Host "✅ Wrangler authenticated" -ForegroundColor Green
} catch {
    Write-Host "❌ Please run: wrangler login" -ForegroundColor Red
    exit 1
}

# Deploy backend
Write-Host "🔧 Deploying backend..." -ForegroundColor Blue
wrangler pages deploy functions --project-name=keliva

# Deploy frontend
Write-Host "🎨 Deploying frontend..." -ForegroundColor Blue
if (Test-Path "frontend") {
    Set-Location frontend
    npm run build
    wrangler pages deploy dist --project-name=keliva-app
    Set-Location ..
}

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Backend: https://keliva.pages.dev" -ForegroundColor Blue
Write-Host "Frontend: https://keliva-app.pages.dev" -ForegroundColor Blue