#!/usr/bin/env pwsh
# Render.com Deployment Verification Script for KeLiva

Write-Host "🚀 KeLiva Render.com Deployment Verification" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Configuration
$RENDER_SERVICE_URL = "https://keliva-backend.onrender.com"
$MAX_RETRIES = 10
$RETRY_DELAY = 30

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Description,
        [int]$ExpectedStatus = 200
    )
    
    try {
        Write-Host "Testing $Description..." -ForegroundColor Yellow
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 30
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✅ $Description - OK (Status: $($response.StatusCode))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $Description - Unexpected status: $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ $Description - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Wait-ForDeployment {
    Write-Host "⏳ Waiting for Render.com deployment to be ready..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MAX_RETRIES; $i++) {
        Write-Host "Attempt $i/$MAX_RETRIES - Checking health endpoint..." -ForegroundColor Cyan
        
        if (Test-Endpoint "$RENDER_SERVICE_URL/health" "Health Check") {
            Write-Host "🎉 Deployment is ready!" -ForegroundColor Green
            return $true
        }
        
        if ($i -lt $MAX_RETRIES) {
            Write-Host "⏳ Waiting $RETRY_DELAY seconds before next attempt..." -ForegroundColor Yellow
            Start-Sleep -Seconds $RETRY_DELAY
        }
    }
    
    Write-Host "❌ Deployment failed to become ready after $MAX_RETRIES attempts" -ForegroundColor Red
    return $false
}

# Main verification process
Write-Host "🔍 Starting deployment verification..." -ForegroundColor Cyan

if (-not (Wait-ForDeployment)) {
    Write-Host "❌ Deployment verification failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n🧪 Running comprehensive endpoint tests..." -ForegroundColor Cyan

$tests = @(
    @{ Url = "$RENDER_SERVICE_URL/"; Description = "Root endpoint" },
    @{ Url = "$RENDER_SERVICE_URL/health"; Description = "Health check" },
    @{ Url = "$RENDER_SERVICE_URL/docs"; Description = "API documentation" },
    @{ Url = "$RENDER_SERVICE_URL/api/v1/status"; Description = "API status" }
)

$passedTests = 0
$totalTests = $tests.Count

foreach ($test in $tests) {
    if (Test-Endpoint $test.Url $test.Description) {
        $passedTests++
    }
    Start-Sleep -Seconds 2
}

Write-Host "`n📊 Test Results:" -ForegroundColor Cyan
Write-Host "Passed: $passedTests/$totalTests tests" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

if ($passedTests -eq $totalTests) {
    Write-Host "`n🎉 All tests passed! Deployment is successful." -ForegroundColor Green
    Write-Host "🌐 Backend URL: $RENDER_SERVICE_URL" -ForegroundColor Cyan
    Write-Host "📚 API Docs: $RENDER_SERVICE_URL/docs" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠️  Some tests failed. Check the logs above for details." -ForegroundColor Yellow
}

Write-Host "`n🔗 Useful Links:" -ForegroundColor Cyan
Write-Host "• Render Dashboard: https://dashboard.render.com/" -ForegroundColor White
Write-Host "• Service Logs: Check your Render dashboard for detailed logs" -ForegroundColor White
Write-Host "• API Documentation: $RENDER_SERVICE_URL/docs" -ForegroundColor White

Write-Host "`nVerification complete! 🚀" -ForegroundColor Green