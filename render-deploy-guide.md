# KeLiva Render.com Deployment Guide

## 🚀 Complete Deployment Steps

### Step 1: Backend Deployment on Render.com

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub (recommended)

2. **Deploy Backend**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `keliva-backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Instance Type**: `Free` (0.1 CPU, 512MB RAM)

3. **Environment Variables**
   Add these in Render dashboard:
   ```
   SECRET_KEY=your-super-secret-key-change-in-production
   JWT_SECRET=your-jwt-secret-key-change-in-production
   DEBUG_MODE=false
   ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
   ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com,.vercel.app
   KEEP_ALIVE_ENABLED=true
   KEEP_ALIVE_INTERVAL=840
   GROQ_API_KEY=your_groq_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Note your backend URL: `https://keliva-backend.onrender.com`

### Step 2: Frontend Deployment on Vercel

1. **Update Frontend Config**
   - Update `frontend/.env` with your Render backend URL:
   ```
   VITE_API_BASE_URL=https://keliva-backend.onrender.com
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your repository
   - Set root directory to `frontend`
   - Deploy automatically

### Step 3: 24/7 Keep-Alive Setup

The backend includes automatic keep-alive functionality:

1. **Built-in Keep-Alive**
   - Pings itself every 14 minutes
   - Prevents Render's 15-minute sleep timeout
   - Automatically detects production URL

2. **UptimeRobot Setup (Optional Extra Protection)**
   - Go to [uptimerobot.com](https://uptimerobot.com)
   - Create free account
   - Add monitor:
     - **Type**: HTTP(s)
     - **URL**: `https://keliva-backend.onrender.com/api/health`
     - **Interval**: 5 minutes
     - **Name**: KeLiva Backend

### Step 4: Update CORS Origins

After deployment, update your backend environment variables:

```
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
```

Replace `your-frontend-domain` with your actual Vercel domain.

## 🔧 Troubleshooting

### Backend Issues
- Check Render logs for errors
- Verify all environment variables are set
- Test health endpoint: `/api/health`

### Frontend Issues
- Verify `VITE_API_BASE_URL` points to correct backend
- Check browser console for CORS errors
- Ensure backend is running before testing frontend

### Keep-Alive Issues
- Check logs for "Keep-alive ping successful" messages
- Verify `KEEP_ALIVE_ENABLED=true` in environment
- Monitor uptime with UptimeRobot

## 📊 Free Tier Limits

### Render.com Free Tier
- **CPU**: 0.1 CPU units
- **RAM**: 512MB
- **Bandwidth**: 100GB/month
- **Sleep**: After 15 minutes of inactivity (prevented by keep-alive)
- **Build Time**: 500 minutes/month

### Vercel Free Tier
- **Bandwidth**: 100GB/month
- **Serverless Functions**: 100GB-hours/month
- **Builds**: 6,000 minutes/month

## 🎯 Expected Performance

- **Response Time**: 200-500ms (after cold start)
- **Cold Start**: 2-5 seconds (first request after sleep)
- **Uptime**: 99.9% with keep-alive
- **Concurrent Users**: 10-50 (free tier)

## ✅ Deployment Checklist

- [ ] Backend deployed on Render
- [ ] Environment variables configured
- [ ] Health endpoint responding
- [ ] Keep-alive logs showing success
- [ ] Frontend deployed on Vercel
- [ ] CORS configured correctly
- [ ] API calls working from frontend
- [ ] UptimeRobot monitoring setup (optional)

Your KeLiva app is now live 24/7 with enterprise security and keep-alive functionality!