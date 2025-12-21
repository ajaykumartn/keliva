"""
KeLiva - Central Brain (FastAPI Backend)
Main application entry point with enterprise-grade security
"""
# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import jwt
import time
import logging
from datetime import datetime
import asyncio
from threading import Thread

from utils.db_manager import DatabaseManager
# from routers.users import router as users_router
from routers.grammar import router as grammar_router
from routers.chat import router as chat_router
from routers.telegram import router as telegram_router
from routers.voice import router as voice_router
# from routers.rate_limit import router as rate_limit_router
from routers.whatsapp import router as whatsapp_router
from simple_auth import router as auth_router
# from routers.family_groups import router as family_groups_router
# from routers.voice_biometrics import router as voice_biometrics_router
# from routers.dream_journal import router as dream_journal_router
# from routers.emotion_ai import router as emotion_ai_router
# from middleware.rate_limit_middleware import setup_rate_limit_handlers

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key-change-in-production")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com,.vercel.app").split(",")

# Keep-Alive Configuration
KEEP_ALIVE_ENABLED = os.getenv("KEEP_ALIVE_ENABLED", "true").lower() == "true"
KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", "840"))  # 14 minutes (Render sleeps after 15 min)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keep-Alive System for 24/7 Uptime
class KeepAliveManager:
    """Manages self-ping to prevent Render.com from sleeping"""
    
    def __init__(self):
        self.is_running = False
        self.base_url = None
        
    def set_base_url(self, url: str):
        """Set the base URL for self-ping"""
        self.base_url = url
        logger.info(f"Keep-alive base URL set to: {url}")
    
    async def self_ping(self):
        """Ping own health endpoint to stay alive"""
        if not self.base_url:
            return
            
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health") as response:
                    if response.status == 200:
                        logger.info("Keep-alive ping successful")
                    else:
                        logger.warning(f"Keep-alive ping failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Keep-alive ping error: {str(e)}")
    
    async def start_keep_alive(self):
        """Start the keep-alive loop"""
        if not KEEP_ALIVE_ENABLED:
            logger.info("Keep-alive disabled")
            return
            
        self.is_running = True
        logger.info(f"Starting keep-alive with {KEEP_ALIVE_INTERVAL}s interval")
        
        while self.is_running:
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)
            await self.self_ping()
    
    def stop_keep_alive(self):
        """Stop the keep-alive loop"""
        self.is_running = False
        logger.info("Keep-alive stopped")

# Global keep-alive manager
keep_alive_manager = KeepAliveManager()

# Initialize FastAPI app
app = FastAPI(
    title="KeLiva API",
    description="Knowledge-Enhanced Linguistic Intelligence & Voice Assistant",
    version="1.0.0"
)

# Security: Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Startup event to initialize keep-alive
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("KeLiva API starting up...")
    
    # Detect deployment URL for keep-alive
    if KEEP_ALIVE_ENABLED:
        # Try to detect Render URL
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            keep_alive_manager.set_base_url(render_url)
            # Start keep-alive in background
            asyncio.create_task(keep_alive_manager.start_keep_alive())
        else:
            logger.info("No external URL detected, keep-alive will be set up after first request")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("KeLiva API shutting down...")
    keep_alive_manager.stop_keep_alive()

# Middleware to detect external URL on first request
@app.middleware("http")
async def detect_external_url(request: Request, call_next):
    """Detect external URL from first request for keep-alive"""
    if KEEP_ALIVE_ENABLED and not keep_alive_manager.base_url:
        # Construct base URL from request
        scheme = request.url.scheme
        host = request.headers.get("host", request.url.hostname)
        base_url = f"{scheme}://{host}"
        
        # Only set if it's not localhost (i.e., production)
        if "localhost" not in host and "127.0.0.1" not in host:
            keep_alive_manager.set_base_url(base_url)
            # Start keep-alive in background
            asyncio.create_task(keep_alive_manager.start_keep_alive())
    
    response = await call_next(request)
    return response

# Security: JWT Authentication
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token for protected routes"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            JWT_SECRET, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Security: Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Security: Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for security monitoring"""
    start_time = time.time()
    
    # Get client IP (handle proxy headers)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log request details
    logger.info(
        f"IP: {client_ip} | "
        f"Method: {request.method} | "
        f"URL: {str(request.url)} | "
        f"Status: {response.status_code} | "
        f"Time: {process_time:.2f}s | "
        f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    
    # Log suspicious activity
    if response.status_code >= 400:
        logger.warning(
            f"Suspicious activity - IP: {client_ip} | "
            f"Status: {response.status_code} | "
            f"URL: {str(request.url)}"
        )
    
    return response

# Initialize database manager
# For local development, uses SQLite
# For Cloudflare deployment, will use D1 bindings from request.state.env.DB
db_manager = DatabaseManager(db_path=os.getenv("DB_PATH", "keliva.db"))

# Set up rate limit error handlers
# setup_rate_limit_handlers(app)

# Security: CORS configuration with strict origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security: Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

# Include routers
# app.include_router(users_router)
app.include_router(grammar_router)
app.include_router(chat_router)
app.include_router(voice_router)
# app.include_router(rate_limit_router)
app.include_router(telegram_router)
app.include_router(whatsapp_router)

# Advanced features routers
app.include_router(auth_router)
# app.include_router(family_groups_router)
# app.include_router(voice_biometrics_router)
# app.include_router(dream_journal_router)
# app.include_router(emotion_ai_router)

@app.get("/api/health")
@limiter.limit("60/minute")  # Rate limit: 60 requests per minute
async def health_check(request: Request):
    """Health check endpoint for keep-alive monitoring"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }

@app.get("/api/db/test")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def test_database(request: Request):
    """Test database connection and operations"""
    try:
        import sqlite3
        conn = sqlite3.connect(os.getenv("DB_PATH", "keliva.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "ok",
            "users_count": count,
            "message": "Database is working correctly"
        }
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return {
            "status": "error",
            "message": "Database connection failed"
        }

@app.get("/")
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
async def root(request: Request):
    """Root endpoint"""
    return {"message": "KeLiva API is running securely"}

@app.get("/api/test")
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
async def test_endpoint(request: Request):
    """Simple test endpoint for frontend connectivity"""
    return {
        "status": "success",
        "message": "Python backend is working securely!",
        "cors": "enabled",
        "security": "active",
        "timestamp": datetime.now().isoformat()
    }

# Security: Protected endpoint example
@app.get("/api/protected")
@limiter.limit("20/minute")
async def protected_endpoint(request: Request, user: dict = Depends(verify_token)):
    """Example of a protected endpoint requiring JWT authentication"""
    return {
        "message": "This is a protected endpoint",
        "user": user,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
