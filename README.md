# Keliva - AI Language Learning Platform

## 🌟 Overview

Keliva is an advanced AI-powered language learning platform that provides personalized language learning experiences through natural conversations. The platform supports multiple languages (English, Kannada, Telugu) and offers both web dashboard and WhatsApp integration for seamless learning.

## ✨ Key Features

### 🤖 AI-Powered Learning
- **Vani AI Companion** - Intelligent conversational AI that adapts to your learning style
- **Emotion Recognition** - Advanced emotion detection to optimize learning experiences
- **Personalized Responses** - Context-aware conversations that feel natural and engaging
- **Multi-Language Support** - English, Kannada, and Telugu language learning

### 👨‍👩‍👧‍👦 Family Learning Groups
- **WhatsApp-Style Interface** - Familiar chat interface for family communication
- **Real-Time Chat** - Instant messaging with emotion detection
- **Progress Tracking** - Monitor family learning progress and streaks
- **Invitation System** - Easy family member invitations with unique codes
- **Learning Analytics** - Comprehensive emotion and progress analytics

### 🎯 Learning Tools
- **Dream Journal** - AI-powered dream analysis for vocabulary building
- **Grammar Checking** - Real-time grammar correction and suggestions
- **Voice Biometrics** - Voice-based learning and pronunciation feedback
- **Vocabulary Builder** - Personalized vocabulary expansion

### 📱 Multi-Platform Access
- **Web Dashboard** - Full-featured web application
- **WhatsApp Integration** - Learn on-the-go through WhatsApp
- **Telegram Bot** - Alternative messaging platform support
- **Mobile Responsive** - Perfect experience on all devices

## 🏗️ Architecture

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx          # Main dashboard
│   │   ├── FamilyGroups.tsx       # Family learning groups
│   │   ├── EmotionAI.tsx          # Emotion recognition interface
│   │   ├── DreamJournal.tsx       # Dream analysis tool
│   │   ├── Vocabulary.tsx         # Vocabulary builder
│   │   └── VoiceBiometrics.tsx    # Voice learning tools
│   ├── contexts/                  # React contexts for state management
│   └── styles/                    # CSS and styling files
```

### Backend (FastAPI + Python)
```
backend/
├── main.py                        # FastAPI application entry point
├── routers/
│   ├── auth.py                    # Authentication endpoints
│   ├── family_groups.py           # Family groups API
│   ├── emotion_ai.py              # Emotion recognition API
│   ├── dream_journal.py           # Dream analysis API
│   ├── whatsapp.py                # WhatsApp integration
│   └── telegram.py                # Telegram bot integration
├── services/
│   ├── vani_persona.py            # AI personality system
│   ├── emotion_ai.py              # Emotion recognition service
│   ├── family_groups.py           # Family groups logic
│   └── email_service.py           # Email invitation service
└── models/
    └── user.py                    # User data models
```

### Database (SQLite)
- **Users** - User accounts and profiles
- **Family Groups** - Group management and settings
- **Chat Messages** - Family group conversations
- **Emotion Analysis** - Emotion detection results
- **Learning Progress** - User progress tracking
- **Dream Entries** - Dream journal data

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- SQLite

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd keliva
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

4. **Environment Configuration**
Create a `.env` file in the root directory:
```env
# Database
DB_PATH=keliva.db
CHROMA_DB_PATH=./chroma_db

# AI Services
GROQ_API_KEY=your_groq_api_key_here

# WhatsApp Integration (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Frontend URL
FRONTEND_URL=https://keliva-app.pages.dev

