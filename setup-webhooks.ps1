# KeLiva Webhook Setup Script
# This script helps configure Telegram and WhatsApp webhooks for different deployment scenarios

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("cloudflare", "ngrok")]
    [string]$Platform,
    
    [string]$NgrokUrl,
    [string]$TelegramToken,
    [string]$TwilioAccountSid,
    [string]$TwilioAuthToken,
    [switch]$Help
)

if ($Help) {
    Write-Host "KeLiva Webhook Setup Script" -ForegroundColor Cyan
    Write-Host "Usage: .\setup-webhooks.ps1 -Platform <cloudflare|ngrok> [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor Yellow
    Write-Host "  -Platform        Deployment platform (cloudflare or ngrok)" -ForegroundColor White
    Write-Host "  -NgrokUrl        Your ngrok URL (required for ngrok platform)" -ForegroundColor White
    Write-Host "  -TelegramToken   Your Telegram bot token (optional, will prompt if not provided)" -ForegroundColor White
    Write-Host "  -TwilioAccountSid Twilio Account SID (optional, for WhatsApp)" -ForegroundColor White
    Write-Host "  -TwilioAuthToken  Twilio Auth Token (optional, for WhatsApp)" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\setup-webhooks.ps1 -Platform cloudflare" -ForegroundColor Cyan
    Write-Host "  .\setup-webhooks.ps1 -Platform ngrok -NgrokUrl https://abc123.ngrok.io" -ForegroundColor Cyan
    exit 0
}

Write-Host "🔗 KeLiva Webhook Setup" -ForegroundColor Cyan
Write-Host "Platform: $Platform" -ForegroundColor Blue
Write-Host "========================" -ForegroundColor Cyan

# Set base URLs based on platform
if ($Platform -eq "cloudflare") {
    $baseUrl = "https://keliva.pages.dev"
    Write-Host "Using Cloudflare deployment URL: $baseUrl" -ForegroundColor Green
} elseif ($Platform -eq "ngrok") {
    if (-not $NgrokUrl) {
        $NgrokUrl = Read-Host "Enter your ngrok URL (e.g., https://abc123.ngrok.io)"
    }
    $baseUrl = $NgrokUrl.TrimEnd('/')
    Write-Host "Using ngrok URL: $baseUrl" -ForegroundColor Green
}

$telegramWebhookUrl = "$baseUrl/api/telegram/webhook"
$whatsappWebhookUrl = "$baseUrl/api/whatsapp/webhook"

# Get Telegram token if not provided
if (-not $TelegramToken) {
    Write-Host "`nTelegram Bot Configuration" -ForegroundColor Blue
    Write-Host "Get your bot token from @BotFather on Telegram" -ForegroundColor Yellow
    $TelegramToken = Read-Host "Enter your Telegram bot token"
}

