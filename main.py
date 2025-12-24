"""
KeLiva - Central Brain (FastAPI Backend)
Main application entry point with 24/7 keep-alive system
"""
# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
import logging
from datetime import datetime
import asyncio

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keep-Alive Configuration
KEEP_ALIVE_ENABLED = os.getenv("KEEP_ALIVE_ENABLED", "true").lower() == "true"
KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", "840"))  # 14 minutes

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

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
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/health")
                if response.status_code == 200:
                    logger.info("Keep-alive ping successful")
                else:
                    logger.warning(f"Keep-alive ping failed with status: {response.status_code}")
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

# Security: Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Security: Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for security monitoring"""
    start_time = time.time()
    
    # Get client IP
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
        f"Time: {process_time:.2f}s"
    )
    
    return response

# Security: CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint for keep-alive monitoring"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "KeLiva API is running with 24/7 keep-alive"
    }

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Root endpoint"""
    return {"message": "KeLiva API is running with 24/7 uptime"}

@app.get("/api/test")
@limiter.limit("30/minute")
async def test_endpoint(request: Request):
    """Simple test endpoint for frontend connectivity"""
    return {
        "status": "success",
        "message": "KeLiva backend is working!",
        "timestamp": datetime.now().isoformat(),
        "keep_alive": KEEP_ALIVE_ENABLED
    }

# Simple chat endpoint
@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat_endpoint(request: Request):
    """Simple chat endpoint"""
    try:
        data = await request.json()
        message = data.get("message", "")
        
        # Simple response for now
        response = f"Echo: {message}"
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
