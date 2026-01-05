# KeLiva Telegram Webhook Setup Script

$botToken = "8400809403:AAGulVzMo4raH8ITngvzdDstGKgvBRn5Dmw"
$webhookUrl = "https://keliva.onrender.com/api/telegram/webhook"

Write-Host "Setting up Telegram webhook for KeLiva..." -ForegroundColor Green
Write-Host "Bot Token: $botToken" -ForegroundColor Yellow
Write-Host "Webhook URL: $webhookUrl" -ForegroundColor Yellow

# Wait for deployment to complete
Write-Host ""
Write-Host "Checking if webhook endpoint is ready..." -ForegroundColor Cyan

$maxAttempts = 10
$attempt = 1

while ($attempt -le $maxAttempts) {
    try {
        Write-Host "Attempt $attempt/$maxAttempts - Testing webhook endpoint..." -ForegroundColor Gray
        $response = Invoke-RestMethod -Uri $webhookUrl -Method Get -TimeoutSec 10
        Write-Host "SUCCESS - Webhook endpoint is ready!" -ForegroundColor Green
        break
    }
    catch {
        Write-Host "Endpoint not ready yet, waiting 30 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        $attempt++
    }
}

if ($attempt -gt $maxAttempts) {
    Write-Host "ERROR - Webhook endpoint not ready after $maxAttempts attempts" -ForegroundColor Red
    Write-Host "Please check your Render deployment and try again later." -ForegroundColor Red
    exit 1
}

# Set the webhook
Write-Host ""
Write-Host "Setting Telegram webhook..." -ForegroundColor Cyan

try {
    $setWebhookUrl = "https://api.telegram.org/bot$botToken/setWebhook"
    $body = @{
        url = $webhookUrl
    } | ConvertTo-Json

    $result = Invoke-RestMethod -Uri $setWebhookUrl -Method Post -Body $body -ContentType "application/json"
    
    if ($result.ok) {
        Write-Host "SUCCESS - Telegram webhook set successfully!" -ForegroundColor Green
        Write-Host "Description: $($result.description)" -ForegroundColor Gray
    } else {
        Write-Host "ERROR - Failed to set webhook: $($result.description)" -ForegroundColor Red
    }
}
catch {
    Write-Host "ERROR - Failed to set webhook: $($_.Exception.Message)" -ForegroundColor Red
}

# Verify the webhook
Write-Host ""
Write-Host "Verifying webhook setup..." -ForegroundColor Cyan

try {
    $getWebhookUrl = "https://api.telegram.org/bot$botToken/getWebhookInfo"
    $info = Invoke-RestMethod -Uri $getWebhookUrl -Method Get
    
    Write-Host "Webhook Info:" -ForegroundColor Yellow
    Write-Host "  URL: $($info.result.url)" -ForegroundColor Gray
    Write-Host "  Has Custom Certificate: $($info.result.has_custom_certificate)" -ForegroundColor Gray
    Write-Host "  Pending Update Count: $($info.result.pending_update_count)" -ForegroundColor Gray
    Write-Host "  Last Error Date: $($info.result.last_error_date)" -ForegroundColor Gray
    Write-Host "  Last Error Message: $($info.result.last_error_message)" -ForegroundColor Gray
}
catch {
    Write-Host "ERROR - Failed to get webhook info: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Setup complete! Your Telegram bot is ready to receive messages." -ForegroundColor Green
Write-Host "Test by messaging your bot on Telegram." -ForegroundColor Cyan