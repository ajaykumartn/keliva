"""
Voice Biometrics Router
Handles voice tracking, pronunciation analysis, and improvement metrics
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from models.user import User
from services.voice_biometrics import VoiceBiometricService, VoiceFeatures
from routers.auth import get_current_user

router = APIRouter(prefix="/api/voice-biometrics", tags=["voice_biometrics"])

# Initialize service
voice_service = VoiceBiometricService(os.getenv("DB_PATH", "keliva.db"))

class VoiceSampleData(BaseModel):
    language: str
    text_spoken: str
    expected_text: str
    recording_quality: Optional[float] = 0.8

class PronunciationRequest(BaseModel):
    language: str = "en"
    days_back: int = 30

@router.post("/initialize-profile")
async def initialize_voice_profile(
    voice_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Initialize voice biometric profile for user"""
    try:
        # Read audio file
        audio_data = await voice_file.read()
        
        # Extract voice features (simplified - in production use proper audio processing)
        voice_features = voice_service.extract_voice_features(audio_data)
        
        # Create voice profile
        voice_signature = voice_service.create_voice_profile(current_user.id, voice_features)
        
        if not voice_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create voice profile"
            )
        
        return {
            "message": "Voice profile initialized successfully",
            "voice_signature": voice_signature,
            "baseline_features": voice_features.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice file: {str(e)}"
        )

@router.post("/analyze-sample")
async def analyze_voice_sample(
    voice_file: UploadFile = File(...),
    sample_data: str = None,  # JSON string of VoiceSampleData
    current_user: User = Depends(get_current_user)
):
    """Analyze a voice sample for pronunciation and improvement tracking"""
    try:
        import json
        
        # Parse sample data
        if sample_data:
            data = json.loads(sample_data)
            sample_info = VoiceSampleData(**data)
        else:
            sample_info = VoiceSampleData(
                language="en",
                text_spoken="sample text",
                expected_text="sample text"
            )
        
        # Read and process audio
        audio_data = await voice_file.read()
        voice_features = voice_service.extract_voice_features(audio_data)
        
        # Analyze pronunciation
        pronunciation_scores = voice_service.analyze_pronunciation(
            text_spoken=sample_info.text_spoken,
            voice_features=voice_features,
            expected_text=sample_info.expected_text,
            language=sample_info.language
        )
        
        # Store voice sample
        sample_id = voice_service.store_voice_sample(
            user_id=current_user.id,
            language=sample_info.language,
            text_spoken=sample_info.text_spoken,
            voice_features=voice_features,
            pronunciation_scores=pronunciation_scores,
            recording_quality=sample_info.recording_quality
        )
        
        return {
            "message": "Voice sample analyzed successfully",
            "sample_id": sample_id,
            "voice_features": voice_features.to_dict(),
            "pronunciation_scores": pronunciation_scores,
            "overall_score": sum(pronunciation_scores.values()) / len(pronunciation_scores) if pronunciation_scores else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing voice sample: {str(e)}"
        )

@router.get("/pronunciation-progress")
async def get_pronunciation_progress(
    language: str = "en",
    days_back: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get pronunciation progress for user"""
    progress = voice_service.get_pronunciation_progress(
        user_id=current_user.id,
        language=language,
        days_back=days_back
    )
    
    if not progress:
        return {
            "message": "No pronunciation data found",
            "progress": None
        }
    
    return {
        "message": "Pronunciation progress retrieved successfully",
        "progress": progress.to_dict()
    }

@router.get("/voice-profile")
async def get_voice_profile(current_user: User = Depends(get_current_user)):
    """Get complete voice biometric profile"""
    profile = voice_service.get_voice_biometric_profile(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice profile not found. Please initialize your voice profile first."
        )
    
    return {
        "message": "Voice profile retrieved successfully",
        "profile": profile.to_dict()
    }

@router.get("/improvement-timeline")
async def get_improvement_timeline(
    days_back: int = 90,
    current_user: User = Depends(get_current_user)
):
    """Get voice improvement timeline for visualization"""
    timeline = voice_service.get_voice_improvement_timeline(
        user_id=current_user.id,
        days_back=days_back
    )
    
    return {
        "message": "Improvement timeline retrieved successfully",
        "timeline": timeline,
        "total_samples": len(timeline)
    }

@router.get("/pronunciation-recommendations")
async def get_pronunciation_recommendations(
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Get personalized pronunciation recommendations"""
    progress = voice_service.get_pronunciation_progress(
        user_id=current_user.id,
        language=language,
        days_back=30
    )
    
    if not progress:
        return {
            "message": "No data available for recommendations",
            "recommendations": [
                "Start by recording some voice samples to get personalized recommendations",
                "Practice basic pronunciation exercises daily",
                "Focus on clear articulation of vowel sounds"
            ]
        }
    
    return {
        "message": "Pronunciation recommendations generated",
        "recommendations": progress.recommendations,
        "problem_areas": progress.problem_areas,
        "strengths": progress.strengths,
        "overall_improvement": progress.overall_improvement
    }

@router.get("/voice-consistency-score")
async def get_voice_consistency_score(current_user: User = Depends(get_current_user)):
    """Get voice consistency score (how consistent user's voice patterns are)"""
    profile = voice_service.get_voice_biometric_profile(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice profile not found"
        )
    
    return {
        "message": "Voice consistency score retrieved",
        "consistency_score": profile.voice_consistency_score,
        "interpretation": {
            "score": profile.voice_consistency_score,
            "level": "High" if profile.voice_consistency_score > 0.8 else "Medium" if profile.voice_consistency_score > 0.6 else "Low",
            "description": "High consistency indicates stable voice patterns and good recording conditions"
        }
    }

@router.post("/compare-pronunciation")
async def compare_pronunciation(
    target_text: str,
    voice_file: UploadFile = File(...),
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Compare user's pronunciation with target text"""
    try:
        # Process audio
        audio_data = await voice_file.read()
        voice_features = voice_service.extract_voice_features(audio_data)
        
        # For this demo, we'll simulate speech-to-text
        # In production, integrate with actual STT service
        simulated_transcription = target_text  # Simplified
        
        # Analyze pronunciation
        pronunciation_scores = voice_service.analyze_pronunciation(
            text_spoken=simulated_transcription,
            voice_features=voice_features,
            expected_text=target_text,
            language=language
        )
        
        # Calculate overall accuracy
        overall_accuracy = sum(pronunciation_scores.values()) / len(pronunciation_scores) if pronunciation_scores else 0
        
        # Generate feedback
        feedback = []
        if overall_accuracy > 0.9:
            feedback.append("Excellent pronunciation! Keep up the great work.")
        elif overall_accuracy > 0.7:
            feedback.append("Good pronunciation with room for improvement.")
        else:
            feedback.append("Focus on clearer articulation. Practice slowly first.")
        
        return {
            "message": "Pronunciation comparison completed",
            "target_text": target_text,
            "transcribed_text": simulated_transcription,
            "overall_accuracy": overall_accuracy,
            "detailed_scores": pronunciation_scores,
            "feedback": feedback,
            "voice_features": voice_features.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing pronunciation: {str(e)}"
        )