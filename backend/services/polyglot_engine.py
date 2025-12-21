"""
Polyglot Engine Service
Provides language detection and switching for English, Kannada, and Telugu
Uses Groq API (FREE - 14,000 requests/day for 8B model)
"""
from typing import Optional
from enum import Enum
from dataclasses import dataclass
import os
import json
import re
from groq import AsyncGroq
from .rate_limiter import get_rate_limiter, GroqModel, RateLimitExceededError


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    KANNADA = "kn"
    TELUGU = "te"
    UNKNOWN = "unknown"


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    language: Language
    confidence: float  # 0.0 to 1.0
    detected_by: str  # "llm" or "unicode"


class PolyglotEngine:
    """
    Language detection and switching engine.
    Uses LLM-based detection with Unicode fallback for Kannada/Telugu.
    """
    
    # Unicode ranges for Indian languages
    KANNADA_RANGE = (0x0C80, 0x0CFF)  # Kannada Unicode block
    TELUGU_RANGE = (0x0C00, 0x0C7F)   # Telugu Unicode block
    
    # Confidence threshold for language detection
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Polyglot Engine with Groq API client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment")
        
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"  # FREE - 14,000 requests/day
        self.rate_limiter = get_rate_limiter()
    
    async def detect_language(self, text: str) -> Language:
        """
        Detects the primary language of input text.
        
        Uses a two-stage approach:
        1. Unicode character analysis (fast, for Kannada/Telugu)
        2. LLM-based detection (accurate, for all languages)
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language enum (ENGLISH, KANNADA, TELUGU)
            Defaults to ENGLISH if confidence < 0.7
        """
        if not text or not text.strip():
            return Language.ENGLISH
        
        # Stage 1: Try Unicode-based detection (fast path)
        unicode_result = self._detect_by_unicode(text)
        if unicode_result.confidence >= self.CONFIDENCE_THRESHOLD:
            return unicode_result.language
        
        # Stage 2: Use LLM for more accurate detection
        try:
            llm_result = await self._detect_by_llm(text)
            
            # If LLM confidence is high enough, use it
            if llm_result.confidence >= self.CONFIDENCE_THRESHOLD:
                return llm_result.language
            
            # If both methods have low confidence, default to English
            return Language.ENGLISH
            
        except Exception as e:
            # Fallback to Unicode result or English
            if unicode_result.language != Language.UNKNOWN:
                return unicode_result.language
            return Language.ENGLISH
    
    def _detect_by_unicode(self, text: str) -> LanguageDetectionResult:
        """
        Detects language based on Unicode character ranges.
        Fast method for identifying Kannada and Telugu scripts.
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult with language and confidence
        """
        # Count characters in each script
        kannada_count = 0
        telugu_count = 0
        total_chars = 0
        
        for char in text:
            code_point = ord(char)
            
            # Skip whitespace and punctuation
            if char.isspace() or not char.isalnum():
                continue
            
            total_chars += 1
            
            # Check if character is in Kannada range
            if self.KANNADA_RANGE[0] <= code_point <= self.KANNADA_RANGE[1]:
                kannada_count += 1
            
            # Check if character is in Telugu range
            elif self.TELUGU_RANGE[0] <= code_point <= self.TELUGU_RANGE[1]:
                telugu_count += 1
        
        # Calculate confidence based on script character percentage
        if total_chars == 0:
            return LanguageDetectionResult(
                language=Language.UNKNOWN,
                confidence=0.0,
                detected_by="unicode"
            )
        
        kannada_ratio = kannada_count / total_chars
        telugu_ratio = telugu_count / total_chars
        
        # If more than 30% of characters are in a specific script, consider it that language
        if kannada_ratio > 0.3:
            return LanguageDetectionResult(
                language=Language.KANNADA,
                confidence=kannada_ratio,
                detected_by="unicode"
            )
        
        if telugu_ratio > 0.3:
            return LanguageDetectionResult(
                language=Language.TELUGU,
                confidence=telugu_ratio,
                detected_by="unicode"
            )
        
        # If mostly ASCII/Latin characters, likely English (but low confidence)
        ascii_count = sum(1 for c in text if ord(c) < 128 and c.isalnum())
        ascii_ratio = ascii_count / total_chars if total_chars > 0 else 0
        
        if ascii_ratio > 0.7:
            return LanguageDetectionResult(
                language=Language.ENGLISH,
                confidence=ascii_ratio * 0.8,  # Reduce confidence since it's just a guess
                detected_by="unicode"
            )
        
        return LanguageDetectionResult(
            language=Language.UNKNOWN,
            confidence=0.0,
            detected_by="unicode"
        )
    
    async def _detect_by_llm(self, text: str) -> LanguageDetectionResult:
        """
        Detects language using LLM analysis.
        More accurate for mixed scripts and context-based detection.
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult with language and confidence
        """
        prompt = f"""Identify the primary language of this text. Respond with ONLY a JSON object in this exact format:

{{
  "language": "english" | "kannada" | "telugu",
  "confidence": 0.0 to 1.0
}}

Text to analyze: "{text}"

Rules:
- If the text is primarily in English (even with some Indian language words), return "english"
- If the text is primarily in Kannada script, return "kannada"
- If the text is primarily in Telugu script, return "telugu"
- Confidence should be 1.0 if you're certain, lower if mixed or unclear
- Return ONLY the JSON, no other text"""
        
        try:
            # Check rate limit before making API call
            self.rate_limiter.check_and_increment(GroqModel.LLAMA_8B)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a language detection expert. Respond only with JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent detection
                max_tokens=100
            )
            
            llm_output = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result = self._parse_llm_detection(llm_output)
            return result
            
        except RateLimitExceededError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            # Return unknown with zero confidence on error
            return LanguageDetectionResult(
                language=Language.UNKNOWN,
                confidence=0.0,
                detected_by="llm"
            )
    
    def _parse_llm_detection(self, llm_output: str) -> LanguageDetectionResult:
        """
        Parses LLM response for language detection.
        
        Args:
            llm_output: Raw output from LLM
            
        Returns:
            LanguageDetectionResult
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            data = json.loads(json_str)
            
            # Map language string to enum
            language_str = data.get("language", "").lower()
            language_map = {
                "english": Language.ENGLISH,
                "kannada": Language.KANNADA,
                "telugu": Language.TELUGU
            }
            
            language = language_map.get(language_str, Language.UNKNOWN)
            confidence = float(data.get("confidence", 0.0))
            
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            return LanguageDetectionResult(
                language=language,
                confidence=confidence,
                detected_by="llm"
            )
            
        except Exception as e:
            return LanguageDetectionResult(
                language=Language.UNKNOWN,
                confidence=0.0,
                detected_by="llm"
            )
