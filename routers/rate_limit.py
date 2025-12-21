"""
Rate Limit Router
Provides endpoints for checking and managing API rate limits.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from datetime import datetime

from services.rate_limiter import get_rate_limiter, GroqModel, RateLimitInfo

router = APIRouter(prefix="/api/rate-limits", tags=["rate-limits"])


@router.get("/status")
async def get_rate_limit_status() -> Dict[str, Any]:
    """
    Get current rate limit status for all models.
    
    Returns:
        Dictionary with rate limit information for each model
    """
    limiter = get_rate_limiter()
    all_limits = limiter.get_all_limits()
    
    # Format response
    response = {
        "timestamp": datetime.utcnow().isoformat(),
        "limits": {}
    }
    
    for model_name, info in all_limits.items():
        response["limits"][model_name] = {
            "current_count": info.current_count,
            "limit": info.limit,
            "remaining": info.remaining,
            "percentage_used": round(info.percentage_used, 2),
            "is_exceeded": info.is_exceeded,
            "reset_time": info.reset_time.isoformat()
        }
    
    return response


@router.get("/status/{model}")
async def get_model_rate_limit_status(model: str) -> Dict[str, Any]:
    """
    Get rate limit status for a specific model.
    
    Args:
        model: Model name (llama-3.3-70b-versatile or llama-3.3-8b-instant)
        
    Returns:
        Rate limit information for the specified model
    """
    limiter = get_rate_limiter()
    
    # Validate model name
    try:
        groq_model = GroqModel(model)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model name. Must be one of: {[m.value for m in GroqModel]}"
        )
    
    info = limiter.check_limit(groq_model)
    
    return {
        "model": model,
        "current_count": info.current_count,
        "limit": info.limit,
        "remaining": info.remaining,
        "percentage_used": round(info.percentage_used, 2),
        "is_exceeded": info.is_exceeded,
        "reset_time": info.reset_time.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/reset/{model}")
async def reset_model_rate_limit(model: str) -> Dict[str, str]:
    """
    Reset rate limit counter for a specific model (admin/testing only).
    
    Args:
        model: Model name to reset
        
    Returns:
        Success message
    """
    limiter = get_rate_limiter()
    
    # Validate model name
    try:
        groq_model = GroqModel(model)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model name. Must be one of: {[m.value for m in GroqModel]}"
        )
    
    limiter.reset_model(groq_model)
    
    return {
        "message": f"Rate limit reset successfully for {model}",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/reset")
async def reset_all_rate_limits() -> Dict[str, str]:
    """
    Reset all rate limit counters (admin/testing only).
    
    Returns:
        Success message
    """
    limiter = get_rate_limiter()
    limiter.reset_all()
    
    return {
        "message": "All rate limits reset successfully",
        "timestamp": datetime.utcnow().isoformat()
    }
