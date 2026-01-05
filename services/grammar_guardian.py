"""
Grammar Guardian Service
Provides intelligent grammar correction using Groq API (FREE - 1,000 requests/day for 70B model)
"""
from typing import List, Optional
from dataclasses import dataclass
import os
import json
import re
import requests
from .rate_limiter import get_rate_limiter, GroqModel, RateLimitExceededError


@dataclass
class GrammarError:
    """Represents a single grammatical error with correction details"""
    start_pos: int
    end_pos: int
    error_type: str  # "tense", "article", "preposition", "subject-verb", etc.
    original_text: str
    corrected_text: str
    explanation: str
    severity: str  # "critical", "moderate", "minor"


@dataclass
class GrammarAnalysis:
    """Complete grammar analysis result"""
    original_text: str
    corrected_text: str
    errors: List[GrammarError]
    overall_score: float  # 0-100


class GrammarGuardian:
    """
    Grammar correction engine using Groq Llama 3.3 70B model.
    Provides detailed error analysis with explanations and categorization.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Grammar Guardian with Groq API client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment")
        
        self.model = "llama-3.1-8b-instant"  # Updated to working model
        try:
            self.rate_limiter = get_rate_limiter()
        except Exception:
            # If rate limiter fails, continue without it
            self.rate_limiter = None
        
    async def analyze_text(self, text: str) -> GrammarAnalysis:
        """
        Analyzes text and returns comprehensive grammar corrections.
        
        Args:
            text: User input text in English
            
        Returns:
            GrammarAnalysis with errors, corrections, and explanations
        """
        if not text or not text.strip():
            return GrammarAnalysis(
                original_text=text,
                corrected_text=text,
                errors=[],
                overall_score=100.0
            )
        
        # Create prompt for grammar analysis
        prompt = self._create_grammar_prompt(text)
        
        try:
            # Check rate limit before making API call (if rate limiter is available)
            if self.rate_limiter:
                try:
                    self.rate_limiter.check_and_increment(GroqModel.LLAMA_8B)
                except:
                    # If rate limiting fails, continue without it
                    pass
            
            # Use direct HTTP request to Groq API
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for consistent corrections
                    "max_tokens": 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_output = result["choices"][0]["message"]["content"]
                analysis = self._parse_llm_response(text, llm_output)
                return analysis
            else:
                # Fallback on API error
                return GrammarAnalysis(
                    original_text=text,
                    corrected_text=text,
                    errors=[],
                    overall_score=0.0
                )
            
        except RateLimitExceededError:
            # Re-raise rate limit errors so they can be handled by the caller
            raise
        except Exception as e:
            # Fallback: return original text with error indication
            return GrammarAnalysis(
                original_text=text,
                corrected_text=text,
                errors=[],
                overall_score=0.0
            )
    
    def _get_system_prompt(self) -> str:
        """Returns the system prompt for grammar correction"""
        return """You are a friendly English grammar expert helping students learn.

Your task is to:
1. Identify ALL grammatical errors in the text
2. Provide corrections with clear explanations
3. Categorize each error by type
4. Be encouraging and supportive in your tone

Return your response in this EXACT JSON format:
{
  "corrected_text": "The fully corrected version of the text",
  "errors": [
    {
      "original": "the exact wrong phrase",
      "corrected": "the corrected phrase",
      "error_type": "tense|article|preposition|subject-verb|word-choice|punctuation|spelling",
      "explanation": "Brief, friendly explanation of the mistake",
      "severity": "critical|moderate|minor"
    }
  ],
  "overall_score": 85
}

Guidelines:
- Be specific about error locations
- Use simple, clear explanations
- Maintain an encouraging tone
- Score: 100 = perfect, 0 = many errors
- If text is perfect, return empty errors array and score 100"""
    
    def _create_grammar_prompt(self, text: str) -> str:
        """Creates the user prompt for grammar analysis"""
        return f"""Please analyze this text for grammatical errors:

"{text}"

