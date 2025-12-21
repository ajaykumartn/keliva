# KeLiva Render Deployment Verification Script
param(
    [Parameter(Mandatory=$true)]
    [string]$BackendUrl
)

Write-Host "Verifying KeLiva Deployment on Render.com" -ForegroundColor Green
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Green

# Test endpoints
$endpoints = @(
    @{ Path = "/api/health"; Name = "Health Check" },
    @{ Path = "/"; Name = "Root Endpoint" },
    @{ Path = "/api/test"; Name = "Test Endpoint" }
)

$allPassed = $true

foreach ($endpoint in $endpoints) {
    $url = "$BackendUrl$($endpoint.Path)"
    Write-Host ""
    Write-Host "Testing $($endpoint.Name): $url" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 30
        Write-Host "SUCCESS - $($endpoint.Name)" -ForegroundColor Green
        
        if ($endpoint.Path -eq "/api/health") {
            Write-Host "   Status: $($response.status)" -ForegroundColor Gray
            Write-Host "   Database: $($response.database)" -ForegroundColor Gray
        }
        
        if ($endpoint.Path -eq "/api/test") {
            Write-Host "   Message: $($response.message)" -ForegroundColor Gray
            Write-Host "   Security: $($response.security)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "FAILED - $($endpoint.Name)" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""
Write-Host "Security Features Check:" -ForegroundColor Yellow

# Check security headers
try {
    $headers = Invoke-WebRequest -Uri "$BackendUrl/api/health" -Method GET -TimeoutSec 30
    
    $securityHeaders = @(
        "X-Content-Type-Options",
        "X-Frame-Options", 
        "X-XSS-Protection",
        "Strict-Transport-Security"
    )
    
    foreach ($header in $securityHeaders) {
        if ($headers.Headers[$header]) {
            Write-Host "SUCCESS - $header present" -ForegroundColor Green
        } else {
            Write-Host "MISSING - $header" -ForegroundColor Red
        }
    }
}
catch {
    Write-Host "Could not check security headers" -ForegroundColor Red
}

Write-Host ""
Write-Host "Keep-Alive System Check:" -ForegroundColor Yellow
Write-Host "The keep-alive system will start automatically after deployment."
Write-Host "Check your Render logs for 'Keep-alive ping successful' messages."

Write-Host ""
if ($allPassed) {
    Write-Host "Deployment Verification PASSED!" -ForegroundColor Green
    Write-Host "Your KeLiva backend is ready for production use." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Update frontend/.env with: VITE_API_URL=$BackendUrl"
    Write-Host "2. Deploy frontend to Vercel"
    Write-Host "3. Set up UptimeRobot monitoring (optional)"
} else {
    Write-Host "Deployment Verification FAILED!" -ForegroundColor Red
    Write-Host "Please check the errors above and redeploy." -ForegroundColor Red
}

Write-Host ""
Write-Host "Monitoring URLs:" -ForegroundColor Magenta
Write-Host "Health Check: $BackendUrl/api/health"
Write-Host "API Test: $BackendUrl/api/test"