if ($TelegramToken) {
    Write-Host "`n🤖 Setting up Telegram webhook..." -ForegroundColor Blue
    
    try {
        # Set webhook
        $telegramApiUrl = "https://api.telegram.org/bot$TelegramToken/setWebhook"
        $body = @{
            url = $telegramWebhookUrl
            allowed_updates = @("message", "callback_query")
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $telegramApiUrl -Method Post -Body $body -Headers $headers
        
        if ($response.ok) {
            Write-Host "✅ Telegram webhook set successfully!" -ForegroundColor Green
            Write-Host "   Webhook URL: $telegramWebhookUrl" -ForegroundColor White
        } else {
            Write-Host "❌ Failed to set Telegram webhook: $($response.description)" -ForegroundColor Red
        }
        
        # Verify webhook
        $getWebhookUrl = "https://api.telegram.org/bot$TelegramToken/getWebhookInfo"
        $webhookInfo = Invoke-RestMethod -Uri $getWebhookUrl -Method Get
        
        if ($webhookInfo.ok -and $webhookInfo.result.url -eq $telegramWebhookUrl) {
            Write-Host "✅ Webhook verification successful" -ForegroundColor Green
            Write-Host "   Pending updates: $($webhookInfo.result.pending_update_count)" -ForegroundColor White
        }
        
    } catch {
        Write-Host "❌ Error setting up Telegram webhook: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Manual setup command:" -ForegroundColor Yellow
        Write-Host "curl -X POST 'https://api.telegram.org/bot$TelegramToken/setWebhook' -d 'url=$telegramWebhookUrl'" -ForegroundColor Cyan
    }
}

# WhatsApp setup (optional)
Write-Host "`n📱 WhatsApp Setup (Optional)" -ForegroundColor Blue
$setupWhatsApp = Read-Host "Do you want to set up WhatsApp integration? (y/n)"

if ($setupWhatsApp -match "^[Yy]$") {
    if (-not $TwilioAccountSid) {
        Write-Host "Get your Twilio credentials from https://console.twilio.com/" -ForegroundColor Yellow
        $TwilioAccountSid = Read-Host "Enter your Twilio Account SID"
    }
    
    if (-not $TwilioAuthToken) {
        $TwilioAuthToken = Read-Host "Enter your Twilio Auth Token" -AsSecureString
        $TwilioAuthToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($TwilioAuthToken))
    }
    
    if ($TwilioAccountSid -and $TwilioAuthToken) {
        Write-Host "🔧 Setting up WhatsApp webhook..." -ForegroundColor Blue
        
        try {
            # Create basic auth header
            $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${TwilioAccountSid}:${TwilioAuthToken}"))
            $headers = @{
                "Authorization" = "Basic $auth"
                "Content-Type" = "application/x-www-form-urlencoded"
            }
            
            # Note: This is a simplified example. In practice, you'd need to configure
            # the WhatsApp sandbox or approved WhatsApp Business account
            Write-Host "⚠️  WhatsApp webhook configuration requires manual setup in Twilio Console:" -ForegroundColor Yellow
            Write-Host "1. Go to https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox" -ForegroundColor White
            Write-Host "2. Set webhook URL to: $whatsappWebhookUrl" -ForegroundColor Cyan
            Write-Host "3. Set HTTP method to: POST" -ForegroundColor White
            Write-Host "4. Save the configuration" -ForegroundColor White
            
        } catch {
            Write-Host "❌ Error with WhatsApp setup: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "⏭️  Skipping WhatsApp setup" -ForegroundColor Yellow
}

# Test the webhooks
Write-Host "`n🧪 Testing webhook endpoints..." -ForegroundColor Blue

# Test Telegram webhook endpoint
try {
    $response = Invoke-WebRequest -Uri $telegramWebhookUrl -Method Get -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Telegram webhook endpoint is accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Telegram webhook endpoint test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test WhatsApp webhook endpoint
try {
    $response = Invoke-WebRequest -Uri $whatsappWebhookUrl -Method Get -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ WhatsApp webhook endpoint is accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "⚠️  WhatsApp webhook endpoint test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n📋 Setup Summary" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan
Write-Host "Platform: $Platform" -ForegroundColor White
Write-Host "Base URL: $baseUrl" -ForegroundColor White
Write-Host "Telegram Webhook: $telegramWebhookUrl" -ForegroundColor Blue
Write-Host "WhatsApp Webhook: $whatsappWebhookUrl" -ForegroundColor Blue

Write-Host "`n🎯 Next Steps:" -ForegroundColor Green
Write-Host "1. Test your Telegram bot by sending /start" -ForegroundColor White
Write-Host "2. Check webhook logs: wrangler pages deployment tail --project-name=keliva" -ForegroundColor White
Write-Host "3. Monitor your bot at: https://t.me/your_bot_username" -ForegroundColor White

if ($Platform -eq "ngrok") {
    Write-Host "`n⚠️  Important for ngrok:" -ForegroundColor Yellow
    Write-Host "- Keep ngrok running while testing" -ForegroundColor White
    Write-Host "- Update webhooks if ngrok URL changes" -ForegroundColor White
    Write-Host "- Use Cloudflare for production deployment" -ForegroundColor White
}