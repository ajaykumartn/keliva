# KeLiva Project Structure (PostgreSQL Version)

## Core Files
```
keliva/
├── main.py                          # Main FastAPI application with PostgreSQL
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables
├── .env.example                    # Environment template
├── postgres_deploy_guide.md        # PostgreSQL deployment guide
├── init_postgres_database.py       # Database initialization script
└── README.md                       # Project documentation
```

## Database & Models
```
models/
├── __init__.py                     # Models package exports
├── postgres_database.py           # PostgreSQL database manager and services
├── database.py                     # Legacy SQLite models (kept for reference)
└── user.py                        # Legacy user models (kept for reference)
```

## Routers (Partially Used)
```
routers/
├── __init__.py
├── auth.py                         # Authentication routes (not used - integrated in main.py)
├── chat.py                         # Chat routes (not used - integrated in main.py)
├── grammar.py                      # Grammar routes (not used - integrated in main.py)
├── rate_limit.py                   # Rate limiting (not used - integrated in main.py)
├── telegram.py                     # Telegram webhook (kept for reference)
├── users.py                        # User routes (not used - integrated in main.py)
└── voice.py                        # Voice routes (not used - integrated in main.py)
```

## Services (Legacy - Not Used)
```
services/
├── __init__.py
├── conversation_service.py         # Legacy conversation service
├── grammar_guardian.py             # Legacy grammar service
├── knowledge_vault.py              # Legacy knowledge service
├── polyglot_engine.py              # Legacy language service
├── rate_limiter.py                 # Legacy rate limiter
├── stt_service.py                  # Speech-to-text service
└── tts_service.py                  # Text-to-speech service
```

## Frontend
```
frontend/
├── src/                            # React TypeScript source
├── public/                         # Static assets
├── .env                           # Frontend environment variables
├── .env.production                # Production environment
├── package.json                   # Node.js dependencies
├── vercel.json                    # Vercel deployment config
└── vite.config.ts                 # Vite build configuration
```

## Deployment & Configuration
```
├── Procfile                       # Heroku deployment (if needed)
├── render.yaml                    # Render.com deployment config
├── deploy-render.ps1              # Render deployment script
├── deploy-render.bat              # Render deployment batch script
├── verify-deployment.ps1          # Deployment verification
├── verify-render-deployment.ps1   # Render-specific verification
└── test-endpoints.ps1             # API endpoint testing
```

## Telegram Integration
```
├── setup-telegram-webhook.ps1     # Telegram webhook setup
├── setup-telegram.ps1             # Telegram bot setup
├── setup-webhooks.ps1             # General webhook setup
└── WEBHOOK_SETUP.md               # Webhook documentation
```

## Other Files
```
├── .gitignore                     # Git ignore rules
├── logo.png                       # Project logo
├── package.json                   # Node.js config (for frontend tools)
├── MOBILE_APP_PLAN.md             # Mobile app planning (future)
├── DEPLOYMENT_READY.md            # Deployment checklist
├── SECURITY_CHECKLIST.md          # Security guidelines
└── middleware/                    # Custom middleware (if any)
```

## Features Implemented

### ✅ Core Features (Active)
- **PostgreSQL Database**: Production-ready database with connection pooling
- **User Authentication**: Registration, login with JWT tokens
- **Grammar Checking**: AI-powered grammar correction with history
- **Chat System**: Conversational AI with message storage
- **Voice Practice**: Voice session recording and feedback storage
- **Telegram Integration**: Bot with AI responses and commands
- **24/7 Keep-Alive**: Prevents service sleeping on free tier
- **Rate Limiting**: API protection and abuse prevention
- **CORS Support**: Frontend integration ready
- **Security Headers**: Production security measures

### 📦 Database Schema
- **users**: User accounts and profiles
- **conversations**: Chat conversations
- **messages**: Individual messages in conversations
- **grammar_corrections**: Grammar check results and history
- **voice_practice_sessions**: Voice practice data and scores
- **user_facts**: User personalization data

### 🚫 Removed Features (Simplified)
- Family Groups and Family Chat
- Dream Journal
- Emotion AI Detection
- Voice Biometrics
- Email Services
- ChromaDB Vector Storage
- Complex Knowledge Vault

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Chat & AI
- `POST /api/chat` - Chat with AI (supports grammar and general chat modes)

### User Management
- `GET /api/user/profile/{user_id}` - Get user profile
- `GET /api/user/conversations/{user_id}` - Get conversation history
- `GET /api/user/grammar-history/{user_id}` - Get grammar correction history
- `GET /api/user/voice-history/{user_id}` - Get voice practice history

### Voice Practice
- `POST /api/voice/practice` - Save voice practice session

### Telegram
- `POST /api/telegram/webhook` - Telegram webhook endpoint
- `GET /api/telegram/webhook` - Webhook verification

### Health & Monitoring
- `GET /api/health` - Application health check
- `GET /api/database/health` - Database connection health
- `GET /api/test` - Simple connectivity test

## Deployment Status
- ✅ Backend: Deployed on Render.com with PostgreSQL
- ✅ Frontend: Deployed on Vercel
- ✅ Database: PostgreSQL on Render.com
- ✅ Keep-Alive: 24/7 uptime system active
- ✅ Telegram Bot: Active with webhook integration

This simplified structure focuses on the core functionality: grammar checking, chat, and voice practice with a robust PostgreSQL backend.