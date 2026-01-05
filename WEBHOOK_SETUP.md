# 🔗 KeLiva Webhook Setup Guide

Your KeLiva backend already has comprehensive Telegram and WhatsApp integration with full AI capabilities!

## 🤖 What's Already Integrated:

### ✅ Telegram Bot Features:
- **Full Groq AI Integration** - Smart responses using your API key
- **Multiple Modes**: Grammar check, general chat, voice practice
- **Interactive Menus** - Inline keyboards for easy navigation
- **Conversation Memory** - Remembers context within sessions
- **Multi-language Support** - English, Kannada, Telugu
- **Voice Message Handling** - Processes voice notes
- **Command Support** - /start, /help, /grammar, /chat, /voice

### ✅ WhatsApp Integration:
- **Business API Ready** - Full webhook support
- **Message Processing** - Handles text and media messages
- **Verification System** - Secure webhook verification
- **AI Responses** - Connected to conversation service

## 📱 Quick Telegram Setup

### 1. Your Bot is Ready!
- **Bot Token**: `8400809403:AAGulVzMo4raH8ITngvzdDstGKgvBRn5Dmw`
- **Webhook URL**: `https://keliva.onrender.com/api/telegram/webhook`

### 2. Set Webhook (Run this now):
```powershell
./setup-telegram-webhook.ps1
```

### 3. Test Your Bot:
1. Search for your bot on Telegram
2. Send `/start` command
3. Choose from interactive menu:
   - ✏️ Grammar Check
   - 💬 General Chat  
   - 🎤 Voice Practice

## 🎯 Bot Capabilities:

### Grammar Check Mode:
- Send any English text
- Get corrections and explanations
- Clean, structured responses
- Educational feedback

### General Chat Mode:
- Natural conversations
- Multi-language support
- Context awareness
- Friendly AI personality

### Voice Practice Mode:
- Voice message processing
- Pronunciation feedback
- Speaking exercises
- Accent improvement tips

## 💬 WhatsApp Business Setup

### 1. Facebook Developer Console:
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create app → Add WhatsApp Business API
3. **Webhook URL**: `https://keliva.onrender.com/api/whatsapp/webhook`
4. **Verify Token**: Set `WHATSAPP_VERIFY_TOKEN` in Render environment

### 2. Add Environment Variable:
In Render dashboard:
```
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token_here
```

## 🔧 Available Endpoints:

### Telegram (Full AI Integration):
- **POST** `/api/telegram/webhook` - Main webhook with AI
- **POST** `/api/telegram/set-webhook` - Helper for setup
- **GET** `/api/telegram/webhook-info` - Status check

### WhatsApp (AI Ready):
- **POST** `/api/whatsapp/webhook` - Message processing
- **GET** `/api/whatsapp/webhook` - Verification

### Core API:
- **GET** `/api/health` - Keep-alive monitoring
- **GET** `/api/test` - Basic connectivity test
- **POST** `/api/chat` - Direct chat API

## 🚀 Ready to Use!

Your Telegram bot is already fully functional with:
- ✅ **Groq AI Integration** (using your API key)
- ✅ **24/7 Uptime** (keep-alive system active)
- ✅ **Enterprise Security** (rate limiting, logging)
- ✅ **Multi-mode Chat** (grammar, chat, voice)
- ✅ **Interactive Interface** (inline keyboards)

Just run the setup script and start chatting! 🎉