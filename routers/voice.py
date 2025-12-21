"""
Voice API Router
Handles text-to-speech and voice-related functionality
"""
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import logging
import asyncio
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])


class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    voice: Optional[str] = "en-US-AriaNeural"
    rate: Optional[str] = "medium"
    pitch: Optional[str] = "medium"


class VoicePracticeRequest(BaseModel):
    """Voice practice request"""
    text: str
    user_audio_url: Optional[str] = None
    session_id: Optional[str] = None


class STTRequest(BaseModel):
    """Speech-to-text request"""
    audio_data: Optional[str] = None  # Base64 encoded audio
    language: Optional[str] = "en-US"
    session_id: Optional[str] = None


@router.post("/tts")
async def text_to_speech(tts_request: TTSRequest):
    """
    Convert text to speech using Web Speech API
    
    Args:
        tts_request: TTS request with text and voice parameters
        
    Returns:
        Response with TTS configuration for frontend
    """
    try:
        # Return configuration for the frontend to speak the text
        return {
            "status": "success",
            "speak_text": tts_request.text,
            "voice_config": {
                "voice": tts_request.voice,
                "rate": 1.0 if tts_request.rate == "medium" else 0.8 if tts_request.rate == "slow" else 1.2,
                "pitch": 1.0 if tts_request.pitch == "medium" else 0.8 if tts_request.pitch == "low" else 1.2,
                "volume": 1.0
            },
            "should_speak": True,
            "use_web_speech_api": True
        }
        
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate speech: {str(e)}"
        )


@router.post("/practice/feedback")
async def voice_practice_feedback(practice_request: VoicePracticeRequest):
    """
    Provide feedback on voice practice
    
    Args:
        practice_request: Voice practice request with text and audio
        
    Returns:
        Practice feedback and suggestions
    """
    try:
        # Simple feedback for now - in a full implementation, this would
        # analyze the audio and compare with the target text
        feedback = {
            "status": "success",
            "original_text": practice_request.text,
            "feedback": {
                "pronunciation_score": 85,  # Mock score
                "suggestions": [
                    "Focus on clear consonant sounds",
                    "Maintain steady pace",
                    "Good overall pronunciation"
                ],
                "areas_to_improve": [
                    "Word stress patterns",
                    "Intonation"
                ]
            },
            "next_exercise": "Try reading this text with emphasis on stressed syllables"
        }
        
        return feedback
        
    except Exception as e:
        logger.error(f"Error in voice practice feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provide voice feedback: {str(e)}"
        )


@router.get("/voices")
async def get_available_voices():
    """
    Get list of available TTS voices
    
    Returns:
        List of available voices for different languages
    """
    try:
        voices = {
            "english": [
                {"id": "en-US-AriaNeural", "name": "Aria (US Female)", "language": "en-US"},
                {"id": "en-US-GuyNeural", "name": "Guy (US Male)", "language": "en-US"},
                {"id": "en-GB-SoniaNeural", "name": "Sonia (UK Female)", "language": "en-GB"},
                {"id": "en-IN-NeerjaNeural", "name": "Neerja (India Female)", "language": "en-IN"}
            ],
            "kannada": [
                {"id": "kn-IN-GaganNeural", "name": "Gagan (Male)", "language": "kn-IN"},
                {"id": "kn-IN-SapnaNeural", "name": "Sapna (Female)", "language": "kn-IN"}
            ],
            "telugu": [
                {"id": "te-IN-ShrutiNeural", "name": "Shruti (Female)", "language": "te-IN"},
                {"id": "te-IN-MohanNeural", "name": "Mohan (Male)", "language": "te-IN"}
            ]
        }
        
        return {
            "status": "success",
            "voices": voices,
            "default_voice": "en-US-AriaNeural",
            "use_web_speech_api": True
        }
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voices: {str(e)}"
        )


@router.post("/exercises")
async def get_voice_exercises():
    """
    Get voice practice exercises
    
    Returns:
        List of voice practice exercises
    """
    try:
        exercises = [
            {
                "id": 1,
                "title": "Basic Pronunciation",
                "text": "The quick brown fox jumps over the lazy dog.",
                "focus": "Clear consonants and vowels",
                "difficulty": "beginner"
            },
            {
                "id": 2,
                "title": "Word Stress",
                "text": "Photography, photographer, photographic - notice the stress patterns.",
                "focus": "Word stress and rhythm",
                "difficulty": "intermediate"
            },
            {
                "id": 3,
                "title": "Intonation Practice",
                "text": "Are you coming to the party? Yes, I am! That's wonderful news.",
                "focus": "Question and statement intonation",
                "difficulty": "intermediate"
            },
            {
                "id": 4,
                "title": "Tongue Twisters",
                "text": "She sells seashells by the seashore.",
                "focus": "Articulation and speed",
                "difficulty": "advanced"
            }
        ]
        
        return {
            "status": "success",
            "exercises": exercises,
            "total_count": len(exercises)
        }
        
    except Exception as e:
        logger.error(f"Error getting voice exercises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice exercises: {str(e)}"
        )


@router.post("/stt")
async def speech_to_text(stt_request: STTRequest):
    """
    Convert speech to text using Web Speech API
    
    Args:
        stt_request: STT request with audio data
        
    Returns:
        Instructions for frontend to use Web Speech API
    """
    try:
        return {
            "status": "success",
            "message": "Use Web Speech Recognition API",
            "language": stt_request.language,
            "use_web_speech_api": True,
            "instructions": {
                "method": "webkitSpeechRecognition",
                "language": stt_request.language,
                "continuous": True,
                "interim_results": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error in STT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process speech: {str(e)}"
        )


@router.get("/test")
async def test_voice_features():
    """
    Test endpoint to check voice feature availability
    """
    return {
        "status": "success",
        "features": {
            "text_to_speech": {
                "available": True,
                "method": "Web Speech API",
                "test_text": "Hello, this is a test of the text to speech system."
            },
            "speech_to_text": {
                "available": True,
                "method": "Web Speech Recognition API",
                "supported_languages": ["en-US", "en-GB", "hi-IN", "kn-IN", "te-IN"]
            }
        },
        "browser_support": {
            "speechSynthesis": "window.speechSynthesis",
            "SpeechRecognition": "window.SpeechRecognition || window.webkitSpeechRecognition"
        },
        "instructions": {
            "tts": "Use window.speechSynthesis.speak(new SpeechSynthesisUtterance(text))",
            "stt": "Use new (window.SpeechRecognition || window.webkitSpeechRecognition)()"
        }
    }


@router.get("/health")
async def voice_health_check():
    """Health check for voice service"""
    return {
        "status": "ok",
        "service": "voice",
        "tts_available": True,
        "stt_available": True,
        "web_speech_api": True,
        "edge_tts": os.getenv("USE_EDGE_TTS", "true").lower() == "true"
    }