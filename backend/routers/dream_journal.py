"""
Dream Journal Router
Handles dream recording, analysis, and learning insights
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from models.user import User
from services.dream_journal import DreamJournalService
from routers.auth import get_current_user

router = APIRouter(prefix="/api/dreams", tags=["dream_journal"])

# Initialize service
dream_service = DreamJournalService(os.getenv("DB_PATH", "keliva.db"))

class AddDreamEntry(BaseModel):
    dream_text: str
    language: str = "en"
    voice_recording_url: Optional[str] = None

class DreamStatisticsRequest(BaseModel):
    days_back: int = 30

@router.post("/entries")
async def add_dream_entry(
    dream_data: AddDreamEntry,
    current_user: User = Depends(get_current_user)
):
    """Add a new dream entry"""
    entry_id = dream_service.add_dream_entry(
        user_id=current_user.id,
        dream_text=dream_data.dream_text,
        language=dream_data.language,
        voice_recording_url=dream_data.voice_recording_url
    )
    
    if not entry_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add dream entry"
        )
    
    return {
        "message": "Dream entry added successfully",
        "entry_id": entry_id
    }

@router.post("/entries/voice")
async def add_dream_entry_with_voice(
    voice_file: UploadFile = File(...),
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Add dream entry with voice recording"""
    try:
        # Save voice file (implement proper file storage)
        voice_filename = f"dream_voice_{current_user.id}_{voice_file.filename}"
        voice_url = f"/uploads/dreams/{voice_filename}"
        
        # TODO: Implement actual file saving and STT processing
        # For now, we'll simulate transcription
        dream_text = "This is a simulated transcription of the dream voice recording."
        
        entry_id = dream_service.add_dream_entry(
            user_id=current_user.id,
            dream_text=dream_text,
            language=language,
            voice_recording_url=voice_url
        )
        
        if not entry_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add dream entry"
            )
        
        return {
            "message": "Dream entry with voice added successfully",
            "entry_id": entry_id,
            "voice_url": voice_url,
            "transcribed_text": dream_text
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice recording: {str(e)}"
        )

@router.get("/entries")
async def get_dream_entries(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get user's dream entries"""
    entries = dream_service.get_user_dream_entries(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    return {
        "message": "Dream entries retrieved successfully",
        "entries": [entry.to_dict() for entry in entries],
        "total_count": len(entries)
    }

@router.get("/insights")
async def get_learning_insights(
    insight_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get learning insights from dreams"""
    insights = dream_service.get_user_learning_insights(
        user_id=current_user.id,
        insight_type=insight_type
    )
    
    return {
        "message": "Learning insights retrieved successfully",
        "insights": [insight.to_dict() for insight in insights],
        "total_count": len(insights)
    }

@router.get("/statistics")
async def get_dream_statistics(
    days_back: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get dream journal statistics"""
    stats = dream_service.get_dream_statistics(
        user_id=current_user.id,
        days_back=days_back
    )
    
    return {
        "message": "Dream statistics retrieved successfully",
        "statistics": stats,
        "period_days": days_back
    }

@router.get("/analysis/{entry_id}")
async def get_dream_analysis(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed analysis for a specific dream entry"""
    # Get the dream entry first to verify ownership
    entries = dream_service.get_user_dream_entries(current_user.id, limit=1000)
    entry = next((e for e in entries if e.id == entry_id), None)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream entry not found"
        )
    
    # Perform fresh analysis
    analysis = dream_service.analyze_dream_content(entry.dream_text, entry.language)
    
    return {
        "message": "Dream analysis retrieved successfully",
        "entry_id": entry_id,
        "analysis": analysis.to_dict(),
        "learning_opportunities": entry.learning_opportunities,
        "vocabulary_suggestions": entry.vocabulary_suggestions,
        "cultural_insights": entry.cultural_insights
    }

@router.get("/recommendations")
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_user)
):
    """Get personalized learning recommendations based on dream patterns"""
    # Get recent insights
    insights = dream_service.get_user_learning_insights(current_user.id)
    
    # Get statistics
    stats = dream_service.get_dream_statistics(current_user.id, days_back=30)
    
    # Generate recommendations based on patterns
    recommendations = []
    
    if stats['total_dreams'] == 0:
        recommendations = [
            "Start recording your dreams to unlock personalized language learning insights",
            "Try keeping a dream journal by your bedside",
            "Record dreams immediately upon waking for best recall"
        ]
    else:
        # Analyze patterns and generate recommendations
        if stats['total_dreams'] < 5:
            recommendations.append("Try to record more dreams for better pattern analysis")
        
        # Theme-based recommendations
        common_themes = [theme[0] for theme in stats['most_common_themes'][:3]]
        if 'family' in str(common_themes).lower():
            recommendations.append("Focus on family-related vocabulary - it appears frequently in your dreams")
        
        if 'work' in str(common_themes).lower() or 'school' in str(common_themes).lower():
            recommendations.append("Practice professional vocabulary based on your work/school dreams")
        
        # Emotional pattern recommendations
        if stats['emotional_patterns']:
            dominant_emotion = max(stats['emotional_patterns'], key=stats['emotional_patterns'].get)
            recommendations.append(f"Practice expressing {dominant_emotion} emotions - they're prominent in your dreams")
        
        # Learning insights recommendations
        vocabulary_insights = [i for i in insights if i.insight_type == 'vocabulary']
        if vocabulary_insights:
            recommendations.append("Focus on vocabulary expansion based on your dream content analysis")
    
    return {
        "message": "Personalized recommendations generated",
        "recommendations": recommendations,
        "based_on": {
            "total_dreams": stats['total_dreams'],
            "insights_count": len(insights),
            "analysis_period": "30 days"
        }
    }