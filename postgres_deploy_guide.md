# KeLiva PostgreSQL Deployment Guide

## Overview
This guide will help you deploy KeLiva with PostgreSQL database on Render.com. The setup includes:
- Grammar checking with AI
- Chat functionality with conversation history  
- Voice practice sessions
- User authentication and profiles
- 24/7 keep-alive system

## Step 1: Set Up PostgreSQL Database on Render

1. Go to Render.com Dashboard
2. Click "New +" → "PostgreSQL"
3. Configure:
   - Name: `keliva-database`
   - Database: `keliva`
   - User: `keliva_user`
   - Plan: Free

## Step 2: Deploy Backend Web Service

1. Create Web Service from GitHub repo
2. Configure:
   - Name: `keliva-backend`
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   Add these environment variables in Render:

   ```bash
   # Database Configuration (Your PostgreSQL Database)
   DATABASE_URL=postgresql://keliva_user:RtUpedFGMfPjyU7QP70VCbGoAsA9qPcS@dpg-d5dtdcf5r7bs73c6eap0-a.oregon-postgres.render.com/keliva
   
   # API Keys
   GROQ_API_KEY=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
   TELEGRAM_BOT_TOKEN=8400809403:AAGulVzMo4raH8ITngvzdDstGKgvBRn5Dmw
   
   # Security
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
   SECRET_KEY=your-super-secret-key-change-in-production
   
   # CORS Configuration
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://keliva.vercel.app
   
   # Keep-Alive Configuration
   KEEP_ALIVE_ENABLED=true
   KEEP_ALIVE_INTERVAL=840
   
   # Environment
   ENVIRONMENT=production
   ```

## Features Included
- Grammar checking with AI
- Chat system with conversation history
- Voice practice sessions
- User authentication
- 24/7 uptime with keep-alive
- CORS support for frontend

## API Endpoints
- POST /api/auth/register - User registration
- POST /api/auth/login - User login  
- POST /api/chat - Chat with AI
- POST /api/voice/practice - Save voice session
- GET /api/user/grammar-history/{user_id} - Grammar history
- GET /api/user/voice-history/{user_id} - Voice history
- GET /api/health - Health check
- GET /api/database/health - Database health