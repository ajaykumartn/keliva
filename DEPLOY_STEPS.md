# KeLiva Cloudflare Deployment Steps

## Prerequisites
1. **Run PowerShell as Administrator** (Right-click PowerShell → "Run as Administrator")
2. Navigate to project: `cd "D:\DREAM\3RD\AJAY"`

## Step 1: Create D1 Database
```powershell
wrangler d1 create keliva-db
```
**Important**: Copy the database_id from the output and update wrangler.toml

## Step 2: Update wrangler.toml
Replace `REPLACE_WITH_YOUR_DATABASE_ID` with the actual database_id from step 1.

## Step 3: Apply Database Schema
```powershell
wrangler d1 execute keliva-db --file=schema.sql
```

## Step 4: Set Secrets
```powershell
wrangler secret put GROQ_API_KEY
wrangler secret put TELEGRAM_BOT_TOKEN
```
Use your existing values:
- GROQ_API_KEY: `your_groq_api_key_here`
- TELEGRAM_BOT_TOKEN: `your_telegram_bot_token_here`

## Step 5: Deploy Backend
```powershell
wrangler pages deploy functions --project-name=keliva
```

## Step 6: Deploy Frontend
```powershell
cd frontend
npm install
npm run build
wrangler pages deploy dist --project-name=keliva-app
cd ..
```

## Step 7: Set Up Webhooks
```powershell
.\setup-webhooks.ps1 -Platform cloudflare
```

## Your URLs
- **Backend**: https://keliva.pages.dev
- **Frontend**: https://keliva-app.pages.dev
- **API Docs**: https://keliva.pages.dev/docs

## Webhook URLs (for Telegram Bot)
- **Telegram**: https://keliva.pages.dev/api/telegram/webhook
- **WhatsApp**: https://keliva.pages.dev/api/whatsapp/webhook