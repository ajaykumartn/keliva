"""
KeLiva - Central Brain (FastAPI Backend)
Main application entry point with 24/7 keep-alive system and AI integration
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

# AI Helper Function
async def get_ai_response(message: str, mode: str = "chat") -> str:
    """Get AI response using Groq API"""
    try:
        import groq
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Sorry, AI service is not configured."
        
        client = groq.Groq(api_key=api_key)
        
        # System prompts based on mode
        system_prompts = {
            "chat": "You are KeLiva, a helpful and friendly AI assistant. Be conversational and helpful.",
            "grammar": "You are KeLiva, a grammar expert. Check the text for grammar errors and provide corrections with explanations. Be clear and educational.",
            "voice": "You are KeLiva, a pronunciation and speaking coach. Help users improve their speaking skills."
        }
        
        system_prompt = system_prompts.get(mode, system_prompts["chat"])
        
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            model="llama3-8b-8192",
            max_tokens=1000,
            temperature=0.7
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"AI response error: {str(e)}")
        return "Sorry, I'm having trouble processing your message right now. Please try again!"

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
    return {"message": "KeLiva API is running with 24/7 uptime and AI integration"}

@app.get("/api/test")
@limiter.limit("30/minute")
async def test_endpoint(request: Request):
    """Simple test endpoint for frontend connectivity"""
    return {
        "status": "success",
        "message": "KeLiva backend is working with AI!",
        "timestamp": datetime.now().isoformat(),
        "keep_alive": KEEP_ALIVE_ENABLED,
        "ai_available": bool(os.getenv("GROQ_API_KEY"))
    }

# Chat endpoint with AI
@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat_endpoint(request: Request):
    """Chat endpoint with AI integration"""
    try:
        data = await request.json()
        message = data.get("message", "")
        mode = data.get("mode", "chat")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get AI response
        ai_response = await get_ai_response(message, mode)
        
        return {
            "response": ai_response,
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing failed")

# Telegram webhook with AI
@app.post("/api/telegram/webhook")
@limiter.limit("100/minute")
async def telegram_webhook(request: Request):
    """Telegram webhook with AI integration"""
    try:
        data = await request.json()
        logger.info("Telegram webhook received")
        
        # Extract message
        if "message" in data:
            message = data["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_name = message.get("from", {}).get("first_name", "User")
            
            if chat_id and text:
                # Handle commands
                if text.startswith("/"):
                    if text == "/start":
                        response_text = f"👋 Hello {user_name}! I'm KeLiva, your AI assistant.\n\n" \
                                      "I can help you with:\n" \
                                      "💬 General conversations\n" \
                                      "✏️ Grammar checking\n" \
                                      "🎤 Speaking practice\n\n" \
                                      "Just send me a message!"
                    elif text == "/help":
                        response_text = "🤖 KeLiva AI Commands:\n\n" \
                                      "/start - Welcome message\n" \
                                      "/help - Show this help\n" \
                                      "/grammar - Switch to grammar mode\n" \
                                      "/chat - Switch to chat mode\n\n" \
                                      "Or just send any message for AI response!"
                    elif text == "/grammar":
                        response_text = "✏️ Grammar mode activated! Send me any text and I'll check it for grammar errors."
                    elif text == "/chat":
                        response_text = "💬 Chat mode activated! Let's have a conversation."
                    else:
                        response_text = "Unknown command. Type /help for available commands."
                else:
                    # Get AI response for regular messages
                    mode = "grammar" if "grammar" in text.lower() or "correct" in text.lower() else "chat"
                    response_text = await get_ai_response(text, mode)
                
                # Send response back to Telegram
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                if bot_token:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": response_text
                            },
                            timeout=10.0
                        )
                    
                    logger.info(f"AI response sent to Telegram chat {chat_id}")
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {str(e)}")
        return {"ok": True}  # Always return ok to Telegram

# Telegram webhook verification
@app.get("/api/telegram/webhook")
async def telegram_webhook_verify(request: Request):
    """Telegram webhook verification"""
    return {
        "status": "Telegram webhook active with AI integration", 
        "timestamp": datetime.now().isoformat(),
        "ai_available": bool(os.getenv("GROQ_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
