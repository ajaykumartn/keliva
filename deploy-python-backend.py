#!/usr/bin/env python3
"""
Deploy script for KeLiva Python backend
Supports Railway, Render, and other Python hosting platforms
"""

import os
import subprocess
import sys
from pathlib import Path

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        "functions/main.py",
        "functions/requirements.txt",
        "functions/routers/telegram.py",
        "functions/services/conversation_service.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def create_railway_config():
    """Create railway.json for Railway deployment"""
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "cd functions && python -m uvicorn main:app --host 0.0.0.0 --port $PORT",
            "healthcheckPath": "/api/health"
        }
    }
    
    import json
    with open("railway.json", "w") as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ Created railway.json")

def create_render_config():
    """Create render.yaml for Render deployment"""
    render_config = """services:
  - type: web
    name: keliva-backend
    env: python
    buildCommand: cd functions && pip install -r requirements.txt
    startCommand: cd functions && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: ELEVENLABS_API_KEY
        sync: false
      - key: DB_PATH
        value: ./keliva.db
      - key: CHROMA_DB_PATH
        value: ./chroma_db
"""
    
    with open("render.yaml", "w") as f:
        f.write(render_config)
    
    print("✅ Created render.yaml")

def create_dockerfile():
    """Create Dockerfile for containerized deployment"""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY functions/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY functions/ .

# Create directories for data
RUN mkdir -p chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    print("✅ Created Dockerfile")

def create_procfile():
    """Create Procfile for Heroku-style deployment"""
    with open("Procfile", "w") as f:
        f.write("web: cd functions && python -m uvicorn main:app --host 0.0.0.0 --port $PORT\n")
    
    print("✅ Created Procfile")

def main():
    print("🚀 KeLiva Python Backend Deployment Setup")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    print("\n📦 Creating deployment configurations...")
    
    # Create all deployment configs
    create_railway_config()
    create_render_config()
    create_dockerfile()
    create_procfile()
    
    print("\n🎉 Deployment configurations created!")
    print("\n📋 Next steps:")
    print("\n1. **Railway Deployment:**")
    print("   - Install Railway CLI: npm install -g @railway/cli")
    print("   - Login: railway login")
    print("   - Deploy: railway up")
    print("   - Set environment variables in Railway dashboard")
    
    print("\n2. **Render Deployment:**")
    print("   - Push code to GitHub")
    print("   - Connect repository in Render dashboard")
    print("   - Render will auto-deploy using render.yaml")
    
    print("\n3. **Docker Deployment:**")
    print("   - Build: docker build -t keliva-backend .")
    print("   - Run: docker run -p 8000:8000 keliva-backend")
    
    print("\n4. **Environment Variables to Set:**")
    print("   - GROQ_API_KEY")
    print("   - TELEGRAM_BOT_TOKEN")
    print("   - ELEVENLABS_API_KEY (optional)")
    
    print("\n5. **Update Telegram Webhook:**")
    print("   - Replace YOUR_DOMAIN with your deployed URL")
    print("   - POST https://api.telegram.org/bot<TOKEN>/setWebhook")
    print("   - Body: {\"url\": \"https://YOUR_DOMAIN/api/telegram/webhook\"}")

if __name__ == "__main__":
    main()