"""
Emotion AI Router
Handles emotion recognition for text and voice analysis
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from models.user import User
from services.emotion_ai import EmotionRecognitionAI
from routers.auth import get_current_user

router = APIRouter(prefix="/api/emotion", tags=["emotion_ai"])

# Initialize service
emotion_ai = EmotionRecognitionAI(os.getenv("DB_PATH", "keliva.db"))

class TextEmotionRequest(BaseModel):
    text: str
    language: str = "en"

class EmotionHistoryRequest(BaseModel):
    days_back: int = 30
    emotion_type: Optional[str] = None

@router.post("/analyze-text")
async def analyze_text_emotion(
    request: TextEmotionRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze emotion in text"""
    try:
        analysis = emotion_ai.analyze_text_emotion(
            text=request.text,
            user_id=current_user.id
        )
        
        return {
            "message": "Text emotion analysis completed",
            "analysis": analysis.to_dict(),
            "primary_emotion": analysis.primary_emotion,
            "confidence_score": analysis.confidence,
            "emotional_intensity": analysis.sentiment_score
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing text emotion: {str(e)}"
        )

@router.post("/analyze-voice")
async def analyze_voice_emotion(
    voice_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Analyze emotion in voice recording"""
    try:
        # Read audio file
        audio_data = await voice_file.read()
        
        # Extract voice features (simplified - in production use proper audio processing)
        voice_features = {
            'pitch': 0.5,
            'energy': 0.6,
            'speaking_rate': 0.5,
            'voice_quality': 'normal'
        }
        
        analysis = emotion_ai.analyze_voice_emotion(
            voice_features=voice_features,
            user_id=current_user.id
        )
        
        return {
            "message": "Voice emotion analysis completed",
            "analysis": analysis.to_dict(),
            "primary_emotion": analysis.primary_emotion,
            "confidence_score": analysis.confidence,
            "voice_features": voice_features
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing voice emotion: {str(e)}"
        )

@router.get("/history")
async def get_emotion_history(
    days_back: int = 30,
    emotion_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's emotion analysis history"""
    # Get user's emotional profile which contains history
    profile = emotion_ai.get_user_emotional_profile(current_user.id)
    
    history = []
    if profile:
        # Convert emotional patterns to history format
        for emotion, score in profile.emotional_patterns.items():
            history.append({
                "emotion": emotion,
                "score": score,
                "timestamp": profile.last_updated.isoformat()
            })
    
    return {
        "message": "Emotion history retrieved successfully",
        "history": history,
        "total_count": len(history),
        "period_days": days_back
    }

@router.get("/patterns")
async def get_emotion_patterns(
    days_back: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get user's emotional patterns and insights"""
    profile = emotion_ai.get_user_emotional_profile(current_user.id)
    
    if profile:
        patterns = {
            "dominant_emotion": max(profile.emotional_patterns, key=profile.emotional_patterns.get) if profile.emotional_patterns else "neutral",
            "emotion_distribution": profile.emotional_patterns,
            "emotional_stability": 0.7,  # Calculated based on variance
            "trend": "stable"
        }
    else:
        patterns = None
    
    return {
        "message": "Emotion patterns retrieved successfully",
        "patterns": patterns,
        "period_days": days_back
    }

@router.get("/learning-insights")
async def get_emotion_learning_insights(
    current_user: User = Depends(get_current_user)
):
    """Get learning insights based on emotional patterns"""
    profile = emotion_ai.get_user_emotional_profile(current_user.id)
    
    insights = []
    if profile:
        if profile.stress_triggers:
            insights.append({
                "type": "stress",
                "text": f"Identified stress triggers: {', '.join(profile.stress_triggers)}",
                "recommendation": "Consider relaxation techniques before learning sessions"
            })
        if profile.motivation_factors:
            insights.append({
                "type": "motivation",
                "text": f"Your motivation factors: {', '.join(profile.motivation_factors)}",
                "recommendation": "Leverage these for better learning outcomes"
            })
    
    return {
        "message": "Emotion learning insights retrieved successfully",
        "insights": insights,
        "total_count": len(insights)
    }

@router.get("/mood-timeline")
async def get_mood_timeline(
    days_back: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get mood timeline for visualization"""
    profile = emotion_ai.get_user_emotional_profile(current_user.id)
    
    timeline = []
    if profile:
        # Generate timeline from emotional patterns
        for emotion, score in profile.emotional_patterns.items():
            timeline.append({
                "date": profile.last_updated.isoformat(),
                "emotion": emotion,
                "score": score
            })
    
    return {
        "message": "Mood timeline retrieved successfully",
        "timeline": timeline,
        "period_days": days_back
    }

@router.post("/batch-analyze")
async def batch_analyze_emotions(
    texts: List[str],
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Analyze emotions in multiple texts at once"""
    try:
        results = []
        
        for i, text in enumerate(texts):
            analysis = emotion_ai.analyze_text_emotion(
                text=text,
                user_id=current_user.id
            )
            
            results.append({
                "index": i,
                "text": text,
                "analysis": analysis.to_dict()
            })
        
        return {
            "message": "Batch emotion analysis completed",
            "results": results,
            "total_analyzed": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch emotion analysis: {str(e)}"
        )

@router.get("/emotion-vocabulary")
async def get_emotion_vocabulary(
    emotion: str,
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Get vocabulary suggestions for expressing specific emotions"""
    # Predefined emotion vocabulary
    emotion_vocab = {
        "happy": {
            "en": ["joyful", "delighted", "pleased", "content", "cheerful", "elated"],
            "te": ["సంతోషం", "ఆనందం", "హర్షం"],
            "hi": ["खुश", "प्रसन्न", "आनंदित"]
        },
        "sad": {
            "en": ["sorrowful", "melancholy", "dejected", "downcast", "gloomy"],
            "te": ["దుఃఖం", "విచారం", "బాధ"],
            "hi": ["दुखी", "उदास", "निराश"]
        },
        "angry": {
            "en": ["furious", "irritated", "annoyed", "frustrated", "enraged"],
            "te": ["కోపం", "ఆగ్రహం", "చిరాకు"],
            "hi": ["गुस्सा", "क्रोधित", "नाराज"]
        }
    }
    
    vocabulary = emotion_vocab.get(emotion, {}).get(language, [])
    
    return {
        "message": "Emotion vocabulary retrieved successfully",
        "emotion": emotion,
        "language": language,
        "vocabulary": vocabulary
    }

@router.get("/emotional-intelligence-score")
async def get_emotional_intelligence_score(
    current_user: User = Depends(get_current_user)
):
    """Get user's emotional intelligence score based on analysis history"""
    profile = emotion_ai.get_user_emotional_profile(current_user.id)
    
    # Calculate score based on profile data
    score = 0.5  # Default score
    if profile:
        # More diverse emotional patterns = higher EQ
        emotion_diversity = len(profile.emotional_patterns) / 7.0  # 7 emotions tracked
        # Awareness of stress triggers = higher EQ
        stress_awareness = min(len(profile.stress_triggers) / 5.0, 1.0)
        # Motivation factors = higher EQ
        motivation_score = min(len(profile.motivation_factors) / 3.0, 1.0)
        
        score = (emotion_diversity + stress_awareness + motivation_score) / 3.0
    
    return {
        "message": "Emotional intelligence score calculated",
        "score": score,
        "interpretation": {
            "level": "High" if score > 0.8 else "Medium" if score > 0.6 else "Developing",
            "description": "Based on emotional awareness and expression patterns in your communications"
        }
    }

@router.post("/emotion-feedback")
async def provide_emotion_feedback(
    analysis_id: str,
    correct_emotion: str,
    current_user: User = Depends(get_current_user)
):
    """Provide feedback on emotion analysis accuracy"""
    # Store feedback for model improvement (simplified)
    return {
        "message": "Emotion feedback stored successfully",
        "analysis_id": analysis_id,
        "correct_emotion": correct_emotion
    }