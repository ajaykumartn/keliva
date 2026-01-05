"""
Speech-to-Text (STT) Service
Handles audio transcription for voice messages
"""
import os
import logging
import requests
from typing import Optional
import tempfile
import subprocess

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using GROQ Whisper API"""
    
    def __init__(self):
        """Initialize STT service"""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.base_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text using GROQ Whisper API
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            # Convert audio to supported format if needed
            converted_path = await self._convert_audio_format(audio_file_path)
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Read the audio file
            with open(converted_path, 'rb') as audio_file:
                files = {
                    'file': ('audio.wav', audio_file, 'audio/wav'),
                    'model': (None, 'whisper-large-v3'),
                    # Remove language parameter to let GROQ auto-detect
                    'response_format': (None, 'text')
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        files=files
                    )
                    
                    if response.status_code == 200:
                        transcription = response.text.strip()
                        if transcription:
                            logger.info(f"Transcription successful: {transcription[:100]}...")
                            return transcription
                        else:
                            logger.warning("Transcription returned empty result")
                            return None
                    else:
                        logger.error(f"GROQ API error: {response.status_code} - {response.text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
        finally:
            # Clean up converted file if it was created
            if 'converted_path' in locals() and converted_path != audio_file_path:
                try:
                    os.unlink(converted_path)
                except:
                    pass
    
    async def _convert_audio_format(self, input_path: str) -> str:
        """
        Convert audio to WAV format if needed
        
        Args:
            input_path: Path to input audio file
            
        Returns:
            Path to converted audio file (or original if no conversion needed)
        """
        try:
            # Check if ffmpeg is available
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                logger.warning("ffmpeg not available, using original file")
                return input_path
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg not found or timeout, using original file")
            return input_path
        
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Convert to WAV using ffmpeg with better settings for speech
            cmd = [
                'ffmpeg', '-i', input_path,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',          # 16kHz sample rate (good for speech)
                '-ac', '1',              # Mono channel
                '-af', 'volume=2.0',     # Boost volume slightly
                '-y',                    # Overwrite output file
                '-loglevel', 'error',    # Reduce ffmpeg output
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Audio converted to WAV format for better transcription")
                return output_path
            else:
                logger.warning(f"Audio conversion failed: {result.stderr}")
                return input_path
                
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return input_path
    
    def is_available(self) -> bool:
        """Check if STT service is available"""
        return bool(self.api_key)


# Fallback STT service without external dependencies
class FallbackSTTService:
    """Fallback STT service that returns a helpful message"""
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Return a helpful message for voice messages"""
        return "I received your voice message, but I need text to respond properly. Please send me a text message!"
    
    def is_available(self) -> bool:
        """Always available as fallback"""
        return True


def create_stt_service() -> STTService:
    """Create appropriate STT service based on available configuration"""
    try:
        return STTService()
    except ValueError:
        logger.warning("GROQ API key not available, using fallback STT service")
        return FallbackSTTService()