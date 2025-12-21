# KeLiva Cloudflare Deployment Script (PowerShell)
param(
    [switch]$SkipSecrets,
    [switch]$SkipDatabase,
    [switch]$Help
)

if ($Help) {
    Write-Host "KeLiva Cloudflare Deployment Script" -ForegroundColor Cyan
    Write-Host "Usage: .\deploy.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -SkipSecrets    Skip secrets verification step" -ForegroundColor White
    Write-Host "  -SkipDatabase   Skip database creation step" -ForegroundColor White
    Write-Host "  -Help           Show this help message" -ForegroundColor White
    exit 0
}

Write-Host "🚀 KeLiva Cloudflare Deployment Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if wrangler is installed
try {
    $null = Get-Command wrangler -ErrorAction Stop
    Write-Host "✅ Wrangler CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Wrangler CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "npm install -g wrangler" -ForegroundColor Yellow
    exit 1
}

# Check wrangler authentication
Write-Host "📋 Checking wrangler authentication..." -ForegroundColor Blue
try {
    $whoami = wrangler whoami 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Not authenticated"
    }
    Write-Host "✅ Wrangler authentication verified" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Not logged in to Cloudflare. Please run:" -ForegroundColor Yellow
    Write-Host "wrangler login" -ForegroundColor White
    exit 1
}

# Function to check if database exists
function Test-Database {
    try {
        $null = wrangler d1 info keliva-db 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Step 1: Create D1 database if it doesn't exist
if (-not $SkipDatabase) {
    Write-Host "`n📊 Checking D1 database..." -ForegroundColor Blue
    if (Test-Database) {
        Write-Host "✅ Database 'keliva-db' already exists" -ForegroundColor Green
    } else {
        Write-Host "📊 Creating D1 database..." -ForegroundColor Yellow
        wrangler d1 create keliva-db
        Write-Host "⚠️  IMPORTANT: Please update wrangler.toml with the database_id from above!" -ForegroundColor Red
        Write-Host "Press Enter after updating wrangler.toml..." -ForegroundColor Yellow
        Read-Host
    }
}

# Step 2: Apply database schema
Write-Host "`n🗄️  Applying database schema..." -ForegroundColor Blue
if (Test-Path "schema.sql") {
    wrangler d1 execute keliva-db --file=schema.sql
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database schema applied" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to apply database schema" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ schema.sql not found" -ForegroundColor Red
    exit 1
}

# Step 3: Check secrets
if (-not $SkipSecrets) {
    Write-Host "`n🔐 Checking environment secrets..." -ForegroundColor Blue
    Write-Host "Please ensure you have set the following secrets:" -ForegroundColor White
    Write-Host "- GROQ_API_KEY (get from console.groq.com)" -ForegroundColor White
    Write-Host "- TELEGRAM_BOT_TOKEN (get from @BotFather)" -ForegroundColor White
    Write-Host ""
    Write-Host "Set them with:" -ForegroundColor White
    Write-Host "wrangler secret put GROQ_API_KEY" -ForegroundColor Yellow
    Write-Host "wrangler secret put TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    Write-Host ""
    $secretsReady = Read-Host "Have you set both secrets? (y/n)"
    if ($secretsReady -notmatch "^[Yy]$") {
        Write-Host "Please set the secrets and run this script again." -ForegroundColor Yellow
        exit 1
    }
}

# Step 4: Deploy backend
Write-Host "`n🔧 Deploying backend to Cloudflare Pages..." -ForegroundColor Blue
wrangler pages deploy functions --project-name=keliva
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend deployed to: https://keliva.pages.dev" -ForegroundColor Green
} else {
    Write-Host "❌ Backend deployment failed" -ForegroundColor Red
    exit 1
}

# Step 5: Build and deploy frontend
Write-Host "`n🎨 Building and deploying frontend..." -ForegroundColor Blue
if (Test-Path "frontend") {
    Push-Location frontend
    
    # Install dependencies if node_modules doesn't exist
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
            Pop-Location
            exit 1
        }
    }
    
    # Build frontend
    Write-Host "🔨 Building frontend..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Deploy frontend
    Write-Host "🚀 Deploying frontend..." -ForegroundColor Yellow
    wrangler pages deploy dist --project-name=keliva-app
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend deployed to: https://keliva-app.pages.dev" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend deployment failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
} else {
    Write-Host "❌ Frontend directory not found" -ForegroundColor Red
    exit 1
}

# Step 6: Test deployment
Write-Host "`n🧪 Testing deployment..." -ForegroundColor Blue
Write-Host "Testing health endpoint..." -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "https://keliva.pages.dev/api/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend health check passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Backend responded with status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Backend might still be starting up..." -ForegroundColor Yellow
}

# Step 7: Webhook setup
Write-Host "`n🤖 Setting up webhooks..." -ForegroundColor Blue
$setupWebhooks = Read-Host "Do you want to set up Telegram webhook now? (y/n)"

if ($setupWebhooks -match "^[Yy]$") {
    Write-Host "Running webhook setup script..." -ForegroundColor Yellow
    try {
        & ".\setup-webhooks.ps1" -Platform cloudflare
    } catch {
        Write-Host "❌ Webhook setup script failed. You can run it manually later:" -ForegroundColor Red
        Write-Host ".\setup-webhooks.ps1 -Platform cloudflare" -ForegroundColor Cyan
    }
} else {
    Write-Host "⏭️  Skipping webhook setup. Run this later:" -ForegroundColor Yellow
    Write-Host ".\setup-webhooks.ps1 -Platform cloudflare" -ForegroundColor Cyan
}

# Summary
Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host "Backend:  https://keliva.pages.dev" -ForegroundColor Blue
Write-Host "Frontend: https://keliva-app.pages.dev" -ForegroundColor Blue
Write-Host "API Docs: https://keliva.pages.dev/docs" -ForegroundColor Blue
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Set up Telegram webhook (commands shown above)" -ForegroundColor White
Write-Host "2. Test your bot by sending /start" -ForegroundColor White
Write-Host "3. Visit the frontend to test the web interface" -ForegroundColor White
Write-Host ""
Write-Host "Your KeLiva app is now running on Cloudflare's global edge network! 🌍" -ForegroundColor Green