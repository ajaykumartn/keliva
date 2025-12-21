"""
Rate Limit Middleware
Provides middleware and utilities for rate limit handling in FastAPI.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable
import traceback

from services.rate_limiter import RateLimitExceededError


async def rate_limit_error_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
    """
    Custom error handler for rate limit exceeded errors.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceededError exception
        
    Returns:
        JSONResponse with rate limit error details
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": str(exc),
            "details": {
                "model": exc.model.value,
                "limit": exc.limit,
                "reset_time": exc.reset_time.isoformat(),
                "retry_after": int((exc.reset_time - exc.reset_time.utcnow()).total_seconds())
            }
        },
        headers={
            "Retry-After": str(int((exc.reset_time - exc.reset_time.utcnow()).total_seconds()))
        }
    )


def setup_rate_limit_handlers(app):
    """
    Set up rate limit error handlers for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RateLimitExceededError, rate_limit_error_handler)
