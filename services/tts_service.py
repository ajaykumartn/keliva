"""
TTS Service - Text-to-Speech Integration
Uses Edge TTS (100% FREE) for all languages: English, Kannada, and Telugu
Provides audio streaming functionality for progressive delivery
"""
from typing import AsyncGenerator, Optional
from dataclasses import dataclass
from enum import Enum
import io
import edge_tts
from .polyglot_engine import Language


# TTS Configuration Constants
class TTSConfig:
    """Configuration for TTS voices and settings"""
    
    # Voice IDs for each language (Edge TTS voices)
    VOICES = {
        Language.ENGLISH: "en-US-AriaNeural",
        Language.KANNADA: "kn-IN-GaganNeural",
        Language.TELUGU: "te-IN-ShrutiNeural"
    }
    
    # Speech rate (can be adjusted: -50% to +100%)
    RATE = "+0%"
    
    # Volume (can be adjusted: -50% to +100%)
    VOLUME = "+0%"
    
    # Pitch (can be adjusted: -50Hz to +50Hz)
    PITCH = "+0Hz"


@dataclass
class AudioChunk:
    """Represents a chunk of audio data for streaming"""
    data: bytes
    sequence: int
    is_final: bool


class TTSService:
    """
    Text-to-Speech service using Edge TTS (100% FREE).
    
    Features:
    - Multi-language support (English, Kannada, Telugu)
    - Audio streaming for progressive delivery
    - Natural-sounding voices
    - Zero cost operation
    """
    
    def __init__(self):
        """Initialize TTS service with default configuration"""
        self.config = TTSConfig()
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS processing by removing problematic characters.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text suitable for TTS
        """
        import re
        
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove or replace problematic characters
        # Keep letters, numbers, basic punctuation, and common Unicode ranges
        # Remove control characters and unusual symbols
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Replace multiple punctuation with single
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{4,}', '...', text)
        
        # Remove emojis (they can cause TTS issues)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # Limit text length to prevent timeout
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text.strip()
    
    async def text_to_speech(
        self,
        text: str,
        language: Language,
        stream: bool = True
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Converts text to speech audio.
        
        Args:
            text: Text to convert to speech
            language: Target language for speech synthesis
            stream: If True, yields audio chunks progressively; if False, yields complete audio
            
        Yields:
            AudioChunk objects containing audio data
            
        Raises:
            ValueError: If language is not supported
            Exception: If TTS generation fails
        """
        if language not in self.config.VOICES:
            raise ValueError(f"Unsupported language: {language}")
        
        voice = self.config.VOICES[language]
        
        # Validate text is not empty
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Clean text for TTS - remove problematic characters
            clean_text = self._clean_text_for_tts(text)
            
            if not clean_text:
                raise ValueError("Text is empty after cleaning")
            
            # Create TTS communicator
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=voice,
                rate=self.config.RATE,
                volume=self.config.VOLUME,
                pitch=self.config.PITCH
            )
            
            # Stream audio chunks
            sequence = 0
            has_audio = False
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data = chunk["data"]
                    has_audio = True
                    
                    yield AudioChunk(
                        data=audio_data,
                        sequence=sequence,
                        is_final=False
                    )
                    sequence += 1
            
            # Send final marker only if we got audio
            if has_audio:
                yield AudioChunk(
                    data=b"",
                    sequence=sequence,
                    is_final=True
                )
            else:
                # Try with fallback voice if no audio received
                fallback_voice = "en-US-JennyNeural"
                communicate_fallback = edge_tts.Communicate(
                    text=clean_text,
                    voice=fallback_voice,
                    rate=self.config.RATE,
                    volume=self.config.VOLUME,
                    pitch=self.config.PITCH
                )
                
                async for chunk in communicate_fallback.stream():
                    if chunk["type"] == "audio":
                        audio_data = chunk["data"]
                        has_audio = True
                        
                        yield AudioChunk(
                            data=audio_data,
                            sequence=sequence,
                            is_final=False
                        )
                        sequence += 1
                
                if has_audio:
                    yield AudioChunk(
                        data=b"",
                        sequence=sequence,
                        is_final=True
                    )
                else:
                    raise Exception("No audio data received from TTS service")
            
        except edge_tts.exceptions.NoAudioReceived:
            # Specific handling for NoAudioReceived error
            raise Exception("TTS service could not generate audio for this text. Try simplifying the text.")
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")
    
    async def text_to_speech_bytes(
        self,
        text: str,
        language: Language
    ) -> bytes:
        """
        Converts text to speech and returns complete audio as bytes.
        Useful for non-streaming scenarios.
        
        Args:
            text: Text to convert to speech
            language: Target language for speech synthesis
            
        Returns:
            Complete audio data as bytes
            
        Raises:
            ValueError: If language is not supported
            Exception: If TTS generation fails
        """
        if language not in self.config.VOICES:
            raise ValueError(f"Unsupported language: {language}")
        
        voice = self.config.VOICES[language]
        
        try:
            # Create TTS communicator
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=self.config.RATE,
                volume=self.config.VOLUME,
                pitch=self.config.PITCH
            )
            
            # Collect all audio chunks
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            
            return audio_buffer.getvalue()
            
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")
    
    def get_voice_for_language(self, language: Language) -> str:
        """
        Gets the voice ID for a specific language.
        
        Args:
            language: Target language
            
        Returns:
            Voice ID string
            
        Raises:
            ValueError: If language is not supported
        """
        if language not in self.config.VOICES:
            raise ValueError(f"Unsupported language: {language}")
        
        return self.config.VOICES[language]
    
    def set_voice_settings(
        self,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> None:
        """
        Updates voice settings for TTS generation.
        
        Args:
            rate: Speech rate (e.g., "+10%", "-20%")
            volume: Speech volume (e.g., "+10%", "-20%")
            pitch: Speech pitch (e.g., "+5Hz", "-10Hz")
        """
        if rate is not None:
            self.config.RATE = rate
        if volume is not None:
            self.config.VOLUME = volume
        if pitch is not None:
            self.config.PITCH = pitch
    
    async def save_to_file(
        self,
        text: str,
        language: Language,
        output_path: str
    ) -> None:
        """
        Converts text to speech and saves to a file.
        
        Args:
            text: Text to convert to speech
            language: Target language for speech synthesis
            output_path: Path where audio file will be saved
            
        Raises:
            ValueError: If language is not supported
            Exception: If TTS generation or file save fails
        """
        if language not in self.config.VOICES:
            raise ValueError(f"Unsupported language: {language}")
        
        voice = self.config.VOICES[language]
        
        try:
            # Create TTS communicator
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=self.config.RATE,
                volume=self.config.VOLUME,
                pitch=self.config.PITCH
            )
            
            # Save to file
            await communicate.save(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to save TTS audio: {str(e)}")
