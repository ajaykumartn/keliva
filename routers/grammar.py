"""
Grammar checking API endpoints
Provides REST API for Grammar Guardian service
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import os

from services.grammar_guardian import GrammarGuardian, GrammarError, GrammarAnalysis


router = APIRouter(prefix="/api/grammar", tags=["grammar"])

# Initialize Grammar Guardian
grammar_guardian = None


def get_grammar_guardian() -> GrammarGuardian:
    """Lazy initialization of Grammar Guardian"""
    global grammar_guardian
    if grammar_guardian is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GROQ_API_KEY not configured"
            )
        grammar_guardian = GrammarGuardian(api_key=api_key)
    return grammar_guardian


# Request/Response models
class GrammarCheckRequest(BaseModel):
    """Request model for grammar checking"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to check for grammar errors")


class GrammarErrorResponse(BaseModel):
    """Response model for a single grammar error"""
    start_pos: int
    end_pos: int
    error_type: str
    original_text: str
    corrected_text: str
    explanation: str
    severity: str


class GrammarCheckResponse(BaseModel):
    """Response model for grammar check results"""
    original_text: str
    corrected_text: str
    errors: List[GrammarErrorResponse]
    overall_score: float
    has_errors: bool


@router.get("/test")
async def test_grammar_router():
    """Test endpoint to verify grammar router is working"""
    return {"message": "Grammar router is working!", "timestamp": "2025-01-05"}

@router.post("/check", response_model=GrammarCheckResponse)
async def check_grammar(request: GrammarCheckRequest):
    """
    Analyze text for grammatical errors and provide corrections.
    
    Uses Groq Llama 3.3 70B model (FREE - 1,000 requests/day).
    
    Args:
        request: GrammarCheckRequest with text to analyze
        
    Returns:
        GrammarCheckResponse with corrections and explanations
        
    Raises:
        HTTPException: If API key is not configured or analysis fails
    """
    print(f"DEBUG: Grammar router called with text: {request.text}")
    
    try:
        guardian = get_grammar_guardian()
        analysis = await guardian.analyze_text(request.text)
        
        print(f"DEBUG: Analysis completed - errors: {len(analysis.errors)}, score: {analysis.overall_score}")
        
        # Convert to response model
        error_responses = [
            GrammarErrorResponse(
                start_pos=error.start_pos,
                end_pos=error.end_pos,
                error_type=error.error_type,
                original_text=error.original_text,
                corrected_text=error.corrected_text,
                explanation=error.explanation,
                severity=error.severity
            )
            for error in analysis.errors
        ]
        
        response = GrammarCheckResponse(
            original_text=analysis.original_text,
            corrected_text=analysis.corrected_text,
            errors=error_responses,
            overall_score=analysis.overall_score,
            has_errors=len(analysis.errors) > 0
        )
        
        print(f"DEBUG: Returning response with {len(error_responses)} errors")
        return response
        
    except ValueError as e:
        print(f"DEBUG: ValueError in grammar check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        print(f"DEBUG: Exception in grammar check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grammar analysis failed: {str(e)}"
        )


class ExplanationRequest(BaseModel):
    """Request model for detailed explanation"""
    error_type: str
    original: str
    corrected: str


class ExplanationResponse(BaseModel):
    """Response model for detailed explanation"""
    explanation: str


@router.post("/explain", response_model=ExplanationResponse)
async def get_explanation(request: ExplanationRequest):
    """
    Get detailed explanation for a specific grammar correction.
    
    Args:
        request: ExplanationRequest with error details
        
    Returns:
        ExplanationResponse with detailed explanation
    """
    try:
        guardian = get_grammar_guardian()
        explanation = await guardian.get_correction_explanation(
            request.error_type,
            request.original,
            request.corrected
        )
        
        return ExplanationResponse(explanation=explanation)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )
