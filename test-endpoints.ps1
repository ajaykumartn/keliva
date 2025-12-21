# Test KeLiva API Endpoints
$baseUrl = "https://ceda27ad.keliva.pages.dev"

Write-Host "Testing KeLiva API Endpoints..." -ForegroundColor Green
Write-Host "Base URL: $baseUrl" -ForegroundColor Yellow

# Test Health Endpoint
Write-Host "`n1. Testing Health Endpoint..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/api/health"
    Write-Host "✅ Health: $($health.status)" -ForegroundColor Green
    Write-Host "   Services: DB=$($health.services.database), Groq=$($health.services.groq_api), Telegram=$($health.services.telegram_bot)"
} catch {
    Write-Host "❌ Health endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Grammar Check
Write-Host "`n2. Testing Grammar Check..." -ForegroundColor Cyan
try {
    $grammar = Invoke-RestMethod -Uri "$baseUrl/api/grammar/check" -Method POST -ContentType "application/json" -Body '{"text":"I am learning english and its very intresting"}'
    Write-Host "✅ Grammar Check: Success=$($grammar.success)" -ForegroundColor Green
    Write-Host "   Scores: Grammar=$($grammar.scores.grammar), Overall=$($grammar.scores.overall)"
} catch {
    Write-Host "❌ Grammar check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Chat Conversation
Write-Host "`n3. Testing Chat Conversation..." -ForegroundColor Cyan
try {
    $chat = Invoke-RestMethod -Uri "$baseUrl/api/chat/conversation" -Method POST -ContentType "application/json" -Body '{"message":"Hello, how can you help me learn English?"}'
    Write-Host "✅ Chat: Success=$($chat.success)" -ForegroundColor Green
    Write-Host "   Response length: $($chat.data.message.Length) characters"
} catch {
    Write-Host "❌ Chat conversation failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test User Profile
Write-Host "`n4. Testing User Profile..." -ForegroundColor Cyan
try {
    $profile = Invoke-RestMethod -Uri "$baseUrl/api/user/profile?user_id=test123"
    Write-Host "✅ Profile: Success=$($profile.success)" -ForegroundColor Green
    Write-Host "   User: $($profile.data.username), Languages: $($profile.data.learning_languages -join ', ')"
} catch {
    Write-Host "❌ User profile failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Learning Progress
Write-Host "`n5. Testing Learning Progress..." -ForegroundColor Cyan
try {
    $progress = Invoke-RestMethod -Uri "$baseUrl/api/learning/progress?user_id=test123"
    Write-Host "✅ Progress: Success=$($progress.success)" -ForegroundColor Green
    Write-Host "   Overall: $($progress.data.overall_progress)%, Grammar: $($progress.data.grammar_score)%"
} catch {
    Write-Host "❌ Learning progress failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Telegram Webhook
Write-Host "`n6. Testing Telegram Webhook..." -ForegroundColor Cyan
try {
    $telegram = Invoke-RestMethod -Uri "$baseUrl/api/telegram/webhook" -Method POST -ContentType "application/json" -Body '{"message":{"chat":{"id":123},"text":"test message"}}'
    Write-Host "✅ Telegram Webhook: Response received" -ForegroundColor Green
} catch {
    Write-Host "❌ Telegram webhook failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 API Testing Complete!" -ForegroundColor Green
Write-Host "Frontend URL: https://cc4f0f86.keliva-app.pages.dev" -ForegroundColor Yellow
Write-Host "Backend URL: https://ceda27ad.keliva.pages.dev" -ForegroundColor Yellow