"""
KeLiva - Central Brain (FastAPI Backend)
Main application entry point
"""
# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os

from utils.db_manager import DatabaseManager
from routers import users_router, grammar_router, chat_router, telegram_router
from routers.voice import router as voice_router
from routers.rate_limit import router as rate_limit_router
from routers.whatsapp import router as whatsapp_router
from routers.auth import router as auth_router
from routers.family_groups import router as family_groups_router
from routers.voice_biometrics import router as voice_biometrics_router
from routers.dream_journal import router as dream_journal_router
from routers.emotion_ai import router as emotion_ai_router
# from routers.make_integration import router as make_integration_router
from middleware import setup_rate_limit_handlers

app = FastAPI(
    title="KeLiva API",
    description="Knowledge-Enhanced Linguistic Intelligence & Voice Assistant",
    version="1.0.0"
)

# Initialize database manager
# For local development, uses SQLite
# For Cloudflare deployment, will use D1 bindings from request.state.env.DB
db_manager = DatabaseManager(db_path=os.getenv("DB_PATH", "keliva.db"))

# Set up rate limit error handlers
setup_rate_limit_handlers(app)

# Include routers
app.include_router(users_router)
app.include_router(grammar_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(rate_limit_router)
app.include_router(telegram_router)
app.include_router(whatsapp_router)

# Advanced features routers
app.include_router(auth_router)
app.include_router(family_groups_router)
app.include_router(voice_biometrics_router)
app.include_router(dream_journal_router)
app.include_router(emotion_ai_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for keep-alive monitoring"""
    return {
        "status": "ok",
        "database": "connected"
    }


@app.get("/api/db/test")
async def test_database():
    """Test database connection and operations"""
    try:
        # Test listing users
        users = db_manager.list_users()
        return {
            "status": "ok",
            "users_count": len(users),
            "message": "Database is working correctly"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "KeLiva API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