# Server Configuration
PORT=8000
HOST=0.0.0.0
DEBUG=true
```

### Database Setup
```bash
python migrate_database.py
```

## 🎨 Design System

### Color Palette
- **Primary Green**: #00a884 (WhatsApp-inspired)
- **Secondary Green**: #06cf9c
- **Dark Background**: #0b141a
- **Card Background**: #202c33
- **Text Primary**: #e9edef
- **Text Secondary**: #8696a0

### UI Components
- **Glassmorphism Design** - Modern frosted glass effects
- **Gradient Typography** - Beautiful text treatments
- **Smooth Animations** - 60fps micro-interactions
- **Responsive Layout** - Perfect on all devices

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout

### Family Groups
- `GET /api/family/groups` - Get user's family groups
- `POST /api/family/groups` - Create new family group
- `POST /api/family/groups/{id}/invite` - Invite member
- `GET /api/family/groups/{id}/messages` - Get group messages
- `POST /api/family/groups/{id}/messages` - Send message

### Emotion AI
- `POST /api/emotion/analyze-text` - Analyze text emotion
- `GET /api/emotion/patterns` - Get emotion patterns
- `GET /api/emotion/insights` - Get learning insights

### WhatsApp Integration
- `POST /api/whatsapp/webhook` - WhatsApp webhook
- `POST /api/whatsapp/send` - Send WhatsApp message

## 🤖 AI Features

### Vani AI Persona
- **Personality System** - Consistent, friendly AI companion
- **Context Awareness** - Remembers conversation history
- **Emotional Intelligence** - Adapts to user emotions
- **Learning Optimization** - Personalizes based on progress

### Emotion Recognition
- **Text Analysis** - Detects emotions in written text
- **Voice Analysis** - Emotion detection from speech
- **Learning Insights** - Emotion-based learning recommendations
- **Progress Tracking** - Emotional learning patterns

### Dream Analysis
- **AI-Powered Interpretation** - Intelligent dream analysis
- **Vocabulary Extraction** - Learn new words from dreams
- **Cultural Context** - Multi-cultural dream interpretation
- **Learning Integration** - Dreams as learning opportunities

## 📱 WhatsApp Integration

### Features
- **Natural Conversations** - Chat with Vani AI via WhatsApp
- **Interactive Buttons** - Rich interactive messages
- **Voice Messages** - Speech-to-text processing
- **Image Analysis** - AI-powered image understanding
- **Grammar Correction** - Real-time grammar feedback

### Setup
1. Configure Twilio WhatsApp sandbox
2. Set webhook URL in Twilio console
3. Add environment variables
4. Test with WhatsApp number

## 🔐 Security

### Authentication
- **JWT Tokens** - Secure authentication system
- **Password Hashing** - Bcrypt password protection
- **Session Management** - Secure session handling

### Data Protection
- **Input Validation** - Comprehensive input sanitization
- **SQL Injection Prevention** - Parameterized queries
- **XSS Protection** - Content Security Policy
- **Rate Limiting** - API rate limiting

## 🚀 Deployment

### Frontend (Cloudflare Pages)
```bash
npm run build
# Deploy to Cloudflare Pages
```

### Backend (Cloudflare Workers)
```bash
# Configure wrangler.toml
wrangler deploy
```

### Database
- SQLite for development
- PostgreSQL for production (recommended)

## 📊 Analytics & Monitoring

### Learning Analytics
- **Progress Tracking** - User learning progress
- **Emotion Analytics** - Emotional learning patterns
- **Family Insights** - Group learning statistics
- **Usage Metrics** - Platform usage analytics

### Performance Monitoring
- **Response Times** - API performance tracking
- **Error Rates** - Error monitoring and alerting
- **User Engagement** - User activity metrics

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards
- **TypeScript** - Strict type checking
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Testing** - Unit and integration tests

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Documentation
- API documentation available at `/docs`
- Component documentation in source files
- Setup guides in this README

### Contact
- Email: support@keliva.com
- GitHub Issues: For bug reports and feature requests

## 🎯 Roadmap

### Upcoming Features
- **Mobile Apps** - Native iOS and Android apps
- **Advanced Analytics** - Enhanced learning insights
- **More Languages** - Additional language support
- **Gamification** - Learning games and challenges
- **Social Features** - Community learning features

### Technical Improvements
- **Performance Optimization** - Enhanced loading speeds
- **Offline Support** - Progressive Web App features
- **Real-time Sync** - Cross-device synchronization
- **Advanced AI** - Improved AI capabilities

---

**Keliva** - Empowering families to learn languages together through AI-powered conversations and emotional intelligence. 🌟