Provide corrections in the JSON format specified."""
    
    def _parse_llm_response(self, original_text: str, llm_output: str) -> GrammarAnalysis:
        """
        Parses LLM response and extracts grammar analysis.
        
        Args:
            original_text: The original input text
            llm_output: Raw output from LLM
            
        Returns:
            GrammarAnalysis object
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
            
            # Extract corrected text and score
            corrected_text = data.get("corrected_text", original_text)
            overall_score = float(data.get("overall_score", 100.0))
            
            # Parse errors and calculate positions
            errors = []
            for error_data in data.get("errors", []):
                error = self._create_grammar_error(
                    original_text,
                    corrected_text,
                    error_data
                )
                if error:
                    errors.append(error)
            
            return GrammarAnalysis(
                original_text=original_text,
                corrected_text=corrected_text,
                errors=errors,
                overall_score=overall_score
            )
            
        except Exception as e:
            # Fallback: return minimal analysis
            return GrammarAnalysis(
                original_text=original_text,
                corrected_text=original_text,
                errors=[],
                overall_score=100.0
            )
    
    def _create_grammar_error(
        self,
        original_text: str,
        corrected_text: str,
        error_data: dict
    ) -> Optional[GrammarError]:
        """
        Creates a GrammarError object with position calculation.
        
        Args:
            original_text: Original input text
            corrected_text: Corrected version
            error_data: Error information from LLM
            
        Returns:
            GrammarError object or None if position cannot be determined
        """
        try:
            original_phrase = error_data.get("original", "")
            corrected_phrase = error_data.get("corrected", "")
            
            # Find position of error in original text
            start_pos = original_text.lower().find(original_phrase.lower())
            if start_pos == -1:
                # Try fuzzy matching - find closest match
                start_pos = self._fuzzy_find_position(original_text, original_phrase)
            
            if start_pos == -1:
                # Cannot determine position, skip this error
                return None
            
            end_pos = start_pos + len(original_phrase)
            
            return GrammarError(
                start_pos=start_pos,
                end_pos=end_pos,
                error_type=error_data.get("error_type", "unknown"),
                original_text=original_phrase,
                corrected_text=corrected_phrase,
                explanation=error_data.get("explanation", ""),
                severity=error_data.get("severity", "moderate")
            )
            
        except Exception:
            return None
    
    def _fuzzy_find_position(self, text: str, phrase: str) -> int:
        """
        Attempts to find phrase position using fuzzy matching.
        Useful when LLM returns slightly different text.
        
        Args:
            text: Text to search in
            phrase: Phrase to find
            
        Returns:
            Position or -1 if not found
        """
        # Try word-by-word matching
        words = phrase.split()
        if not words:
            return -1
        
        # Look for first word
        first_word = words[0].lower()
        text_lower = text.lower()
        
        pos = 0
        while pos < len(text_lower):
            pos = text_lower.find(first_word, pos)
            if pos == -1:
                break
            
            # Check if subsequent words match
            remaining_text = text_lower[pos:]
            if all(word.lower() in remaining_text for word in words):
                return pos
            
            pos += 1
        
        return -1
    
    async def get_correction_explanation(
        self,
        error_type: str,
        original: str,
        corrected: str
    ) -> str:
        """
        Generates detailed explanation for a specific correction.
        
        Args:
            error_type: Type of grammatical error
            original: Original incorrect text
            corrected: Corrected text
            
        Returns:
            Detailed explanation string
        """
        prompt = f"""Explain this grammar correction in a friendly, educational way:

Error Type: {error_type}
Original: "{original}"
Corrected: "{corrected}"

Provide a brief, clear explanation suitable for an English learner."""
        
        try:
            # Check rate limit before making API call (if rate limiter is available)
            if self.rate_limiter:
                try:
                    self.rate_limiter.check_and_increment(GroqModel.LLAMA_8B)
                except:
                    # If rate limiting fails, continue without it
                    pass
            
            # Use direct HTTP request to Groq API
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a friendly English tutor. Explain grammar corrections clearly and encouragingly."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.5,
                    "max_tokens": 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"The correct form is '{corrected}' instead of '{original}'."
            
        except RateLimitExceededError:
            # Re-raise rate limit errors
            raise
        except Exception:
            return f"The correct form is '{corrected}' instead of '{original}'."
