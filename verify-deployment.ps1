# KeLiva Deployment Verification Script
# This script tests all endpoints and services after deployment

Write-Host "🧪 KeLiva Deployment Verification" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$backendUrl = "https://keliva.pages.dev"
$frontendUrl = "https://keliva-app.pages.dev"
$errors = @()

# Test 1: Backend Health Check
Write-Host "`n1. Testing backend health..." -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "$backendUrl/api/health" -TimeoutSec 10
    if ($response.status -eq "ok") {
        Write-Host "✅ Backend health check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend health check failed: $($response.message)" -ForegroundColor Red
        $errors += "Backend health check failed"
    }
} catch {
    Write-Host "❌ Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
    $errors += "Backend unreachable"
}

# Test 2: Database Connection
Write-Host "`n2. Testing database connection..." -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "$backendUrl/api/test-db" -TimeoutSec 10
    if ($response.status -eq "ok") {
        Write-Host "✅ Database connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Database connection failed: $($response.message)" -ForegroundColor Red
        $errors += "Database connection failed"
    }
} catch {
    Write-Host "❌ Database test failed: $($_.Exception.Message)" -ForegroundColor Red
    $errors += "Database test failed"
}

# Test 3: Frontend Accessibility
Write-Host "`n3. Testing frontend accessibility..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend is accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend returned status: $($response.StatusCode)" -ForegroundColor Red
        $errors += "Frontend not accessible"
    }
} catch {
    Write-Host "❌ Frontend test failed: $($_.Exception.Message)" -ForegroundColor Red
    $errors += "Frontend unreachable"
}

# Test 4: API Documentation
Write-Host "`n4. Testing API documentation..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$backendUrl/docs" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API documentation is accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ API docs returned status: $($response.StatusCode)" -ForegroundColor Red
        $errors += "API docs not accessible"
    }
} catch {
    Write-Host "❌ API docs test failed: $($_.Exception.Message)" -ForegroundColor Red
    $errors += "API docs unreachable"
}

# Test 5: CORS Configuration
Write-Host "`n5. Testing CORS configuration..." -ForegroundColor Blue
try {
    $headers = @{
        "Origin" = $frontendUrl
        "Access-Control-Request-Method" = "POST"
        "Access-Control-Request-Headers" = "Content-Type"
    }
    $response = Invoke-WebRequest -Uri "$backendUrl/api/health" -Method Options -Headers $headers -UseBasicParsing -TimeoutSec 10
    if ($response.Headers["Access-Control-Allow-Origin"]) {
        Write-Host "✅ CORS is properly configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  CORS headers not found (might still work)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  CORS test inconclusive: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test 6: Wrangler Configuration
Write-Host "`n6. Checking wrangler configuration..." -ForegroundColor Blue
if (Test-Path "wrangler.toml") {
    $config = Get-Content "wrangler.toml" -Raw
    if ($config -match "REPLACE_WITH_YOUR_DATABASE_ID") {
        Write-Host "❌ Database ID not updated in wrangler.toml" -ForegroundColor Red
        $errors += "Database ID not configured"
    } else {
        Write-Host "✅ Wrangler configuration looks good" -ForegroundColor Green
    }
} else {
    Write-Host "❌ wrangler.toml not found" -ForegroundColor Red
    $errors += "Wrangler config missing"
}

# Test 7: Environment Secrets
Write-Host "`n7. Checking environment secrets..." -ForegroundColor Blue
try {
    $secrets = wrangler secret list 2>$null
    if ($secrets -match "GROQ_API_KEY" -and $secrets -match "TELEGRAM_BOT_TOKEN") {
        Write-Host "✅ Required secrets are configured" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing required secrets" -ForegroundColor Red
        Write-Host "Required: GROQ_API_KEY, TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
        $errors += "Missing secrets"
    }
} catch {
    Write-Host "⚠️  Could not verify secrets: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n📊 Verification Summary" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

if ($errors.Count -eq 0) {
    Write-Host "🎉 All tests passed! Your deployment is ready." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "1. Set up Telegram webhook:" -ForegroundColor White
    Write-Host "   curl -X POST 'https://api.telegram.org/botYOUR_TOKEN/setWebhook' -d 'url=$backendUrl/api/telegram/webhook'" -ForegroundColor Cyan
    Write-Host "2. Test your bot by sending /start" -ForegroundColor White
    Write-Host "3. Visit $frontendUrl to test the web interface" -ForegroundColor White
} else {
    Write-Host "❌ Found $($errors.Count) issue(s):" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "   • $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please fix these issues before proceeding." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Useful URLs:" -ForegroundColor White
Write-Host "Backend:     $backendUrl" -ForegroundColor Blue
Write-Host "Frontend:    $frontendUrl" -ForegroundColor Blue
Write-Host "API Docs:    $backendUrl/docs" -ForegroundColor Blue
Write-Host "Health:      $backendUrl/api/health" -ForegroundColor Blue
Write-Host "DB Test:     $backendUrl/api/test-db" -ForegroundColor Blue